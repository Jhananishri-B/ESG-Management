# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ecosphere_openai_api_key = fields.Char(
        string="OpenAI API Key",
        config_parameter='ecosphere_ai.openai_api_key',
        help="API Key for OpenAI to generate ESG Policies automatically."
    )
