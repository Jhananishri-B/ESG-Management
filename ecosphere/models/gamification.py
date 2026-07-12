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

    def _get_employee_xp(self, employee):
        """Helper to get employee's total XP.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'total_xp'):
            return employee.total_xp
        return self.env.context.get('mock_total_xp', 0)

    def _get_completed_challenges(self, employee):
        """Helper to get employee's completed challenges.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'completed_challenges'):
            return employee.completed_challenges
        return self.env.context.get('mock_completed_challenges', 0)

    def _get_employee_badges(self, employee):
        """Helper to get employee's badges to prevent duplicate badge assignment.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'esg_badge_ids'):
            return employee.esg_badge_ids
        mock_badge_ids = self.env.context.get('mock_badge_ids', [])
        return self.env['esg.badge'].browse(mock_badge_ids)

    def _assign_badge(self, employee):
        """Helper to create employee badge relationship.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'esg_badge_ids'):
            employee.write({'esg_badge_ids': [(4, self.id)]})
        else:
            _logger.info("TODO Integration: Created badge relationship. Badge '%s' linked to Employee '%s'.", self.name, employee.name)

    def action_evaluate_badge(self, employee=None):
        """Evaluates check rules for a badge and triggers the auto-award flow.

        Args:
            employee (res.users, optional): The employee user record to evaluate.
                Defaults to None.

        Returns:
            dict: An Odoo client display notification action structure.
        """
        self.ensure_one()

        if employee is None:
            raise ValidationError("Employee is required.")

        employee_name = getattr(employee, 'name', str(employee))

        _logger.info(
            "Badge evaluation started for Badge: '%s', Employee: '%s' at %s.",
            self.name,
            employee_name,
            fields.Datetime.now()
        )

        # 1. Check whether badge automation is enabled.
        badge_toggle = self.env['ir.config_parameter'].sudo().get_param('ecosphere.badge_toggle')
        if not badge_toggle or badge_toggle == 'False':
            _logger.info(
                "Badge auto-awarding is disabled in settings. Skipping evaluation for badge '%s' and employee '%s'.",
                self.name,
                employee_name
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Badge Evaluation',
                    'message': 'Badge auto-awarding is currently disabled in settings.',
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # 2. Parse unlock_rule and check eligibility
        is_eligible = False
        if self.unlock_rule:
            rule_str = self.unlock_rule.strip()
            import re
            match = re.match(r'^(XP|Challenges)\s*(>=|<=|>|<|==|=)\s*(\d+)$', rule_str, re.IGNORECASE)
            if not match:
                raise ValidationError(f"Invalid badge unlock rule: '{self.unlock_rule}'. Rules must match format like 'XP >= 500' or 'Challenges >= 5'.")

            metric, op, val_str = match.groups()
            val = int(val_str)

            # 3. Read employee profile values using helper methods
            if metric.upper() == 'XP':
                current_val = self._get_employee_xp(employee)
            elif metric.lower() == 'challenges':
                current_val = self._get_completed_challenges(employee)
            else:
                current_val = 0

            # 4. Check eligibility
            if op == '>=':
                is_eligible = (current_val >= val)
            elif op == '<=':
                is_eligible = (current_val <= val)
            elif op == '>':
                is_eligible = (current_val > val)
            elif op == '<':
                is_eligible = (current_val < val)
            elif op in ('==', '='):
                is_eligible = (current_val == val)
        else:
            is_eligible = False

        if not is_eligible:
            _logger.info(
                "Employee '%s' is not eligible for badge '%s'. Requirement not met: %s.",
                employee_name,
                self.name,
                self.unlock_rule
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Badge Evaluation',
                    'message': f"Employee {employee_name} does not meet requirements for Badge '{self.name}'.",
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # 5. Prevent duplicate badge assignment
        assigned_badges = self._get_employee_badges(employee)
        if self in assigned_badges:
            _logger.info(
                "Badge '%s' has already been assigned to Employee '%s'. Skipping duplicate award.",
                self.name,
                employee_name
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Badge Evaluation',
                    'message': f"Badge '{self.name}' is already assigned to {employee_name}.",
                    'type': 'warning',
                    'sticky': False,
                }
            }

        # 6. Create employee badge relationship
        self._assign_badge(employee)

        # 7. Create audit log
        _logger.info(
            "Badge evaluation completed successfully for Badge: '%s', Employee: '%s' (Eligible and Awarded) at %s.",
            self.name,
            employee_name,
            fields.Datetime.now()
        )

        # 8. Notify employee
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Badge Awarded!',
                'message': f"Congratulations! Badge '{self.name}' has been successfully awarded to {employee_name}.",
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

    def _get_employee_xp(self, employee):
        """Helper to retrieve employee points/XP.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'total_xp'):
            return employee.total_xp
        return self.env.context.get('mock_total_xp', 0)

    def _deduct_employee_xp(self, employee, points):
        """Helper to deduct points from employee.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'total_xp'):
            employee.total_xp -= points
        else:
            _logger.info("TODO Integration: Deducted %d XP/Points from Employee '%s'.", points, employee.name)

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

        # Retrieve employee points using helper methods
        employee_xp = self._get_employee_xp(employee)

        # Validate sufficient points
        if employee_xp < self.points_required:
            raise ValidationError(f"Insufficient XP. Employee has {employee_xp} XP, but {self.points_required} XP is required to redeem reward '{self.name}'.")

        # Deduct points
        self._deduct_employee_xp(employee, self.points_required)

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

    def _award_employee_xp(self, employee, xp):
        """Helper to award XP to employee.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'total_xp'):
            employee.total_xp += xp
        else:
            _logger.info("TODO Integration: Awarded %d XP to Employee '%s'.", xp, employee.name)

    def _increment_completed_challenges(self, employee):
        """Helper to increment completed challenges count.
        TODO: Integrate with the ESG Employee Profile module when available.
        """
        if hasattr(employee, 'completed_challenges'):
            employee.completed_challenges += 1
        else:
            _logger.info("TODO Integration: Incremented completed challenges count for Employee '%s'.", employee.name)

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
            xp_to_award = rec.challenge_id.xp
            vals['xp_awarded'] = xp_to_award

            # Update employee profile stats (helpers)
            employee = rec.employee_id
            if employee:
                rec._award_employee_xp(employee, xp_to_award)
                rec._increment_completed_challenges(employee)

                # Trigger badge evaluation engine for the employee
                badges = self.env['esg.badge'].search([])
                for badge in badges:
                    badge.action_evaluate_badge(employee=employee)

            rec.with_context(
                skip_challenge_workflow=True
            ).write(vals)

            # Record workflow completion in logs
            _logger.info(
                "Challenge approval workflow completed: Participant '%s' approved for challenge '%s'. Awarded XP: %d.",
                getattr(employee, 'name', str(employee)),
                rec.challenge_id.title,
                xp_to_award
            )

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

