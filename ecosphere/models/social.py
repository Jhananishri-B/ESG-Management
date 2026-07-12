# -*- coding: utf-8 -*-

from odoo import models, fields


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
            vals['points_earned'] = rec.activity_id.points

            # TODO:
            # Update employee ESG points balance when
            # Employee ESG Profile module becomes available.

            rec.with_context(
                skip_approval_workflow=True
            ).write(vals)

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