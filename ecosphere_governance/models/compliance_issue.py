# -*- coding: utf-8 -*-
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class ComplianceIssue(models.Model):
    """
    Compliance Issue: A regulatory or internal compliance violation or risk.
    Tracks root cause, severity, corrective actions, and resolution.
    """
    _name = 'compliance.issue'
    _description = 'Compliance Issue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'severity, reported_date desc'

    name = fields.Char(string='Issue Title', required=True, tracking=True)
    reference = fields.Char(
        string='Reference', copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('compliance.issue'))
    description = fields.Text(string='Description')

    # Classification
    issue_type = fields.Selection([
        ('regulatory',     'Regulatory Violation'),
        ('policy',         'Internal Policy Breach'),
        ('environmental',  'Environmental Non-Compliance'),
        ('labor',          'Labor Law Issue'),
        ('data_privacy',   'Data Privacy Breach'),
        ('financial',      'Financial Compliance'),
        ('health_safety',  'Health & Safety'),
        ('other',          'Other'),
    ], string='Issue Type', required=True, default='regulatory', tracking=True)

    severity = fields.Selection([
        ('low',      'Low'),
        ('medium',   'Medium'),
        ('high',     'High'),
        ('critical', 'Critical'),
    ], string='Severity', required=True, default='medium', tracking=True)

    department_id = fields.Many2one('esg.department', string='Department',
                                     required=True, ondelete='restrict')
    reported_by = fields.Many2one('res.users', string='Reported By',
                                   default=lambda self: self.env.user)
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    policy_id = fields.Many2one('esg.policy', string='Related Policy')

    # Dates
    reported_date = fields.Date(string='Reported Date', default=fields.Date.today)
    due_date = fields.Date(string='Resolution Due Date', tracking=True)
    resolved_date = fields.Date(string='Resolved On')
    days_open = fields.Integer(string='Days Open', compute='_compute_days_open')

    # Root cause & resolution
    root_cause = fields.Text(string='Root Cause Analysis')
    corrective_action = fields.Text(string='Corrective Action Plan')
    preventive_action = fields.Text(string='Preventive Action')
    resolution_notes = fields.Text(string='Resolution Notes')

    # State
    state = fields.Selection([
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('pending_review', 'Pending Review'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
        ('escalated',   'Escalated'),
    ], string='Status', default='open', tracking=True)

    # Regulatory details
    regulation_name = fields.Char(string='Regulation / Standard')
    regulatory_body = fields.Char(string='Regulatory Body')
    fine_amount = fields.Float(string='Fine / Penalty Amount', digits=(10, 2))
    currency_id = fields.Many2one('res.currency', string='Currency',
                                   default=lambda self: self.env.company.currency_id)
    financial_impact = fields.Float(
        string='Total Financial Impact', digits=(10, 2),
        compute='_compute_financial_impact', store=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Evidence')
    active = fields.Boolean(default=True)

    @api.depends('reported_date', 'resolved_date')
    def _compute_days_open(self):
        today = fields.Date.today()
        for issue in self:
            end = issue.resolved_date or today
            if issue.reported_date:
                issue.days_open = (end - issue.reported_date).days
            else:
                issue.days_open = 0

    @api.depends('fine_amount')
    def _compute_financial_impact(self):
        for issue in self:
            issue.financial_impact = issue.fine_amount

    def action_start(self):
        self.write({'state': 'in_progress'})
        if self.assigned_to:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.assigned_to.id,
                note=f'Compliance issue assigned: {self.name}',
            )

    def action_submit_review(self):
        self.write({'state': 'pending_review'})

    def action_resolve(self):
        self.write({'state': 'resolved', 'resolved_date': fields.Date.today()})
        self.message_post(body='✅ Compliance issue resolved.')
        self._update_governance_score()

    def action_close(self):
        self.write({'state': 'closed'})

    def action_escalate(self):
        self.write({'state': 'escalated'})
        self.message_post(body='🚨 Issue escalated to management.')

    def _update_governance_score(self):
        """Resolving a compliance issue positively impacts governance score."""
        dept = self.department_id
        if dept:
            improvement = {'low': 1, 'medium': 2, 'high': 3, 'critical': 5}
            delta = improvement.get(self.severity, 1)
            dept.governance_score = min(dept.governance_score + delta, 100)

    @api.model
    def _cron_check_overdue(self):
        """Escalate issues that are past due date and still open."""
        today = fields.Date.today()
        overdue = self.search([
            ('state', 'in', ('open', 'in_progress')),
            ('due_date', '<', today),
        ])
        for issue in overdue:
            issue.action_escalate()
            _logger.warning('Auto-escalated compliance issue: %s', issue.name)


class RiskRegister(models.Model):
    """
    Risk Register: ESG-related risks scored by likelihood × impact.
    Automatic risk level assignment and mitigation tracking.
    """
    _name = 'risk.register'
    _description = 'ESG Risk Register'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'risk_score desc, name'

    name = fields.Char(string='Risk Title', required=True, tracking=True)
    description = fields.Text(string='Risk Description')
    reference = fields.Char(
        string='Reference', copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('risk.register'))

    # Classification
    risk_category = fields.Selection([
        ('climate',         'Climate / Environmental'),
        ('regulatory',      'Regulatory & Compliance'),
        ('supply_chain',    'Supply Chain'),
        ('reputational',    'Reputational'),
        ('operational',     'Operational'),
        ('financial',       'Financial'),
        ('social',          'Social / Labor'),
        ('technology',      'Technology'),
        ('governance',      'Governance'),
        ('other',           'Other'),
    ], string='Risk Category', required=True, default='regulatory', tracking=True)

    department_id = fields.Many2one('esg.department', string='Department',
                                     required=True, ondelete='restrict')
    owner_id = fields.Many2one('res.users', string='Risk Owner',
                                default=lambda self: self.env.user, tracking=True)

    # Inherent risk (before controls)
    likelihood = fields.Selection([
        ('1', 'Rare (1)'),
        ('2', 'Unlikely (2)'),
        ('3', 'Possible (3)'),
        ('4', 'Likely (4)'),
        ('5', 'Almost Certain (5)'),
    ], string='Likelihood', required=True, default='3', tracking=True)

    impact = fields.Selection([
        ('1', 'Negligible (1)'),
        ('2', 'Minor (2)'),
        ('3', 'Moderate (3)'),
        ('4', 'Major (4)'),
        ('5', 'Catastrophic (5)'),
    ], string='Impact', required=True, default='3', tracking=True)

    risk_score = fields.Integer(
        string='Risk Score', compute='_compute_risk_score', store=True)
    risk_level = fields.Selection([
        ('low',      '🟢 Low (1–4)'),
        ('medium',   '🟡 Medium (5–9)'),
        ('high',     '🔴 High (10–19)'),
        ('critical', '⛔ Critical (20–25)'),
    ], string='Risk Level', compute='_compute_risk_score', store=True, tracking=True)

    # Residual risk (after controls)
    residual_likelihood = fields.Selection([
        ('1', 'Rare (1)'), ('2', 'Unlikely (2)'), ('3', 'Possible (3)'),
        ('4', 'Likely (4)'), ('5', 'Almost Certain (5)'),
    ], string='Residual Likelihood', default='2')
    residual_impact = fields.Selection([
        ('1', 'Negligible (1)'), ('2', 'Minor (2)'), ('3', 'Moderate (3)'),
        ('4', 'Major (4)'), ('5', 'Catastrophic (5)'),
    ], string='Residual Impact', default='2')
    residual_score = fields.Integer(
        string='Residual Score', compute='_compute_residual_score', store=True)

    # Controls & mitigation
    existing_controls = fields.Text(string='Existing Controls')
    mitigation_plan = fields.Text(string='Mitigation Plan')
    mitigation_deadline = fields.Date(string='Mitigation Deadline')
    mitigation_owner_id = fields.Many2one('res.users', string='Mitigation Owner')

    # Status
    state = fields.Selection([
        ('identified',  'Identified'),
        ('assessed',    'Assessed'),
        ('mitigating',  'Mitigating'),
        ('monitored',   'Monitored'),
        ('closed',      'Closed'),
        ('accepted',    'Accepted'),
    ], string='Status', default='identified', tracking=True)

    review_date = fields.Date(string='Next Review Date')
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)

    @api.depends('likelihood', 'impact')
    def _compute_risk_score(self):
        level_map = {(s, l): None for s in range(1, 6) for l in range(1, 6)}
        for risk in self:
            l = int(risk.likelihood or 3)
            i = int(risk.impact or 3)
            score = l * i
            risk.risk_score = score
            if score <= 4:
                risk.risk_level = 'low'
            elif score <= 9:
                risk.risk_level = 'medium'
            elif score <= 19:
                risk.risk_level = 'high'
            else:
                risk.risk_level = 'critical'

    @api.depends('residual_likelihood', 'residual_impact')
    def _compute_residual_score(self):
        for risk in self:
            risk.residual_score = (
                int(risk.residual_likelihood or 2) *
                int(risk.residual_impact or 2)
            )

    def action_assess(self):
        self.write({'state': 'assessed'})

    def action_mitigate(self):
        self.write({'state': 'mitigating'})

    def action_monitor(self):
        self.write({'state': 'monitored'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_accept(self):
        self.write({'state': 'accepted'})
        self.message_post(body='⚠️ Risk accepted by risk owner. Will be monitored.')
