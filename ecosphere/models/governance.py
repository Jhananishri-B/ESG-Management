# -*- coding: utf-8 -*-

from odoo import models

class ESGGovernanceRecord(models.Model):
    _name = 'esg.governance.record'
    _description = 'Governance Metric Record'

class ESGBoardMeeting(models.Model):
    _name = 'esg.board.meeting'
    _description = 'Board Meeting Record'

class ESGPolicyCompliance(models.Model):
    _name = 'esg.policy.compliance'
    _description = 'Policy Compliance Record'
