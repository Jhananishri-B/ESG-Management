# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgWeightConfig(models.Model):
    """
    ESG Weight Configuration: Defines the percentage contribution of each
    ESG pillar (Environmental, Social, Governance) to the overall ESG score.
    Only one active configuration should exist at a time.
    """
    _name = 'esg.weight.config'
    _description = 'ESG Weight Configuration'
    _order = 'id desc'

    name = fields.Char(string='Configuration Name', required=True,
                       default='Default ESG Weights')
    active = fields.Boolean(string='Active', default=True)
    effective_date = fields.Date(string='Effective Date', default=fields.Date.today)

    # Weights (must sum to 100)
    weight_env = fields.Float(
        string='Environmental Weight (%)', default=40.0,
        digits=(5, 2), help='Percentage contribution of Environmental pillar to ESG score')
    weight_social = fields.Float(
        string='Social Weight (%)', default=30.0,
        digits=(5, 2), help='Percentage contribution of Social pillar to ESG score')
    weight_governance = fields.Float(
        string='Governance Weight (%)', default=30.0,
        digits=(5, 2), help='Percentage contribution of Governance pillar to ESG score')

    total_weight = fields.Float(
        string='Total (%)', compute='_compute_total', store=True, digits=(5, 2))

    notes = fields.Text(string='Notes')

    @api.depends('weight_env', 'weight_social', 'weight_governance')
    def _compute_total(self):
        for config in self:
            config.total_weight = config.weight_env + config.weight_social + config.weight_governance

    @api.constrains('weight_env', 'weight_social', 'weight_governance')
    def _check_weights_sum(self):
        for config in self:
            total = config.weight_env + config.weight_social + config.weight_governance
            if abs(total - 100.0) > 0.01:
                raise ValidationError(
                    f'ESG weights must sum to 100%. Current total: {total:.2f}%')

    @api.constrains('weight_env', 'weight_social', 'weight_governance')
    def _check_weights_positive(self):
        for config in self:
            if any(w < 0 for w in [config.weight_env, config.weight_social, config.weight_governance]):
                raise ValidationError('All ESG weights must be positive values.')

    @api.model
    def get_active_config(self):
        """Return the active weight configuration, or defaults if none exists."""
        config = self.search([('active', '=', True)], limit=1)
        if config:
            return {
                'env': config.weight_env / 100,
                'social': config.weight_social / 100,
                'governance': config.weight_governance / 100,
            }
        return {'env': 0.40, 'social': 0.30, 'governance': 0.30}
