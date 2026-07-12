# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EsgAudit(models.Model):
    """
    ESG Audit: Planned or ad-hoc audit covering environmental, social,
    or governance areas. Tracks findings, corrective actions, and score impact.
    """
    _name = 'esg.audit'
    _description = 'ESG Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'planned_date desc, name'

    name = fields.Char(string='Audit Title', required=True, tracking=True)
    reference = fields.Char(
        string='Reference', copy=False,
        default=lambda self: self.env['ir.sequence'].next_by_code('esg.audit'))

    # Classification
    audit_type = fields.Selection([
        ('internal',   'Internal Audit'),
        ('external',   'External Audit'),
        ('regulatory', 'Regulatory Audit'),
        ('supplier',   'Supplier Audit'),
        ('iso',        'ISO Certification Audit'),
    ], string='Audit Type', required=True, default='internal', tracking=True)

    category_id = fields.Many2one('esg.category', string='ESG Category')
    department_id = fields.Many2one(
        'esg.department', string='Department', required=True,
        ondelete='restrict', tracking=True)
    scope = fields.Text(string='Audit Scope')

    # Team
    lead_auditor_id = fields.Many2one('res.users', string='Lead Auditor',
                                       default=lambda self: self.env.user, tracking=True)
    auditor_ids = fields.Many2many('res.users', string='Audit Team')
    auditee_id = fields.Many2one('res.users', string='Auditee (Dept. Manager)')

    # Dates
    planned_date = fields.Date(string='Planned Date', required=True, tracking=True)
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    report_due_date = fields.Date(string='Report Due Date')
    days_to_audit = fields.Integer(string='Days Until Audit',
                                    compute='_compute_days_to_audit')

    # State
    state = fields.Selection([
        ('planned',    'Planned'),
        ('in_progress','In Progress'),
        ('completed',  'Completed'),
        ('reported',   'Report Issued'),
        ('closed',     'Closed'),
        ('cancelled',  'Cancelled'),
    ], string='Status', default='planned', tracking=True)

    # Findings
    finding_ids = fields.One2many('audit.finding', 'audit_id', string='Findings')
    finding_count = fields.Integer(string='Findings', compute='_compute_finding_count')
    critical_count = fields.Integer(string='Critical', compute='_compute_finding_count')
    major_count = fields.Integer(string='Major', compute='_compute_finding_count')
    minor_count = fields.Integer(string='Minor', compute='_compute_finding_count')

    # Result
    overall_score = fields.Float(string='Audit Score (0–100)', digits=(5, 1))
    result = fields.Selection([
        ('pass',         '✅ Pass'),
        ('pass_minor',   '✅ Pass with Minor Observations'),
        ('conditional',  '⚠️ Conditional Pass'),
        ('fail',         '❌ Fail'),
        ('not_assessed', 'Not Assessed'),
    ], string='Result', default='not_assessed')

    # Report
    executive_summary = fields.Html(string='Executive Summary')
    recommendations = fields.Html(string='Recommendations')
    report_attachment_ids = fields.Many2many('ir.attachment', string='Audit Reports')

    priority = fields.Selection([('0', 'Normal'), ('1', 'High'), ('2', 'Critical')],
                                 default='0')
    active = fields.Boolean(default=True)

    @api.depends('planned_date')
    def _compute_days_to_audit(self):
        today = fields.Date.today()
        for audit in self:
            if audit.planned_date:
                audit.days_to_audit = (audit.planned_date - today).days
            else:
                audit.days_to_audit = 0

    @api.depends('finding_ids', 'finding_ids.severity')
    def _compute_finding_count(self):
        for audit in self:
            findings = audit.finding_ids
            audit.finding_count = len(findings)
            audit.critical_count = len(findings.filtered(lambda f: f.severity == 'critical'))
            audit.major_count = len(findings.filtered(lambda f: f.severity == 'major'))
            audit.minor_count = len(findings.filtered(lambda f: f.severity == 'minor'))

    def action_start(self):
        self.write({'state': 'in_progress', 'start_date': fields.Date.today()})

    def action_complete(self):
        self.write({'state': 'completed', 'end_date': fields.Date.today()})
        self._auto_score()

    def action_report(self):
        self.write({'state': 'reported'})
        self._update_governance_score()

    def action_close(self):
        self.write({'state': 'closed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def _auto_score(self):
        """Calculate audit score based on findings."""
        if not self.finding_ids:
            self.overall_score = 100.0
            self.result = 'pass'
            return
        deduction = (
            self.critical_count * 25 +
            self.major_count * 10 +
            self.minor_count * 3
        )
        score = max(0, 100 - deduction)
        self.overall_score = score
        if score >= 90:
            self.result = 'pass'
        elif score >= 75:
            self.result = 'pass_minor'
        elif score >= 55:
            self.result = 'conditional'
        else:
            self.result = 'fail'

    def _update_governance_score(self):
        """Update department governance score based on audit result."""
        dept = self.department_id
        if not dept:
            return
        # Weight: each audit contributes to governance score
        score_map = {'pass': 100, 'pass_minor': 85, 'conditional': 65, 'fail': 30,
                     'not_assessed': 50}
        audit_score = score_map.get(self.result, 50)
        # Running average with existing score
        current = dept.governance_score
        dept.governance_score = round((current * 0.7 + audit_score * 0.3), 2)


class AuditFinding(models.Model):
    """
    Audit Finding: Individual observation or non-conformity found during an audit.
    """
    _name = 'audit.finding'
    _description = 'Audit Finding'
    _order = 'severity, name'

    audit_id = fields.Many2one('esg.audit', string='Audit',
                                required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Finding Title', required=True)
    description = fields.Text(string='Description')

    severity = fields.Selection([
        ('observation', 'Observation'),
        ('minor',       'Minor Non-Conformity'),
        ('major',       'Major Non-Conformity'),
        ('critical',    'Critical Non-Conformity'),
    ], string='Severity', required=True, default='minor')

    area = fields.Char(string='Area / Process')
    responsible_id = fields.Many2one('res.users', string='Responsible')
    corrective_action = fields.Text(string='Corrective Action Required')
    due_date = fields.Date(string='Corrective Action Due')
    closed = fields.Boolean(string='Closed', default=False)
    closed_on = fields.Date(string='Closed On')

    @api.onchange('closed')
    def _onchange_closed(self):
        if self.closed:
            self.closed_on = fields.Date.today()
