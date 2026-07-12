# -*- coding: utf-8 -*-

from odoo import models

class ESGDashboardCard(models.Model):
    _name = 'esg.dashboard.card'
    _description = 'ESG Dashboard Card'

class ESGDashboardMetric(models.Model):
    _name = 'esg.dashboard.metric'
    _description = 'ESG Dashboard Metric Configuration'
