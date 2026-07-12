# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """
    Extends Odoo's global Settings to include EcoSphere ESG configuration.
    All EcoSphere modules contribute settings sections here.
    """
    _inherit = 'res.config.settings'

    # ── Organization Info ────────────────────────────────────────────────
    ecosphere_org_name = fields.Char(
        string='Organization Name',
        config_parameter='ecosphere.org_name',
        default='My Organization')
    ecosphere_fiscal_year_start = fields.Selection([
        ('01', 'January'), ('04', 'April'), ('07', 'July'), ('10', 'October'),
    ], string='Fiscal Year Start',
       config_parameter='ecosphere.fiscal_year_start',
       default='01')
    ecosphere_base_currency = fields.Many2one(
        'res.currency', string='Reporting Currency',
        related='company_id.currency_id', readonly=False)

    # ── ESG Score Settings ───────────────────────────────────────────────
    ecosphere_score_calculation = fields.Selection([
        ('weighted', 'Weighted Average'),
        ('equal', 'Equal Weight'),
        ('custom', 'Custom Weights'),
    ], string='Score Calculation Method',
       config_parameter='ecosphere.score_calculation',
       default='weighted')
    ecosphere_score_decimal_places = fields.Integer(
        string='Score Decimal Places',
        config_parameter='ecosphere.score_decimal_places',
        default=2)

    # ── Notification Settings ────────────────────────────────────────────
    ecosphere_notify_goal_achieved = fields.Boolean(
        string='Notify on Goal Achievement',
        config_parameter='ecosphere.notify_goal_achieved',
        default=True)
    ecosphere_notify_carbon_threshold = fields.Boolean(
        string='Notify on Carbon Threshold Exceeded',
        config_parameter='ecosphere.notify_carbon_threshold',
        default=True)
    ecosphere_notify_policy_due = fields.Boolean(
        string='Notify on Policy Acknowledgement Due',
        config_parameter='ecosphere.notify_policy_due',
        default=True)
    ecosphere_notify_audit_due = fields.Boolean(
        string='Notify on Audit Due',
        config_parameter='ecosphere.notify_audit_due',
        default=True)
    ecosphere_notify_challenge_deadline = fields.Boolean(
        string='Notify on Challenge Deadline',
        config_parameter='ecosphere.notify_challenge_deadline',
        default=True)

    # ── AI Settings ──────────────────────────────────────────────────────
    ecosphere_ai_enabled = fields.Boolean(
        string='Enable AI Copilot',
        config_parameter='ecosphere.ai_enabled',
        default=False)
    ecosphere_ai_provider = fields.Selection([
        ('openai', 'OpenAI'),
        ('azure', 'Azure OpenAI'),
        ('anthropic', 'Anthropic (compatible)'),
        ('local', 'Local / Ollama'),
        ('custom', 'Custom Endpoint'),
    ], string='AI Provider',
       config_parameter='ecosphere.ai_provider',
       default='openai')
    ecosphere_ai_api_key = fields.Char(
        string='AI API Key',
        config_parameter='ecosphere.ai_api_key')
    ecosphere_ai_endpoint = fields.Char(
        string='AI Endpoint URL',
        config_parameter='ecosphere.ai_endpoint',
        default='https://api.openai.com/v1/chat/completions')
    ecosphere_ai_model = fields.Char(
        string='AI Model',
        config_parameter='ecosphere.ai_model',
        default='gpt-4o-mini')
    ecosphere_ai_max_tokens = fields.Integer(
        string='Max Tokens',
        config_parameter='ecosphere.ai_max_tokens',
        default=1024)

    # ── Portal Settings ──────────────────────────────────────────────────
    ecosphere_portal_enabled = fields.Boolean(
        string='Enable Employee Portal',
        config_parameter='ecosphere.portal_enabled',
        default=True)
    ecosphere_portal_allow_self_join = fields.Boolean(
        string='Allow Self-Join on Challenges',
        config_parameter='ecosphere.portal_allow_self_join',
        default=True)

    # ── Carbon Settings ──────────────────────────────────────────────────
    ecosphere_carbon_unit = fields.Selection([
        ('kg', 'Kilograms (kg CO₂e)'),
        ('tonne', 'Metric Tonnes (tCO₂e)'),
    ], string='Carbon Unit',
       config_parameter='ecosphere.carbon_unit',
       default='kg')
    ecosphere_carbon_threshold_pct = fields.Float(
        string='Carbon Alert Threshold (%)',
        config_parameter='ecosphere.carbon_threshold_pct',
        default=90.0,
        help='Send alert when department carbon usage exceeds this % of target')
