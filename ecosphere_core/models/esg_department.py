# -*- coding: utf-8 -*-
# pyrefly: ignore [missing-import]
from odoo import api, fields, models
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError


class EsgDepartment(models.Model):
    """
    ESG Department: Central entity for organizing ESG performance.
    Stores aggregated Environmental, Social, and Governance scores
    and provides department-level hierarchy for ESG reporting.
    """
    _name = 'esg.department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'ESG Department'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Department Name', required=True, translate=True)
    complete_name = fields.Char(
        string='Full Name', compute='_compute_complete_name',
        store=True, recursive=True)
    parent_id = fields.Many2one(
        'esg.department', string='Parent Department',
        index=True, ondelete='restrict')
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many('esg.department', 'parent_id', string='Sub-Departments')
    child_count = fields.Integer(string='Sub-departments', compute='_compute_child_count')

    manager_id = fields.Many2one(
        'res.users', string='ESG Manager',
        domain="[('share', '=', False)]")
    code = fields.Char(string='Department Code')
    head_id = fields.Many2one('res.users', string='Department Head', related='manager_id', readonly=False, store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='active')
    active = fields.Boolean(string='Active', default=True)
    color = fields.Integer(string='Color', default=0)
    sequence = fields.Integer(string='Sequence', default=10)

    # ESG Scores (0–100)
    env_score = fields.Float(
        string='Environmental Score', default=0.0,
        digits=(5, 2), help='Aggregated environmental performance score (0–100)')
    social_score = fields.Float(
        string='Social Score', default=0.0,
        digits=(5, 2), help='Aggregated social performance score (0–100)')
    governance_score = fields.Float(
        string='Governance Score', default=0.0,
        digits=(5, 2), help='Aggregated governance performance score (0–100)')
    esg_score = fields.Float(
        string='Overall ESG Score', compute='_compute_esg_score',
        store=True, digits=(5, 2))

    # Score trend (delta from last period)
    env_score_delta = fields.Float(string='Env Δ', default=0.0, digits=(5, 2))
    social_score_delta = fields.Float(string='Social Δ', default=0.0, digits=(5, 2))
    governance_score_delta = fields.Float(string='Gov Δ', default=0.0, digits=(5, 2))
    esg_score_delta = fields.Float(string='ESG Δ', compute='_compute_esg_score', store=True)

    # Carbon footprint (computed by ecosphere_environment)
    total_carbon_kg = fields.Float(
        string='Total Carbon (kg CO₂e)', default=0.0, digits=(10, 2))
    carbon_target_kg = fields.Float(
        string='Carbon Target (kg CO₂e)', default=0.0, digits=(10, 2))

    # Gamification stats
    total_xp = fields.Integer(string='Total XP', default=0)
    employee_count = fields.Integer(
        string='Employees', compute='_compute_employee_count', store=False)

    # Meta
    description = fields.Html(string='Description')
    logo = fields.Binary(string='Logo')
    tag_ids = fields.Many2many('esg.department.tag', string='Tags')

    # Rank (updated by scheduled action)
    esg_rank = fields.Integer(string='ESG Rank', default=0)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for dept in self:
            if dept.parent_id:
                dept.complete_name = f'{dept.parent_id.complete_name} / {dept.name}'
            else:
                dept.complete_name = dept.name

    @api.depends('env_score', 'social_score', 'governance_score')
    def _compute_esg_score(self):
        WeightConfig = self.env['esg.weight.config'].sudo()
        config = WeightConfig.search([], limit=1)
        w_env = config.weight_env / 100 if config else 0.40
        w_soc = config.weight_social / 100 if config else 0.30
        w_gov = config.weight_governance / 100 if config else 0.30
        for dept in self:
            dept.esg_score = (
                dept.env_score * w_env +
                dept.social_score * w_soc +
                dept.governance_score * w_gov
            )
            dept.esg_score_delta = (
                dept.env_score_delta * w_env +
                dept.social_score_delta * w_soc +
                dept.governance_score_delta * w_gov
            )

    def _compute_child_count(self):
        for dept in self:
            dept.child_count = len(dept.child_ids)

    def _compute_employee_count(self):
        """Count employees linked via ecosphere_social (optional dependency)."""
        try:
            Employee = self.env['hr.employee']
            for dept in self:
                dept.employee_count = Employee.search_count(
                    [('department_id.name', '=', dept.name)])
        except Exception:
            for dept in self:
                dept.employee_count = 0

    @api.constrains('parent_id')
    def _check_parent_cycle(self):
        if not self._check_recursion():
            raise ValidationError('A department cannot be its own ancestor.')

    def action_view_goals(self):
        return {
            'name': f'Goals — {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'esg.goal',
            'view_mode': 'list,form',
            'domain': [('department_id', '=', self.id)],
            'context': {'default_department_id': self.id},
        }

    def get_score_badge(self):
        """Return a CSS class based on ESG score range."""
        if self.esg_score >= 80:
            return 'eco-badge-excellent'
        elif self.esg_score >= 60:
            return 'eco-badge-good'
        elif self.esg_score >= 40:
            return 'eco-badge-average'
        return 'eco-badge-poor'


class EsgDepartmentTag(models.Model):
    _name = 'esg.department.tag'
    _description = 'ESG Department Tag'

    name = fields.Char(string='Tag', required=True)
    color = fields.Integer(string='Color')
