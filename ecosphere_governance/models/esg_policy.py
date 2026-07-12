# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EsgPolicy(models.Model):
    """
    ESG Policy: Organizational policies requiring employee acknowledgement.
    Lifecycle: draft → under_review → published → archived
    On publish, notifies all relevant employees and opens acknowledgement window.
    """
    _name = 'esg.policy'
    _description = 'ESG Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'effective_date desc, name'

    name = fields.Char(string='Policy Title', required=True, tracking=True)
    reference = fields.Char(string='Policy Reference', copy=False,
                            default=lambda self: self.env['ir.sequence'].next_by_code('esg.policy'))
    description = fields.Html(string='Policy Content')
    summary = fields.Text(string='Executive Summary')

    # Classification
    policy_type = fields.Selection([
        ('environmental',  'Environmental'),
        ('social',         'Social Responsibility'),
        ('governance',     'Governance & Ethics'),
        ('health_safety',  'Health & Safety'),
        ('data_privacy',   'Data Privacy'),
        ('anti_bribery',   'Anti-Bribery'),
        ('supplier',       'Supplier Code'),
        ('hr',             'Human Resources'),
        ('other',          'Other'),
    ], string='Policy Type', required=True, default='governance', tracking=True)

    category_id = fields.Many2one('esg.category', string='ESG Category')
    department_ids = fields.Many2many(
        'esg.department', string='Applicable Departments',
        help='Leave empty to apply organization-wide')
    applies_to_all = fields.Boolean(
        string='Applies to All Departments',
        compute='_compute_applies_to_all', store=True)

    # Ownership
    owner_id = fields.Many2one('res.users', string='Policy Owner',
                                default=lambda self: self.env.user, tracking=True)
    reviewer_id = fields.Many2one('res.users', string='Reviewer')
    approver_id = fields.Many2one('res.users', string='Approver')

    # Dates
    effective_date = fields.Date(string='Effective Date', tracking=True)
    review_date = fields.Date(string='Next Review Date')
    expiry_date = fields.Date(string='Expiry Date')
    acknowledgement_deadline = fields.Date(
        string='Acknowledgement Deadline', tracking=True,
        help='Deadline by which all employees must acknowledge this policy')

    # State
    state = fields.Selection([
        ('draft',         'Draft'),
        ('under_review',  'Under Review'),
        ('published',     'Published'),
        ('archived',      'Archived'),
    ], string='Status', default='draft', tracking=True)

    version = fields.Char(string='Version', default='1.0')
    priority = fields.Selection([('0', 'Normal'), ('1', 'Important'), ('2', 'Critical')],
                                 default='0')

    # Acknowledgement stats
    acknowledgement_ids = fields.One2many(
        'policy.acknowledgement', 'policy_id', string='Acknowledgements')
    total_ack = fields.Integer(string='Acknowledged', compute='_compute_ack_stats', store=True)
    pending_ack = fields.Integer(string='Pending', compute='_compute_ack_stats', store=True)
    ack_rate = fields.Float(string='Ack Rate (%)', compute='_compute_ack_stats',
                             store=True, digits=(5, 1))

    # Document attachment
    attachment_ids = fields.Many2many('ir.attachment', string='Documents')
    active = fields.Boolean(default=True)

    @api.depends('department_ids')
    def _compute_applies_to_all(self):
        for p in self:
            p.applies_to_all = not bool(p.department_ids)

    @api.depends('acknowledgement_ids', 'acknowledgement_ids.state')
    def _compute_ack_stats(self):
        for policy in self:
            acks = policy.acknowledgement_ids
            total = len(acks)
            acknowledged = len(acks.filtered(lambda a: a.state == 'acknowledged'))
            policy.total_ack = acknowledged
            policy.pending_ack = total - acknowledged
            policy.ack_rate = (acknowledged / total * 100) if total else 0.0

    # ── Workflow ────────────────────────────────────────────────────
    def action_submit_review(self):
        self.write({'state': 'under_review'})
        if self.reviewer_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.reviewer_id.id,
                note=f'Please review policy: {self.name}',
            )

    def action_publish(self):
        self.write({'state': 'published'})
        self._notify_employees()
        self._create_acknowledgements()
        self.message_post(body=f'📋 Policy <b>{self.name}</b> published. Acknowledgement requests sent.')

    def action_archive_policy(self):
        self.write({'state': 'archived', 'active': False})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def _notify_employees(self):
        """Post a channel message notifying about the new policy."""
        channel = self.env.ref('mail.channel_all_employees', raise_if_not_found=False)
        if channel:
            channel.message_post(
                body=(f'📋 New Policy Published: <b>{self.name}</b><br/>'
                      f'Please acknowledge by {self.acknowledgement_deadline or "N/A"}.'),
                message_type='comment',
                subtype_xmlid='mail.mt_comment',
            )

    def _create_acknowledgements(self):
        """Create pending acknowledgement records for all relevant employees."""
        employees = self.env['hr.employee'].search([('active', '=', True)])
        existing = self.acknowledgement_ids.mapped('employee_id')
        to_create = employees - existing
        AckModel = self.env['policy.acknowledgement']
        for emp in to_create:
            AckModel.create({
                'policy_id': self.id,
                'employee_id': emp.id,
                'deadline': self.acknowledgement_deadline,
            })
        _logger.info('Created %d acknowledgement requests for policy %s',
                     len(to_create), self.name)

    def action_send_reminder(self):
        """Send reminder to employees with pending acknowledgements."""
        pending = self.acknowledgement_ids.filtered(lambda a: a.state == 'pending')
        for ack in pending:
            ack.employee_id.message_post(
                body=(f'⏰ Reminder: Please acknowledge policy <b>{self.name}</b> '
                      f'by {self.acknowledgement_deadline}.'),
                partner_ids=[ack.employee_id.user_id.partner_id.id]
                if ack.employee_id.user_id else [],
            )
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'message': f'Reminders sent to {len(pending)} employees.',
                           'type': 'success'}}

    @api.model
    def _cron_send_policy_reminders(self):
        """Cron: send reminders for policies with approaching deadlines."""
        today = fields.Date.today()
        import datetime
        in_7_days = today + datetime.timedelta(days=7)
        overdue_policies = self.search([
            ('state', '=', 'published'),
            ('acknowledgement_deadline', '>=', today),
            ('acknowledgement_deadline', '<=', in_7_days),
        ])
        for policy in overdue_policies:
            policy.action_send_reminder()


