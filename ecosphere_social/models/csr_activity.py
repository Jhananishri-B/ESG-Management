# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class CsrActivity(models.Model):
    """
    CSR Activity: A community or sustainability event that employees can
    participate in. Activities are categorized, scheduled, and tracked
    for engagement and XP award purposes.

    Workflow: draft → open (accepting registrations) → in_progress → done → archived
    """
    _name = 'csr.activity'
    _description = 'CSR Activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, name'

    name = fields.Char(string='Activity Name', required=True, tracking=True)
    description = fields.Html(string='Description')
    image = fields.Binary(string='Banner Image')
    image_filename = fields.Char(string='Image Filename')

    # Classification
    activity_type = fields.Selection([
        ('community',       'Community Service'),
        ('environment',     'Environmental Action'),
        ('education',       'Education & Training'),
        ('health',          'Health & Wellbeing'),
        ('fundraising',     'Fundraising'),
        ('diversity',       'Diversity & Inclusion'),
        ('tree_planting',   'Tree Planting'),
        ('beach_cleanup',   'Beach / Area Cleanup'),
        ('food_drive',      'Food Drive'),
        ('mentoring',       'Mentoring'),
        ('other',           'Other'),
    ], string='Activity Type', required=True, default='community', tracking=True)

    department_id = fields.Many2one(
        'esg.department', string='Organizing Department',
        tracking=True)
    organizer_id = fields.Many2one(
        'res.users', string='Organizer',
        default=lambda self: self.env.user, tracking=True)

    # Schedule
    start_date = fields.Datetime(string='Start Date', required=True, tracking=True)
    end_date = fields.Datetime(string='End Date', required=True, tracking=True)
    location = fields.Char(string='Location')
    is_virtual = fields.Boolean(string='Virtual Event', default=False)
    meeting_url = fields.Char(string='Meeting URL', invisible=True)

    # Capacity
    max_participants = fields.Integer(string='Max Participants', default=0,
                                      help='0 = unlimited')
    participant_count = fields.Integer(
        string='Registered', compute='_compute_participant_count', store=True)
    approved_count = fields.Integer(
        string='Approved', compute='_compute_participant_count', store=True)
    is_full = fields.Boolean(
        string='Fully Booked', compute='_compute_is_full', store=True)

    # Points
    xp_reward = fields.Integer(string='XP Reward', default=50,
                                help='XP awarded per approved participant')
    volunteer_hours = fields.Float(
        string='Volunteer Hours', default=4.0, digits=(5, 1),
        help='Hours credited to each participant')
    requires_evidence = fields.Boolean(string='Evidence Required', default=False)

    # State
    state = fields.Selection([
        ('draft',       'Draft'),
        ('open',        'Open for Registration'),
        ('in_progress', 'In Progress'),
        ('pending_review', 'Pending Review'),
        ('done',        'Completed'),
        ('cancelled',   'Cancelled'),
        ('archived',    'Archived'),
    ], string='Status', default='draft', tracking=True)

    color = fields.Integer(string='Color', default=0)
    tag_ids = fields.Many2many('csr.activity.tag', string='Tags')

    # Participation
    participation_ids = fields.One2many(
        'employee.participation', 'activity_id', string='Participants')

    # Linked calendar event
    calendar_event_id = fields.Many2one(
        'calendar.event', string='Calendar Event', readonly=True)

    @api.depends('participation_ids', 'participation_ids.state')
    def _compute_participant_count(self):
        for act in self:
            act.participant_count = len(act.participation_ids)
            act.approved_count = len(
                act.participation_ids.filtered(lambda p: p.state == 'approved'))

    @api.depends('participant_count', 'max_participants')
    def _compute_is_full(self):
        for act in self:
            act.is_full = (
                act.max_participants > 0 and
                act.participant_count >= act.max_participants)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for act in self:
            if act.end_date and act.start_date and act.end_date < act.start_date:
                raise ValidationError('End date must be after start date.')

    # ── State Actions ────────────────────────────────────────────────
    def action_open(self):
        self.write({'state': 'open'})
        self._create_calendar_event()

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_complete(self):
        self.write({'state': 'pending_review'})

    def action_done(self):
        for act in self:
            act.state = 'done'
            act._award_xp_to_approved()
        self.message_post(body='✅ Activity completed. XP awarded to approved participants.')

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_archive(self):
        self.write({'state': 'archived', 'active': False})

    active = fields.Boolean(default=True)

    def _create_calendar_event(self):
        """Create a linked calendar event when activity opens."""
        for act in self:
            if not act.calendar_event_id:
                event = self.env['calendar.event'].create({
                    'name': act.name,
                    'start': act.start_date,
                    'stop': act.end_date,
                    'location': act.location or '',
                    'description': f'CSR Activity: {act.name}',
                })
                act.calendar_event_id = event

    def _award_xp_to_approved(self):
        """Award XP to all approved participants (calls gamification module if installed)."""
        GamifModule = self.env.get('xp.ledger')
        if not GamifModule:
            return
        for act in self:
            approved = act.participation_ids.filtered(lambda p: p.state == 'approved')
            for part in approved:
                GamifModule.award_xp(
                    employee_id=part.employee_id.id,
                    amount=act.xp_reward,
                    reason=f'CSR Activity: {act.name}',
                    source_model='csr.activity',
                    source_id=act.id,
                )

    def action_register_self(self):
        """Allow current user to register for this activity."""
        employee = self.env['hr.employee'].search(
            [('user_id', '=', self.env.uid)], limit=1)
        if not employee:
            raise ValidationError('No employee record linked to your user account.')
        if self.is_full:
            raise ValidationError('This activity is fully booked.')
        existing = self.env['employee.participation'].search([
            ('activity_id', '=', self.id),
            ('employee_id', '=', employee.id),
        ])
        if existing:
            raise ValidationError('You are already registered for this activity.')
        self.env['employee.participation'].create({
            'activity_id': self.id,
            'employee_id': employee.id,
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'message': f'Successfully registered for {self.name}!',
                           'type': 'success'}}


class CsrActivityTag(models.Model):
    _name = 'csr.activity.tag'
    _description = 'CSR Activity Tag'

    name = fields.Char(required=True)
    color = fields.Integer()
