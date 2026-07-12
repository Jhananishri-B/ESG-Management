# -*- coding: utf-8 -*-

import logging
from odoo import models, fields
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class ESGBadge(models.Model):
    _name = 'esg.badge'
    _description = 'ESG Badge'

    name = fields.Char(string='Badge Name', required=True)
    description = fields.Text(string='Description')
    unlock_rule = fields.Char(string='Unlock Rule Description')
    icon = fields.Binary(string='Badge Icon')

    def action_evaluate_badge(self, employee=None):
        """Evaluates check rules for a badge and triggers the auto-award flow.

        Args:
            employee (res.users, optional): The employee user record to evaluate.
                Defaults to None.

        Returns:
            dict: An Odoo client display notification action structure.

        Future Integration:
            This method will be extended to query employee points/challenges,
            verify double-allocation protection, and store relationships
            with employee badge tables.
        """
        # -----------------------------
        # Validation
        # -----------------------------
        self.ensure_one()

        if employee is None:
            raise ValidationError("Employee is required.")

        employee_name = getattr(employee, 'name', str(employee))

        # -----------------------------
        # Audit Logging (Start Evaluation)
        # -----------------------------
        _logger.info(
            "Badge evaluation started for Badge: '%s', Employee: '%s' at %s.",
            self.name,
            employee_name,
            fields.Datetime.now()
        )

        # -----------------------------
        # Future Workflow
        # -----------------------------
        # ==================================================
        # Future Badge Assignment Workflow
        #
        # 1. Check ESG Settings badge_toggle
        # 2. Parse unlock_rule
        # 3. Validate employee eligibility
        # 4. Prevent duplicate badge assignment
        # 5. Create employee badge relation
        # 6. Notify employee
        # ==================================================

        # -----------------------------
        # Audit Logging (Complete Evaluation)
        # -----------------------------
        _logger.info(
            "Badge evaluation completed for Badge: '%s', Employee: '%s' at %s.",
            self.name,
            employee_name,
            fields.Datetime.now()
        )

        # -----------------------------
        # User Notification
        # -----------------------------
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Badge Evaluation',
                'message': 'Badge evaluation completed successfully.\nActual assignment will occur once the employee badge profile module is available.',
                'type': 'success',
                'sticky': False,
            }
        }

    def check_and_assign_badge(self, employee=None):
        """Deprecated wrapper compatibility method calling action_evaluate_badge."""
        return self.action_evaluate_badge(employee)



class ESGReward(models.Model):
    _name = 'esg.reward'
    _description = 'ESG Reward'

    name = fields.Char(string='Reward Name', required=True)
    description = fields.Text(string='Description')
    points_required = fields.Integer(string='Points Required')
    stock = fields.Integer(string='Current Stock')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='draft')

    def action_redeem_reward(self, employee=None):
        """Redeem 1 unit of this reward for an employee."""
        self.ensure_one()

        # 1. Verify reward is active
        if self.status != 'active':
            raise ValidationError("Reward is not currently available.")

        # 2. Verify stock
        if self.stock <= 0:
            raise ValidationError("Reward is out of stock.")

        # 3. Verify employee
        if employee is None:
            raise ValidationError("Employee is required for redemption.")

        # TODO:
        # - Integrate with the ESG Employee Profile module.
        # - Validate employee has sufficient ESG points.
        # - Deduct reward points_required.
        # - Persist updated employee ESG balance.
        # - Record reward redemption history for auditing.

        # 5. Update Stock and Status
        vals = {}
        vals["stock"] = self.stock - 1
        if vals["stock"] <= 0:
            vals["status"] = "inactive"
        
        self.write(vals)

        # 6. Audit logging
        _logger.info(
            "Reward %s redeemed successfully by employee %s. Remaining stock: %d.",
            self.name,
            getattr(employee, 'name', str(employee)),
            vals["stock"]
        )

        # 7. Return Notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Reward Redeemed',
                'message': 'Reward redeemed successfully. Remaining stock has been updated.',
                'type': 'success',
                'sticky': False,
            }
        }



class ESGChallenge(models.Model):
    _name = 'esg.challenge'
    _description = 'Sustainability Challenge'

    title = fields.Char(string='Challenge Title', required=True)
    category_id = fields.Many2one('esg.category', string='Category', domain=[('type', '=', 'challenge')])
    description = fields.Text(string='Description')
    xp = fields.Integer(string='XP Reward')
    difficulty = fields.Selection([
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], string='Difficulty', default='easy')
    evidence_required = fields.Boolean(string='Evidence Required', default=True)
    deadline = fields.Date(string='Deadline')
    status = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('under_review', 'Under Review'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ], string='Status', default='draft')


class ESGChallengeParticipation(models.Model):
    _name = 'esg.challenge.participation'
    _description = 'Challenge Participation Record'

    challenge_id = fields.Many2one('esg.challenge', string='Challenge', required=True)
    employee_id = fields.Many2one('res.users', string='Employee', required=True)
    progress = fields.Float(string='Progress (%)')
    proof = fields.Binary(string='Proof / Evidence')
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Approval Status', default='draft')
    xp_awarded = fields.Integer(string='XP Awarded')

    def action_approve_challenge(self):
        """
        Approve challenge participation and award XP.
        Prevents duplicate XP allocation.
        """
        for rec in self:
            # Skip if XP already awarded
            if rec.xp_awarded > 0:
                continue

            # Verify challenge and XP value exist
            if not rec.challenge_id:
                continue
            if rec.challenge_id.xp <= 0:
                continue

            vals = {}

            # Mark challenge as approved
            if rec.approval_status != 'approved':
                vals['approval_status'] = 'approved'

            # Allocate default challenge XP
            vals['xp_awarded'] = rec.challenge_id.xp

            # TODO:
            # Update employee total XP when the
            # ESG Employee Profile module becomes available.

            rec.with_context(
                skip_challenge_workflow=True
            ).write(vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Challenge Approved',
                'message': 'Challenge approved and XP awarded successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

    def write(self, vals):
        """
        Automatically trigger approval workflow when
        approval_status changes to 'approved'.
        """
        res = super(ESGChallengeParticipation, self).write(vals)

        if (
            vals.get('approval_status') == 'approved'
            and not self.env.context.get('skip_challenge_workflow')
        ):
            self.filtered(
                lambda rec: not rec.xp_awarded
            ).action_approve_challenge()

        return res

