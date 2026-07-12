# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EsgCategory(models.Model):
    """
    ESG Category: Environmental, Social, or Governance.
    Used to classify all ESG metrics and goals.
    """
    _name = 'esg.category'
    _description = 'ESG Category'
    _order = 'sequence, name'

    name = fields.Char(string='Category Name', required=True, translate=True)
    code = fields.Selection([
        ('E', 'Environmental'),
        ('S', 'Social'),
        ('G', 'Governance'),
    ], string='Code', required=True)
    color = fields.Integer(string='Color Index', default=0)
    icon = fields.Char(string='Icon Class', default='fa-leaf',
                       help='Font Awesome icon class (e.g. fa-leaf, fa-users, fa-shield)')
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    type = fields.Selection([
        ('csr', 'CSR Activity Category'),
        ('challenge', 'Challenge Category'),
        ('other', 'Other'),
    ], string='Type', default='other')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='active')

    # Computed stats (populated by other modules)
    goal_count = fields.Integer(string='Goals', compute='_compute_goal_count')

    _sql_constraints = [
        ('unique_code', 'UNIQUE(code)', 'Each ESG category code must be unique.'),
    ]

    @api.depends()
    def _compute_goal_count(self):
        GoalModel = self.env.get('esg.goal')
        for rec in self:
            if GoalModel:
                rec.goal_count = GoalModel.search_count([('category_id', '=', rec.id)])
            else:
                rec.goal_count = 0

    def name_get(self):
        return [(r.id, f'[{r.code}] {r.name}') for r in self]
