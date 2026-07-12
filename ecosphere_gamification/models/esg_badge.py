# -*- coding: utf-8 -*-
from odoo import api, fields, models

class EsgBadge(models.Model):
    """
    Badges awarded to employees for milestones or special achievements.
    """
    _name = 'esg.badge'
    _description = 'ESG Badge'
    _order = 'sequence, name'

    name = fields.Char(string='Badge Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    image_1920 = fields.Image("Image", max_width=1920, max_height=1920)
    image_128 = fields.Image("Icon", related="image_1920", max_width=128, max_height=128, store=True)
    
    badge_type = fields.Selection([
        ('environment', 'Environment'),
        ('social', 'Social'),
        ('governance', 'Governance'),
        ('special', 'Special / Event')
    ], string='Category', default='social', required=True)
    
    level = fields.Selection([
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum')
    ], string='Rarity/Level', default='bronze')
    
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    
    # Auto-award rules (simple implementation for MVP)
    auto_award = fields.Boolean(string='Auto-award')
    rule_type = fields.Selection([
        ('xp_total', 'Total XP Reached'),
        ('volunteer_hours', 'Volunteer Hours Reached')
    ], string='Rule Type')
    rule_threshold = fields.Integer(string='Threshold')

    employee_ids = fields.Many2many('hr.employee', 'employee_badge_rel', 'badge_id', 'employee_id', string='Earned By')
    granted_count = fields.Integer(string='Times Awarded', compute='_compute_granted_count')

    @api.depends('employee_ids')
    def _compute_granted_count(self):
        for badge in self:
            badge.granted_count = len(badge.employee_ids)

    def action_grant_badge(self):
        """Action to manually grant badge to selected employees (via wizard or context)"""
        # A full implementation would use a wizard here.
        pass
