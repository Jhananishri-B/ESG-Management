# -*- coding: utf-8 -*-

from odoo import models, fields

class ESGDepartment(models.Model):
    _name = 'esg.department'
    _description = 'ESG Department'

    name = fields.Char(string='Department Name', required=True)
    code = fields.Char(string='Department Code', required=True)
    head_id = fields.Many2one('res.users', string='Department Head')
    parent_id = fields.Many2one('esg.department', string='Parent Department')
    employee_count = fields.Integer(string='Employee Count')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft')


class ESGCategory(models.Model):
    _name = 'esg.category'
    _description = 'ESG Category'

    name = fields.Char(string='Category Name', required=True)
    type = fields.Selection([
        ('csr', 'CSR Activity Category'),
        ('challenge', 'Challenge Category')
    ], string='Type', required=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft')


class ESGEmissionFactor(models.Model):
    _name = 'esg.emission.factor'
    _description = 'Emission Factor'

    name = fields.Char(string='Factor Name', required=True)
    code = fields.Char(string='Code', required=True)
    factor = fields.Float(string='Factor Value (CO2e / Unit)')
    unit = fields.Char(string='Unit of Measure')


class ESGProductProfile(models.Model):
    _name = 'esg.product.profile'
    _description = 'Product ESG Profile'

    name = fields.Char(string='Product Name', required=True)
    carbon_footprint = fields.Float(string='Carbon Footprint (kg CO2e)')
    water_footprint = fields.Float(string='Water Footprint (L)')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft')
