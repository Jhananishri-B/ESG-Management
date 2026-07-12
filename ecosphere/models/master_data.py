# -*- coding: utf-8 -*-

from odoo import models

class ESGDepartment(models.Model):
    _name = 'esg.department'
    _description = 'ESG Department'

class ESGCategory(models.Model):
    _name = 'esg.category'
    _description = 'ESG Category'

class ESGMetric(models.Model):
    _name = 'esg.metric'
    _description = 'ESG Metric Definition'
