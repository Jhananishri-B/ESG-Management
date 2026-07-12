# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGDepartmentScore(models.Model):
    _name = 'esg.department.score'
    _description = 'Department Score'

    department_id = fields.Many2one('esg.department', string='Department', required=True)
    environmental_score = fields.Float(string='Environmental Score')
    social_score = fields.Float(string='Social Score')
    governance_score = fields.Float(string='Governance Score')
    total_score = fields.Float(string='Total Score')
    period_start = fields.Date(string='Period Start')
    period_end = fields.Date(string='Period End')


class ESGDashboardCard(models.Model):
    _name = 'esg.dashboard.card'
    _description = 'ESG Dashboard Card'

    name = fields.Char(string='Card Title', required=True)
    value = fields.Char(string='Displayed Value')
    color = fields.Char(string='Color Code')
    sequence = fields.Integer(string='Sequence', default=10)


class ESGDashboardMetric(models.Model):
    _name = 'esg.dashboard.metric'
    _description = 'ESG Dashboard Metric Configuration'

    name = fields.Char(string='Metric Name', required=True)
    weight = fields.Float(string='Weight (Percentage)', default=1.0)
    category = fields.Selection([
        ('environmental', 'Environmental'),
        ('social', 'Social'),
        ('governance', 'Governance')
    ], string='Category', required=True)