class PolicyAcknowledgement(models.Model):
    """
    Policy Acknowledgement: Tracks an individual employee's acknowledgement
    of a published policy. Created automatically when a policy is published.
    """
    _name = 'policy.acknowledgement'
    _description = 'Policy Acknowledgement'
    _order = 'deadline asc'

    policy_id = fields.Many2one('esg.policy', string='Policy',
                                 required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',
                                   required=True, ondelete='cascade', index=True)
    department_id = fields.Many2one(
        'esg.department', string='Department',
        related='policy_id.category_id.name', readonly=True, store=False)

    state = fields.Selection([
        ('pending',       'Pending'),
        ('acknowledged',  'Acknowledged'),
        ('overdue',       'Overdue'),
        ('exempted',      'Exempted'),
    ], string='Status', default='pending', tracking=True)

    deadline = fields.Date(string='Deadline')
    acknowledged_on = fields.Datetime(string='Acknowledged On', readonly=True)
    acknowledged_via = fields.Selection([
        ('portal',  'Employee Portal'),
        ('email',   'Email Link'),
        ('manual',  'Manual (Manager)'),
    ], string='Acknowledged Via')
    signature = fields.Binary(string='Digital Signature')
    notes = fields.Text(string='Notes')

    _sql_constraints = [
        ('unique_ack', 'UNIQUE(policy_id, employee_id)',
         'Each employee can have only one acknowledgement per policy.'),
    ]

    def action_acknowledge(self):
        """Employee acknowledges the policy."""
        self.write({
            'state': 'acknowledged',
            'acknowledged_on': fields.Datetime.now(),
            'acknowledged_via': 'manual',
        })

    def action_exempt(self):
        self.write({'state': 'exempted'})

    @api.model
    def _cron_mark_overdue(self):
        """Mark pending acknowledgements as overdue if past deadline."""
        today = fields.Date.today()
        overdue = self.search([
            ('state', '=', 'pending'),
            ('deadline', '<', today),
        ])
        overdue.write({'state': 'overdue'})
        _logger.info('Marked %d policy acknowledgements as overdue.', len(overdue))
