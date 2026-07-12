# -*- coding: utf-8 -*-

from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_carbon_toggle = fields.Boolean(
        string='Auto Carbon Calculation',
        config_parameter='ecosphere.auto_carbon_toggle',
        help='Automatically calculate carbon transactions from daily operations'
    )
    evidence_toggle = fields.Boolean(
        string='Evidence Requirement',
        config_parameter='ecosphere.evidence_toggle',
        help='Require evidence attachments before approving CSR activity participations'
    )
    badge_toggle = fields.Boolean(
        string='Badge Auto-Awarding',
        config_parameter='ecosphere.badge_toggle',
        help='Automatically award badges on challenge completions'
    )
