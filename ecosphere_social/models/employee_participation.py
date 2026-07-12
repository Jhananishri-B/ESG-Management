# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class EmployeeParticipation(models.Model):
    """
    Employee Participation: Links an employee to a CSR activity.
    Tracks state from registration through evidence upload to approval/rejection.
    On approval, XP is awarded and volunteer hours are logged.
    """
    _name = 'employee.participation'
    _description = 'CSR Employee Participation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'
    _rec_name = 'display_name_computed'

    # Links
    activity_id = fields.Many2one(
        'csr.activity', string='CSR Activity',
        required=True, ondelete='cascade', tracking=True, index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        required=True, ondelete='cascade', tracking=True, index=True)
    department_id = fields.Many2one(
        'esg.department', string='Department',
        related='activity_id.department_id', store=True, readonly=True)

    # Display name
    display_name_computed = fields.Char(
        string='Name', compute='_compute_display_name', store=True)

    # State
    state = fields.Selection([
        ('registered', 'Registered'),
        ('attended',   'Attended'),
        ('evidence_uploaded', 'Evidence Uploaded'),
        ('approved',   'Approved'),
        ('rejected',   'Rejected'),
    ], string='Status', default='registered', tracking=True)

    # Evidence
    evidence_description = fields.Text(string='Evidence Description')
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment', string='Evidence Files',
        help='Upload photos, documents, or certificates as evidence of participation')

    # Notes
    reviewer_id = fields.Many2one('res.users', string='Reviewed By', readonly=True)
    review_date = fields.Datetime(string='Review Date', readonly=True)
    rejection_reason = fields.Text(string='Rejection Reason')
    notes = fields.Text(string='Notes')

    # XP granted
    xp_granted = fields.Integer(string='XP Granted', default=0, readonly=True)
    xp_awarded = fields.Boolean(string='XP Awarded', default=False)

    # Volunteer hours
    hours_credited = fields.Float(
        string='Hours Credited',
        related='activity_id.volunteer_hours', readonly=True)

    # Timestamps
    registration_date = fields.Datetime(
        string='Registration Date', default=fields.Datetime.now, readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)

    _sql_constraints = [
        ('unique_participation', 'UNIQUE(activity_id, employee_id)',
         'An employee can only register once per CSR activity.'),
    ]

    @api.depends('activity_id', 'employee_id')
    def _compute_display_name(self):
        for p in self:
            p.display_name_computed = (
                f'{p.employee_id.name} — {p.activity_id.name}'
                if p.employee_id and p.activity_id else 'New Participation')

    # ── Workflow Actions ─────────────────────────────────────────────
    def action_mark_attended(self):
        self.write({'state': 'attended'})

    def action_upload_evidence(self):
        """Mark as evidence uploaded — triggered from portal."""
        self.write({'state': 'evidence_uploaded'})

    def action_approve(self):
        """Approve participation: award XP and log volunteer hours."""
        for part in self:
            if part.state == 'rejected':
                raise UserError('Cannot approve a rejected participation.')
            part.write({
                'state': 'approved',
                'reviewer_id': self.env.uid,
                'review_date': fields.Datetime.now(),
                'approval_date': fields.Datetime.now(),
            })
            part._grant_xp()
            part._log_volunteer_hours()
        self.message_post(body='✅ Participation approved. XP and volunteer hours credited.')

    def action_reject(self, reason=''):
        self.write({
            'state': 'rejected',
            'reviewer_id': self.env.uid,
            'review_date': fields.Datetime.now(),
            'rejection_reason': reason,
        })
        self.message_post(body=f'❌ Participation rejected. Reason: {reason or "Not specified"}')

    def _grant_xp(self):
        """Award XP via the gamification module if available."""
        if self.xp_awarded:
            return
        XpLedger = self.env.get('xp.ledger')
        if XpLedger and self.activity_id.xp_reward:
            XpLedger.award_xp(
                employee_id=self.employee_id.id,
                amount=self.activity_id.xp_reward,
                reason=f'CSR: {self.activity_id.name}',
                source_model='csr.activity',
                source_id=self.activity_id.id,
            )
            self.write({'xp_granted': self.activity_id.xp_reward, 'xp_awarded': True})
            _logger.info('XP %d awarded to %s for %s',
                         self.activity_id.xp_reward, self.employee_id.name,
                         self.activity_id.name)

    def _log_volunteer_hours(self):
        """Create a volunteer hours record."""
        VolHours = self.env.get('volunteer.hours')
        if VolHours:
            VolHours.create({
                'employee_id': self.employee_id.id,
                'activity_id': self.activity_id.id,
                'hours': self.activity_id.volunteer_hours,
                'date': fields.Date.today(),
                'approved': True,
            })

    def action_view_evidence(self):
        return {
            'name': 'Evidence',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.evidence_attachment_ids.ids)],
        }


class HrEmployeeEsgExtension(models.Model):
    """Extends hr.employee with ESG stats."""
    _inherit = 'hr.employee'

    esg_department_id = fields.Many2one(
        'esg.department', string='ESG Department',
        help='Links the employee to an ESG department for score aggregation')
    total_xp = fields.Integer(string='Total XP', default=0)
    total_volunteer_hours = fields.Float(
        string='Total Volunteer Hours', default=0.0, digits=(8, 1))
    csr_participation_count = fields.Integer(
        string='CSR Participations',
        compute='_compute_csr_stats', store=False)
    approved_participation_count = fields.Integer(
        string='Approved Participations',
        compute='_compute_csr_stats', store=False)

    def _compute_csr_stats(self):
        for emp in self:
            parts = self.env['employee.participation'].search(
                [('employee_id', '=', emp.id)])
            emp.csr_participation_count = len(parts)
            emp.approved_participation_count = len(
                parts.filtered(lambda p: p.state == 'approved'))
