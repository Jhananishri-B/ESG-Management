# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGPolicy(models.Model):
    _name = 'esg.policy'
    _description = 'ESG Policy'

    name = fields.Char(string='Policy Name', required=True)
    description = fields.Text(string='Policy Details')
    version = fields.Char(string='Version', default='1.0')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft')


class ESGPolicyAcknowledgement(models.Model):
    _name = 'esg.policy.acknowledgement'
    _description = 'Policy Acknowledgement'

    policy_id = fields.Many2one('esg.policy', string='Policy', required=True)
    employee_id = fields.Many2one('res.users', string='Employee', required=True)
    acknowledgement_date = fields.Date(string='Acknowledgement Date')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('acknowledged', 'Acknowledged')
    ], string='Status', default='draft')


class ESGAudit(models.Model):
    _name = 'esg.audit'
    _description = 'ESG Audit'

    name = fields.Char(string='Audit Name', required=True)
    auditor_id = fields.Many2one('res.users', string='Auditor')
    date = fields.Date(string='Audit Date')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft')


class ESGComplianceIssue(models.Model):
    _name = 'esg.compliance.issue'
    _description = 'ESG Compliance Issue'

    audit_id = fields.Many2one('esg.audit', string='Audit')
    severity = fields.Selection([
        ('minor', 'Minor'),
        ('major', 'Major'),
        ('critical', 'Critical')
    ], string='Severity', default='minor')
    description = fields.Text(string='Issue Description')
    owner_id = fields.Many2one('res.users', string='Owner', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    status = fields.Selection([
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved')
    ], string='Status', default='open')
