# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGCRActivity(models.Model):
    _name = 'esg.csr.activity'
    _description = 'CSR Activity'

    name = fields.Char(string='Activity Title', required=True)
    category_id = fields.Many2one('esg.category', string='Category', domain=[('type', '=', 'csr')])
    description = fields.Text(string='Description')
    date = fields.Date(string='Activity Date')
    points = fields.Integer(string='Base Points')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft')


class ESGEmployeeParticipation(models.Model):
    _name = 'esg.employee.participation'
    _description = 'Employee CSR Participation'

    employee_id = fields.Many2one('res.users', string='Employee', required=True)
    activity_id = fields.Many2one('esg.csr.activity', string='CSR Activity', required=True)
    proof = fields.Binary(string='Attachment / Proof')
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval Status', default='draft')
    points_earned = fields.Integer(string='Points Earned')
    completion_date = fields.Date(string='Completion Date')
