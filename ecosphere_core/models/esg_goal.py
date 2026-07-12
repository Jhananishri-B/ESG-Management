# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class EsgGoal(models.Model):
    """
    ESG Goal: A measurable target assigned to a department and ESG category.
    Tracks progress from current value toward a defined target, with
    deadline management and automated status transitions.
    """
    _name = 'esg.goal'
    _description = 'ESG Goal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline asc, name'

    name = fields.Char(string='Goal Title', required=True, tracking=True)
    description = fields.Html(string='Description')
    category_id = fields.Many2one(
        'esg.category', string='ESG Category', required=True, tracking=True)
    department_id = fields.Many2one(
        'esg.department', string='Department', required=True,
        tracking=True, ondelete='cascade')
    responsible_id = fields.Many2one(
        'res.users', string='Responsible', tracking=True,
        default=lambda self: self.env.user)

    # Target definition
    target_value = fields.Float(
        string='Target Value', required=True, digits=(10, 2),
        help='The numerical target to achieve (e.g., 100 kg CO₂ reduction)')
    current_value = fields.Float(
        string='Current Value', default=0.0, digits=(10, 2), tracking=True)
    unit = fields.Char(string='Unit', default='points',
                       help='Unit of measurement (e.g., kg CO₂e, hours, %)')
    progress = fields.Float(
        string='Progress (%)', compute='_compute_progress',
        store=True, digits=(5, 2))

    # Timeline
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    deadline = fields.Date(string='Deadline', required=True, tracking=True)
    days_remaining = fields.Integer(
        string='Days Remaining', compute='_compute_days_remaining')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('at_risk', 'At Risk'),
        ('achieved', 'Achieved'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    color = fields.Integer(string='Color', compute='_compute_color')
    priority = fields.Selection([
        ('0', 'Normal'), ('1', 'Important'), ('2', 'Critical')
    ], string='Priority', default='0')

    # Linked weight
    weight = fields.Float(
        string='Weight (%)', default=1.0, digits=(5, 2),
        help='Weight of this goal in the department ESG score calculation')

    @api.depends('current_value', 'target_value')
    def _compute_progress(self):
        for goal in self:
            if goal.target_value:
                goal.progress = min(
                    (goal.current_value / goal.target_value) * 100, 100.0)
            else:
                goal.progress = 0.0

    @api.depends('deadline')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for goal in self:
            if goal.deadline:
                goal.days_remaining = (goal.deadline - today).days
            else:
                goal.days_remaining = 0

    @api.depends('state', 'progress', 'days_remaining')
    def _compute_color(self):
        for goal in self:
            if goal.state == 'achieved':
                goal.color = 10  # green
            elif goal.state == 'failed':
                goal.color = 1   # red
            elif goal.state == 'at_risk':
                goal.color = 3   # orange
            elif goal.state == 'active':
                goal.color = 4   # blue
            else:
                goal.color = 0

    @api.constrains('target_value')
    def _check_target_value(self):
        for goal in self:
            if goal.target_value <= 0:
                raise ValidationError('Target value must be greater than 0.')

    @api.constrains('deadline', 'start_date')
    def _check_dates(self):
        for goal in self:
            if goal.deadline and goal.start_date and goal.deadline < goal.start_date:
                raise ValidationError('Deadline must be after the start date.')

    def action_activate(self):
        self.write({'state': 'active'})
        self.message_post(body='Goal activated.')

    def action_mark_achieved(self):
        self.write({'state': 'achieved', 'current_value': self.target_value})
        self._notify_achievement()

    def action_mark_failed(self):
        self.write({'state': 'failed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    def _notify_achievement(self):
        """Post a celebratory message when a goal is achieved."""
        for goal in self:
            goal.message_post(
                body=f'🎉 Goal <b>{goal.name}</b> has been achieved! '
                     f'({goal.current_value} / {goal.target_value} {goal.unit})',
                subtype_xmlid='mail.mt_comment',
            )

    def update_progress(self, new_value):
        """
        Update current value and auto-transition state.
        Called by environment/social/governance modules when metrics change.
        """
        self.ensure_one()
        old_value = self.current_value
        self.current_value = new_value
        if self.progress >= 100 and self.state == 'active':
            self.action_mark_achieved()
        elif self.days_remaining < 7 and self.progress < 70 and self.state == 'active':
            self.state = 'at_risk'
        _logger.info(
            'ESG Goal %s updated: %.2f → %.2f (progress: %.1f%%)',
            self.name, old_value, new_value, self.progress)

    def _cron_update_goal_states(self):
        """Scheduled action: flag at-risk goals."""
        active_goals = self.search([('state', '=', 'active')])
        for goal in active_goals:
            if goal.days_remaining < 7 and goal.progress < 70:
                goal.state = 'at_risk'
            elif goal.days_remaining < 0 and goal.progress < 100:
                goal.state = 'failed'
