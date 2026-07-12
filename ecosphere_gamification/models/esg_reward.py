# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class EsgReward(models.Model):
    """
    Rewards that employees can redeem using their available XP points.
    """
    _name = 'esg.reward'
    _description = 'ESG Reward'
    _order = 'cost asc, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reward Name', required=True)
    description = fields.Text(string='Description')
    image = fields.Image("Image", max_width=1024, max_height=1024)
    
    cost = fields.Integer(string='XP Cost', required=True, tracking=True)
    quantity_available = fields.Integer(string='Quantity Available', default=999)
    is_unlimited = fields.Boolean(string='Unlimited Supply', default=False)
    
    active = fields.Boolean(default=True)
    
    reward_type = fields.Selection([
        ('swag', 'Company Swag (Merch)'),
        ('time_off', 'Extra Time Off (Hours)'),
        ('donation', 'Charitable Donation'),
        ('gift_card', 'Gift Card'),
        ('other', 'Other')
    ], string='Reward Type', default='swag')
    
    redemption_ids = fields.One2many('reward.redemption', 'reward_id', string='Redemptions')
    total_redeemed = fields.Integer(string='Total Redeemed', compute='_compute_total_redeemed')

    @api.depends('redemption_ids')
    def _compute_total_redeemed(self):
        for reward in self:
            reward.total_redeemed = len(reward.redemption_ids.filtered(lambda r: r.state != 'cancelled'))


class RewardRedemption(models.Model):
    """
    Tracks an employee redeeming their points for a reward.
    """
    _name = 'reward.redemption'
    _description = 'Reward Redemption'
    _order = 'date desc'
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, default=lambda self: self.env.user.employee_id)
    reward_id = fields.Many2one('esg.reward', string='Reward', required=True)
    cost = fields.Integer(related='reward_id.cost', string='Cost', store=True)
    
    date = fields.Datetime(string='Redemption Date', default=fields.Datetime.now, required=True)
    
    state = fields.Selection([
        ('requested', 'Requested'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='requested', tracking=True)
    
    notes = fields.Text(string='Notes / Address / Details')

    @api.model
    def create(self, vals):
        employee = self.env['hr.employee'].browse(vals.get('employee_id'))
        reward = self.env['esg.reward'].browse(vals.get('reward_id'))
        
        # Check points
        if employee.available_points < reward.cost:
            raise UserError(f"Not enough points. You need {reward.cost} XP but only have {employee.available_points} available.")
            
        # Check inventory
        if not reward.is_unlimited and reward.quantity_available <= 0:
            raise UserError("This reward is out of stock.")
            
        # Deduct inventory
        if not reward.is_unlimited:
            reward.quantity_available -= 1
            
        # Create redemption
        record = super().create(vals)
        
        # Deduct points (negative amount, is_spendable=True)
        employee.grant_xp(
            -reward.cost, 
            f"Redeemed reward: {reward.name}",
            'reward.redemption', record.id,
            is_spendable=True
        )
        
        return record

    def action_fulfill(self):
        self.write({'state': 'fulfilled'})

    def action_cancel(self):
        if self.state == 'fulfilled':
            raise UserError("Cannot cancel a fulfilled reward. Return inventory manually if needed.")
        
        self.write({'state': 'cancelled'})
        
        # Return points
        self.employee_id.grant_xp(
            self.cost, 
            f"Refunded reward: {self.reward_id.name}",
            'reward.redemption', self.id,
            is_spendable=True
        )
        
        # Return inventory
        if not self.reward_id.is_unlimited:
            self.reward_id.quantity_available += 1
