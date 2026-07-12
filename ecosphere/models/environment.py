# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGEnvironmentalGoal(models.Model):
    _name = 'esg.environmental.goal'
    _description = 'Environmental Goal'

    name = fields.Char(string='Goal Name', required=True)
    target_value = fields.Float(string='Target Value')
    current_value = fields.Float(string='Current Value')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('failed', 'Failed')
    ], string='Status', default='draft')


class ESGCarbonTransaction(models.Model):
    _name = 'esg.carbon.transaction'
    _description = 'Carbon Transaction'

    name = fields.Char(string='Transaction Reference', required=True, default='New')
    date = fields.Date(string='Transaction Date', default=fields.Date.context_today)
    source_doc = fields.Char(string='Source Document')
    department_id = fields.Many2one('esg.department', string='Department')
    emission_factor_id = fields.Many2one('esg.emission.factor', string='Emission Factor')
    quantity = fields.Float(string='Quantity')
    calculated_co2 = fields.Float(string='Calculated CO2 (kg)')
    notes = fields.Text(string='Notes')
