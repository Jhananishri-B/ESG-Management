# -*- coding: utf-8 -*-

import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ESGCRActivity(models.Model):
    _name = 'esg.csr.activity'
    _description = 'CSR Activity'

    name = fields.Char(string='Activity Title', required=True)
    category_id = fields.Many2one(
        'esg.category',
        string='Category',
        domain=[('type', '=', 'csr')]
    )
    description = fields.Text(string='Description')
    date = fields.Date(string='Activity Date')
    points = fields.Integer(string='Base Points')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft')


class ESGEmployeeParticipation(models.Model):
    _name = 'esg.employee.participation'
    _description = 'Employee CSR Participation'

    employee_id = fields.Many2one(
        'res.users',
        string='Employee',
        required=True
    )

    activity_id = fields.Many2one(
        'esg.csr.activity',
        string='CSR Activity',
        required=True
    )

    proof = fields.Binary(string='Attachment / Proof')

    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval Status', default='draft')

    points_earned = fields.Integer(string='Points Earned')
    completion_date = fields.Date(string='Completion Date')

    def _award_employee_points(self, employee, points):
        """Helper to award ESG points to employee.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'esg_points'):
            employee.esg_points += points
        else:
            _logger.info("TODO Integration: Awarded %d ESG Points to Employee '%s'.", points, employee.name)

    def _increment_csr_count(self, employee):
        """Helper to increment CSR completions count for employee.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'csr_count'):
            employee.csr_count += 1
        else:
            _logger.info("TODO Integration: Incremented CSR participation count for Employee '%s'.", employee.name)

    def action_approve_participation(self):
        """
        Approve CSR participation and assign points.
        Prevents duplicate point allocation.
        """
        for rec in self:

            # Skip if points already allocated
            if rec.points_earned:
                continue

            vals = {}

            # Mark participation as approved
            if rec.approval_status != 'approved':
                vals['approval_status'] = 'approved'

            # Allocate default activity points
            points_to_award = rec.activity_id.points
            vals['points_earned'] = points_to_award

            # Update employee values (placeholders for ESG Employee Profile)
            employee = rec.employee_id
            if employee:
                rec._award_employee_points(employee, points_to_award)
                rec._increment_csr_count(employee)

                # Trigger badge evaluation
                if 'esg.badge' in self.env:
                    badges = self.env['esg.badge'].search([])
                    for badge in badges:
                        try:
                            badge.action_evaluate_badge(employee=employee)
                        except Exception as e:
                            _logger.warning("Error evaluating badge %s: %s", badge.name, e)

            rec.with_context(
                skip_approval_workflow=True
            ).write(vals)

            # Produce audit log
            _logger.info(
                "CSR approval workflow completed: Participant '%s' approved for activity '%s'. Awarded points: %d.",
                getattr(employee, 'name', str(employee)),
                rec.activity_id.name,
                points_to_award
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Participation Approved',
                'message': 'CSR participation has been approved successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        """
        Automatically trigger approval workflow when
        approval_status changes to 'approved'.
        """

        res = super(ESGEmployeeParticipation, self).write(vals)

        if (
            vals.get('approval_status') == 'approved'
            and not self.env.context.get('skip_approval_workflow')
        ):
            self.filtered(
                lambda rec: not rec.points_earned
            ).action_approve_participation()

        return res