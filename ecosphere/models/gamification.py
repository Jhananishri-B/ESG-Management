# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGBadge(models.Model):
    _name = 'esg.badge'
    _description = 'ESG Badge'

    name = fields.Char(string='Badge Name', required=True)
    description = fields.Text(string='Description')
    unlock_rule = fields.Char(string='Unlock Rule Description')
    icon = fields.Binary(string='Badge Icon')


class ESGReward(models.Model):
    _name = 'esg.reward'
    _description = 'ESG Reward'

    name = fields.Char(string='Reward Name', required=True)
    description = fields.Text(string='Description')
    points_required = fields.Integer(string='Points Required')
    stock = fields.Integer(string='Current Stock')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft')


class ESGChallenge(models.Model):
    _name = 'esg.challenge'
    _description = 'Sustainability Challenge'

    title = fields.Char(string='Challenge Title', required=True)
    category_id = fields.Many2one('esg.category', string='Category', domain=[('type', '=', 'challenge')])
    description = fields.Text(string='Description')
    xp = fields.Integer(string='XP Reward')
    difficulty = fields.Selection([
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], string='Difficulty', default='easy')
    evidence_required = fields.Boolean(string='Evidence Required', default=True)
    deadline = fields.Date(string='Deadline')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ], string='Status', default='draft')


class ESGChallengeParticipation(models.Model):
    _name = 'esg.challenge.participation'
    _description = 'Challenge Participation Record'

    challenge_id = fields.Many2one('esg.challenge', string='Challenge', required=True)
    employee_id = fields.Many2one('res.users', string='Employee', required=True)
    progress = fields.Float(string='Progress (%)')
    proof = fields.Binary(string='Proof / Evidence')
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval Status', default='draft')
    xp_awarded = fields.Integer(string='XP Awarded')
