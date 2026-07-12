# -*- coding: utf-8 -*-

from odoo import models

class ESGSocialRecord(models.Model):
    _name = 'esg.social.record'
    _description = 'Social Metric Record'

class ESGEmployeeWellbeing(models.Model):
    _name = 'esg.employee.wellbeing'
    _description = 'Employee Wellbeing Record'

class ESGCommunityEngagement(models.Model):
    _name = 'esg.community.engagement'
    _description = 'Community Engagement Record'
