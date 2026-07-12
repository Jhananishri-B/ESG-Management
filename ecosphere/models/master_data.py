# -*- coding: utf-8 -*-

from odoo import models, fields

# ESGDepartment and ESGCategory are defined in ecosphere_core module to prevent collision



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
