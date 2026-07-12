# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGReportConfig(models.Model):
    _name = 'esg.report.config'
    _description = 'ESG Report Configuration'

    name = fields.Char(string='Report Title', required=True)
    report_type = fields.Selection([
        ('environmental', 'Environmental Report'),
        ('social', 'Social Report'),
        ('governance', 'Governance Report'),
        ('summary', 'ESG Summary Report')
    ], string='Report Type', default='summary', required=True)
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    department_ids = fields.Many2many('esg.department', string='Filter by Departments')
