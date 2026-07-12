# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EmissionFactor(models.Model):
    """
    Emission Factor library.
    Provides CO₂-equivalent conversion factors for different activity types.
    Factors are expressed as kg CO₂e per unit of activity.

    Scope definitions (GHG Protocol):
      Scope 1 — Direct emissions (fuel combustion, company vehicles, etc.)
      Scope 2 — Indirect from purchased energy (electricity, heat, steam)
      Scope 3 — All other indirect (supply chain, travel, waste, etc.)
    """
    _name = 'emission.factor'
    _description = 'Emission Factor'
    _order = 'scope, category, name'

    name = fields.Char(string='Factor Name', required=True)
    code = fields.Char(string='Code', help='Short identifier, e.g. GRID_IN, DIESEL_L')
    description = fields.Text(string='Description')

    # Classification
    scope = fields.Selection([
        ('1', 'Scope 1 — Direct'),
        ('2', 'Scope 2 — Purchased Energy'),
        ('3', 'Scope 3 — Value Chain'),
    ], string='GHG Scope', required=True, default='1')

    category = fields.Selection([
        ('fuel',           'Fuel Combustion'),
        ('electricity',    'Electricity'),
        ('heat',           'Heat / Steam'),
        ('transport',      'Transport & Logistics'),
        ('fleet',          'Fleet / Vehicles'),
        ('air_travel',     'Air Travel'),
        ('water',          'Water'),
        ('waste',          'Waste'),
        ('material',       'Raw Materials'),
        ('refrigerant',    'Refrigerants'),
        ('agriculture',    'Agriculture'),
        ('other',          'Other'),
    ], string='Category', required=True, default='fuel')

    # The conversion factor
    factor_value = fields.Float(
        string='Emission Factor (kg CO₂e / unit)',
        required=True, digits=(10, 6),
        help='CO₂-equivalent kg emitted per unit of activity')
    unit = fields.Char(
        string='Activity Unit', required=True, default='kg',
        help='Unit of activity measurement (e.g., litre, kWh, km, kg)')

    # Source & validity
    source = fields.Char(
        string='Data Source',
        help='e.g. IPCC 2021, DEFRA 2023, IEA 2023, EPA 2023')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    region = fields.Char(
        string='Region / Country',
        help='Geographic scope: Global, IN (India), UK, US, EU, etc.')
    active = fields.Boolean(string='Active', default=True)

    # Usage stats
    transaction_count = fields.Integer(
        string='Transactions', compute='_compute_transaction_count')

    _sql_constraints = [
        ('factor_positive', 'CHECK(factor_value >= 0)',
         'Emission factor value must be non-negative.'),
    ]

    @api.depends()
    def _compute_transaction_count(self):
        for ef in self:
            ef.transaction_count = self.env['carbon.transaction'].search_count(
                [('emission_factor_id', '=', ef.id)])

    @api.constrains('valid_from', 'valid_to')
    def _check_validity_dates(self):
        for ef in self:
            if ef.valid_from and ef.valid_to and ef.valid_to < ef.valid_from:
                raise ValidationError('Valid To must be after Valid From.')

    def name_get(self):
        return [(r.id, f'[Scope {r.scope}] {r.name} ({r.factor_value} kg/{r.unit})')
                for r in self]

    @api.model
    def get_factor_for_category(self, category, region=None):
        """
        Find the most appropriate emission factor for a category.
        Prefers region-specific, then falls back to global.
        """
        domain = [('category', '=', category), ('active', '=', True)]
        if region:
            factor = self.search(domain + [('region', '=', region)], limit=1)
            if factor:
                return factor
        return self.search(domain, limit=1)
