# -*- coding: utf-8 -*-

from odoo import models

class ESGEnvironmentRecord(models.Model):
    _name = 'esg.environment.record'
    _description = 'Environmental Metric Record'

class ESGCarbonEmission(models.Model):
    _name = 'esg.carbon.emission'
    _description = 'Carbon Emission Record'

class ESGEnergyConsumption(models.Model):
    _name = 'esg.energy.consumption'
    _description = 'Energy Consumption Record'
