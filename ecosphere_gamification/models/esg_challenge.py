# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

class EsgChallenge(models.Model):
    """
    ESG Challenges for employees or departments to participate in.
    """
    _name = 'esg.challenge'
    _description = 'ESG Challenge'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'end_date desc, name'

    name = fields.Char(string='Challenge Name', required=True, tracking=True)
    description = fields.Html(string='Description')
    
    challenge_type = fields.Selection([
        ('individual', 'Individual Challenge'),
        ('department', 'Department/Team Challenge')
    ], string='Challenge Type', default='individual', required=True, tracking=True)
    
    start_date = fields.Date(string='Start Date', required=True, tracking=True)
    end_date = fields.Date(string='End Date', required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    xp_reward = fields.Integer(string='XP Reward', required=True, help="XP awarded upon successful completion")
    badge_id = fields.Many2one('esg.badge', string='Reward Badge', help="Optional badge awarded upon completion")
    
    target_metric = fields.Integer(string='Target Metric (e.g. Hours, Points)')
    metric_uom = fields.Char(string='Metric Unit', default='Points')
    
    participation_ids = fields.One2many('challenge.participation', 'challenge_id', string='Participants')
    participant_count = fields.Integer(string='Participants', compute='_compute_participant_count')
    
    @api.depends('participation_ids')
    def _compute_participant_count(self):
        for challenge in self:
            challenge.participant_count = len(challenge.participation_ids)
            
    def action_start(self):
        self.write({'state': 'active'})
        
    def action_complete(self):
        self.write({'state': 'completed'})
        # In a real scenario, this would evaluate all participants and grant XP to winners/completers
        
    def action_cancel(self):
        self.write({'state': 'cancelled'})


class ChallengeParticipation(models.Model):
    """
    Tracks participation of an employee or department in a challenge.
    """
    _name = 'challenge.participation'
    _description = 'Challenge Participation'
    _order = 'current_metric desc'

    challenge_id = fields.Many2one('esg.challenge', string='Challenge', required=True, ondelete='cascade')
    challenge_type = fields.Selection(related='challenge_id.challenge_type', store=True)
    
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('esg.department', string='Department')
    
    current_metric = fields.Integer(string='Current Progress', default=0)
    target_metric = fields.Integer(related='challenge_id.target_metric', store=True)
    progress_pct = fields.Float(string='Progress %', compute='_compute_progress', store=True)
    
    state = fields.Selection([
        ('joined', 'Joined'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='joined')

    @api.depends('current_metric', 'target_metric')
    def _compute_progress(self):
        for record in self:
            if record.target_metric > 0:
                record.progress_pct = min((record.current_metric / record.target_metric) * 100.0, 100.0)
                if record.progress_pct >= 100.0 and record.state == 'joined':
                    record.action_complete()
            else:
                record.progress_pct = 0.0

    def action_complete(self):
        self.ensure_one()
        if self.state == 'completed':
            return
            
        self.state = 'completed'
        
        # Grant rewards
        if self.challenge_type == 'individual' and self.employee_id:
            if self.challenge_id.xp_reward > 0:
                self.employee_id.grant_xp(
                    self.challenge_id.xp_reward, 
                    f"Completed challenge: {self.challenge_id.name}",
                    'esg.challenge', self.challenge_id.id
                )
            if self.challenge_id.badge_id:
                self.employee_id.write({'badge_ids': [(4, self.challenge_id.badge_id.id)]})
                
        # (Team rewards logic would go here)

    _sql_constraints = [
        ('unique_emp_challenge', 'UNIQUE(challenge_id, employee_id)', 'An employee can only join a challenge once.'),
        ('unique_dept_challenge', 'UNIQUE(challenge_id, department_id)', 'A department can only join a challenge once.')
    ]
    
    @api.constrains('challenge_type', 'employee_id', 'department_id')
    def _check_participant_type(self):
        for record in self:
            if record.challenge_type == 'individual' and not record.employee_id:
                raise ValidationError("Individual challenges require an employee participant.")
            if record.challenge_type == 'department' and not record.department_id:
                raise ValidationError("Department challenges require a department participant.")
