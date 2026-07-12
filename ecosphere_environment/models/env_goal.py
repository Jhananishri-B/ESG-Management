# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EnvGoal(models.Model):
    """
    Environmental Goal: A department-level carbon or environmental target.
    Extends the base ESG goal concept with environment-specific metrics
    such as reduction targets, baseline values, and achievement method.
    """
    _name = 'env.goal'
    _description = 'Environmental Goal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline asc, name'

    name = fields.Char(string='Goal Title', required=True, tracking=True)
    department_id = fields.Many2one(
        'esg.department', string='Department',
        required=True, ondelete='cascade', tracking=True)
    responsible_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user, tracking=True)

    # Target type
    goal_type = fields.Selection([
        ('carbon_reduction',  'Carbon Reduction'),
        ('energy_reduction',  'Energy Reduction'),
        ('water_reduction',   'Water Reduction'),
        ('waste_reduction',   'Waste Reduction'),
        ('renewable_energy',  'Renewable Energy %'),
        ('recycling_rate',    'Recycling Rate %'),
        ('custom',            'Custom Metric'),
    ], string='Goal Type', required=True, default='carbon_reduction')

    # Values
    baseline_value = fields.Float(
        string='Baseline Value', digits=(10, 2),
        help='Starting value before this goal period')
    target_value = fields.Float(
        string='Target Value', required=True, digits=(10, 2))
    current_value = fields.Float(
        string='Current Value', default=0.0, digits=(10, 2), tracking=True)
    unit = fields.Char(string='Unit', default='kg CO₂e')
    reduction_pct = fields.Float(
        string='Reduction %', compute='_compute_reduction_pct',
        store=True, digits=(5, 2))
    progress = fields.Float(
        string='Progress (%)', compute='_compute_progress',
        store=True, digits=(5, 2))

    # Dates
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    deadline = fields.Date(string='Deadline', required=True, tracking=True)

    # State
    state = fields.Selection([
        ('draft',    'Draft'),
        ('active',   'Active'),
        ('at_risk',  'At Risk'),
        ('achieved', 'Achieved'),
        ('failed',   'Failed'),
    ], string='Status', default='draft', tracking=True)

    priority = fields.Selection([('0', 'Normal'), ('1', 'High'), ('2', 'Critical')],
                                 default='0')
    notes = fields.Html(string='Notes')

    @api.depends('current_value', 'baseline_value')
    def _compute_reduction_pct(self):
        for goal in self:
            if goal.baseline_value:
                goal.reduction_pct = ((goal.baseline_value - goal.current_value)
                                      / goal.baseline_value * 100)
            else:
                goal.reduction_pct = 0.0

    @api.depends('current_value', 'target_value', 'baseline_value', 'goal_type')
    def _compute_progress(self):
        for goal in self:
            if goal.goal_type in ('carbon_reduction', 'energy_reduction',
                                   'water_reduction', 'waste_reduction'):
                # Lower is better
                if goal.baseline_value and goal.target_value < goal.baseline_value:
                    total_reduction = goal.baseline_value - goal.target_value
                    achieved = goal.baseline_value - goal.current_value
                    goal.progress = min(max((achieved / total_reduction) * 100, 0), 100)
                else:
                    goal.progress = 0.0
            else:
                # Higher is better
                if goal.target_value:
                    goal.progress = min((goal.current_value / goal.target_value) * 100, 100)
                else:
                    goal.progress = 0.0

    def action_activate(self):
        self.write({'state': 'active'})

    def action_achieve(self):
        self.write({'state': 'achieved'})
        self.message_post(body='🎉 Environmental goal achieved!')

    def action_fail(self):
        self.write({'state': 'failed'})

    @api.constrains('target_value', 'baseline_value')
    def _check_values(self):
        for goal in self:
            if goal.target_value <= 0:
                raise ValidationError('Target value must be greater than 0.')
