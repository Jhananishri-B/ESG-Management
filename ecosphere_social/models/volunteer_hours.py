# -*- coding: utf-8 -*-
from odoo import api, fields, models


class VolunteerHours(models.Model):
    """
    Volunteer Hours: Records credited volunteer time per employee per activity.
    Aggregated for social score calculation and reporting.
    """
    _name = 'volunteer.hours'
    _description = 'Volunteer Hours'
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                   required=True, ondelete='cascade', index=True)
    activity_id = fields.Many2one('csr.activity', string='CSR Activity', ondelete='set null')
    department_id = fields.Many2one(
        'esg.department', string='Department',
        related='activity_id.department_id', store=True, readonly=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.today)
    hours = fields.Float(string='Hours', required=True, digits=(6, 1))
    approved = fields.Boolean(string='Approved', default=False)
    notes = fields.Char(string='Notes')

    _sql_constraints = [
        ('hours_positive', 'CHECK(hours > 0)', 'Volunteer hours must be positive.'),
    ]

    @api.model
    def get_total_hours(self, employee_id, year=None):
        """Return total approved volunteer hours for an employee, optionally by year."""
        domain = [('employee_id', '=', employee_id), ('approved', '=', True)]
        if year:
            domain += [('date', '>=', f'{year}-01-01'), ('date', '<=', f'{year}-12-31')]
        records = self.search(domain)
        return sum(records.mapped('hours'))

    @api.model
    def get_department_totals(self, year=None):
        """Return dict of {department_id: total_hours} for dashboard."""
        domain = [('approved', '=', True)]
        if year:
            domain += [('date', '>=', f'{year}-01-01'), ('date', '<=', f'{year}-12-31')]
        records = self.search(domain)
        totals = {}
        for rec in records:
            did = rec.department_id.id
            totals[did] = totals.get(did, 0) + rec.hours
        return totals


class DiversityMetric(models.Model):
    """
    Diversity Metric: Periodic snapshot of diversity KPIs per department.
    Used in the Social score calculation and diversity dashboard.
    """
    _name = 'diversity.metric'
    _description = 'Diversity Metric'
    _order = 'period_date desc, department_id'

    department_id = fields.Many2one(
        'esg.department', string='Department', required=True, ondelete='cascade')
    period_date = fields.Date(string='Period (Start of Month)',
                               required=True, default=fields.Date.today)
    period_display = fields.Char(
        string='Period', compute='_compute_period_display', store=True)

    # Headcount
    total_employees = fields.Integer(string='Total Employees')
    female_count = fields.Integer(string='Female Employees')
    male_count = fields.Integer(string='Male Employees')
    other_gender_count = fields.Integer(string='Other / Not Specified')

    # Leadership
    leadership_total = fields.Integer(string='Leadership Positions')
    female_leadership = fields.Integer(string='Female in Leadership')

    # Computed ratios
    female_pct = fields.Float(
        string='Female (%)', compute='_compute_ratios', store=True, digits=(5, 1))
    female_leadership_pct = fields.Float(
        string='Female Leadership (%)', compute='_compute_ratios', store=True, digits=(5, 1))

    # Other diversity dimensions
    age_under_30 = fields.Integer(string='Under 30')
    age_30_50 = fields.Integer(string='Age 30–50')
    age_over_50 = fields.Integer(string='Over 50')

    new_hires = fields.Integer(string='New Hires (Period)')
    attrition = fields.Integer(string='Attrition (Period)')

    notes = fields.Text(string='Notes')

    @api.depends('period_date')
    def _compute_period_display(self):
        for dm in self:
            if dm.period_date:
                dm.period_display = dm.period_date.strftime('%B %Y')
            else:
                dm.period_display = ''

    @api.depends('total_employees', 'female_count', 'leadership_total', 'female_leadership')
    def _compute_ratios(self):
        for dm in self:
            dm.female_pct = (
                (dm.female_count / dm.total_employees * 100)
                if dm.total_employees else 0.0)
            dm.female_leadership_pct = (
                (dm.female_leadership / dm.leadership_total * 100)
                if dm.leadership_total else 0.0)
