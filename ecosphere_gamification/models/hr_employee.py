# -*- coding: utf-8 -*-
from odoo import api, fields, models
import math

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Gamification Fields
    esg_xp = fields.Integer(string='Total ESG XP', compute='_compute_esg_xp', store=True)
    esg_level = fields.Integer(string='ESG Level', compute='_compute_esg_xp', store=True)
    next_level_xp = fields.Integer(string='XP for Next Level', compute='_compute_esg_xp', store=True)
    xp_progress = fields.Float(string='Level Progress %', compute='_compute_esg_xp', store=True)
    
    xp_ledger_ids = fields.One2many('xp.ledger', 'employee_id', string='XP History')
    badge_ids = fields.Many2many('esg.badge', 'employee_badge_rel', 'employee_id', 'badge_id', string='Earned Badges')
    
    available_points = fields.Integer(string='Available Points (for Rewards)', compute='_compute_available_points', store=True)

    @api.depends('xp_ledger_ids.amount')
    def _compute_esg_xp(self):
        for employee in self:
            total_xp = sum(employee.xp_ledger_ids.mapped('amount'))
            employee.esg_xp = max(total_xp, 0)
            
            # Simple leveling formula: Level = floor(sqrt(XP / 100)) + 1
            # Level 1: 0-99, Level 2: 100-399, Level 3: 400-899, etc.
            current_level = math.floor(math.sqrt(employee.esg_xp / 100.0)) + 1 if employee.esg_xp > 0 else 1
            employee.esg_level = current_level
            
            # XP required for current level and next level
            current_level_xp = ((current_level - 1) ** 2) * 100
            next_level_xp = (current_level ** 2) * 100
            
            employee.next_level_xp = next_level_xp
            
            # Progress bar calculation
            xp_into_level = employee.esg_xp - current_level_xp
            level_size = next_level_xp - current_level_xp
            
            if level_size > 0:
                employee.xp_progress = (xp_into_level / level_size) * 100
            else:
                employee.xp_progress = 0.0

    @api.depends('xp_ledger_ids.amount', 'xp_ledger_ids.is_spendable')
    def _compute_available_points(self):
        for employee in self:
            # Sum only spendable transactions (e.g., earning points adds, redeeming rewards subtracts)
            spendable_entries = employee.xp_ledger_ids.filtered(lambda x: x.is_spendable)
            employee.available_points = sum(spendable_entries.mapped('amount'))

    def grant_xp(self, amount, reason, source_model=False, source_id=False, is_spendable=True):
        """Helper method to grant XP to an employee."""
        self.ensure_one()
        if amount == 0:
            return
            
        self.env['xp.ledger'].create({
            'employee_id': self.id,
            'amount': amount,
            'reason': reason,
            'source_model': source_model,
            'source_id': source_id,
            'is_spendable': is_spendable,
        })
        
        # Check if they leveled up and notify
        old_level = self.esg_level
        self._compute_esg_xp()  # Force recompute to check level
        if self.esg_level > old_level:
            self.message_post(
                body=f"🎉 Congratulations! You've reached <b>Level {self.esg_level}</b>!",
                subject="Level Up!"
            )
