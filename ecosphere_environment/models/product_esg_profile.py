# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductEsgProfile(models.Model):
    """
    Product ESG Profile: Attaches ESG/carbon metadata to a product template.
    When products are purchased or manufactured, the profile drives automatic
    carbon transaction creation.
    """
    _name = 'product.esg.profile'
    _description = 'Product ESG Profile'

    name = fields.Char(string='Profile Name', required=True)
    product_tmpl_id = fields.Many2one(
        'product.template', string='Product',
        required=True, ondelete='cascade', index=True)

    # Carbon calculation
    emission_factor_id = fields.Many2one(
        'emission.factor', string='Default Emission Factor',
        help='Factor used when this product triggers carbon transactions')
    emission_per_unit = fields.Float(
        string='Activity per Unit', default=1.0, digits=(10, 4),
        help='Activity quantity per unit of product (e.g., 1 unit = 5 kg material)')
    carbon_per_unit = fields.Float(
        string='Carbon per Unit (kg CO₂e)',
        compute='_compute_carbon_per_unit', store=True, digits=(10, 4))

    # Lifecycle
    lifecycle_stage = fields.Selection([
        ('raw_material',  'Raw Material Extraction'),
        ('manufacturing', 'Manufacturing'),
        ('transport',     'Transport & Distribution'),
        ('use',           'Use Phase'),
        ('end_of_life',   'End of Life'),
        ('full',          'Full Lifecycle'),
    ], string='Lifecycle Stage', default='manufacturing')

    # ESG classification
    esg_category = fields.Selection([
        ('green',    'Green Product'),
        ('neutral',  'Carbon Neutral'),
        ('moderate', 'Moderate Impact'),
        ('high',     'High Impact'),
    ], string='ESG Category', default='moderate')

    recycled_content_pct = fields.Float(
        string='Recycled Content (%)', default=0.0, digits=(5, 2))
    recyclable = fields.Boolean(string='Recyclable', default=False)
    certified = fields.Boolean(string='Eco-Certified', default=False)
    certification_body = fields.Char(string='Certification Body')

    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)

    @api.depends('emission_factor_id', 'emission_per_unit')
    def _compute_carbon_per_unit(self):
        for profile in self:
            if profile.emission_factor_id:
                profile.carbon_per_unit = (
                    profile.emission_per_unit * profile.emission_factor_id.factor_value)
            else:
                profile.carbon_per_unit = 0.0


class ProductTemplateEsgProfile(models.Model):
    """Extends product.template with ESG profile link."""
    _inherit = 'product.template'

    esg_profile_id = fields.Many2one(
        'product.esg.profile', string='ESG Profile',
        compute='_compute_esg_profile', store=True)
    has_esg_profile = fields.Boolean(
        string='Has ESG Profile', compute='_compute_esg_profile', store=True)
    carbon_per_unit = fields.Float(
        string='Carbon (kg CO₂e/unit)',
        related='esg_profile_id.carbon_per_unit', readonly=True)

    def _compute_esg_profile(self):
        Profile = self.env['product.esg.profile']
        for tmpl in self:
            profile = Profile.search([('product_tmpl_id', '=', tmpl.id)], limit=1)
            tmpl.esg_profile_id = profile
            tmpl.has_esg_profile = bool(profile)

    def action_create_esg_profile(self):
        return {
            'name': 'Create ESG Profile',
            'type': 'ir.actions.act_window',
            'res_model': 'product.esg.profile',
            'view_mode': 'form',
            'context': {'default_product_tmpl_id': self.id,
                        'default_name': f'{self.name} ESG Profile'},
        }
