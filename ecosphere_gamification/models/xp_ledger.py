# -*- coding: utf-8 -*-
from odoo import api, fields, models

class XpLedger(models.Model):
    """
    Tracks all XP transactions (earning and spending).
    """
    _name = 'xp.ledger'
    _description = 'XP Ledger Transaction'
    _order = 'create_date desc'

    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, ondelete='cascade', index=True)
    department_id = fields.Many2one('esg.department', string='Department', related='employee_id.department_id', store=True)
    amount = fields.Integer(string='XP Amount', required=True)
    reason = fields.Char(string='Reason', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True)
    
    # Polymorphic link to source document (e.g. CSR Activity, Challenge, Reward Redemption)
    source_model = fields.Char(string='Source Model')
    source_id = fields.Integer(string='Source ID')
    
    # Is this transaction adding/removing spendable points? (True for earning, True (negative amount) for spending)
    is_spendable = fields.Boolean(string='Affects Spendable Points', default=True)

    def name_get(self):
        result = []
        for record in self:
            sign = "+" if record.amount > 0 else ""
            result.append((record.id, f"{sign}{record.amount} XP: {record.reason}"))
        return result
