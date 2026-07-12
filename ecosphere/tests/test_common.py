# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestEcoSphereCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env['res.users'].create({
            'name': 'Test ESG Employee',
            'login': 'test_esg_employee',
            'email': 'test@esg.com',
        })
        cls.category_challenge = cls.env['esg.category'].create({
            'name': 'Challenge Category',
            'type': 'challenge',
        })
        cls.category_csr = cls.env['esg.category'].create({
            'name': 'CSR Category',
            'type': 'csr',
        })
        cls.challenge = cls.env['esg.challenge'].create({
            'title': 'Plant 10 Trees',
            'xp': 100,
            'category_id': cls.category_challenge.id,
            'status': 'active',
        })
        cls.csr_activity = cls.env['esg.csr.activity'].create({
            'name': 'Beach Clean Up',
            'points': 50,
            'category_id': cls.category_csr.id,
            'status': 'active',
        })
        cls.badge_xp = cls.env['esg.badge'].create({
            'name': 'XP Champion',
            'unlock_rule': 'XP >= 500',
        })
        cls.badge_challenges = cls.env['esg.badge'].create({
            'name': 'Challenge Master',
            'unlock_rule': 'Challenges >= 2',
        })
        cls.reward = cls.env['esg.reward'].create({
            'name': 'Green Mug',
            'points_required': 150,
            'stock': 5,
            'status': 'active',
        })

    def test_challenge_approval(self):
        """Test challenge approval workflow updates XP and triggers evaluation."""
        self.env['ir.config_parameter'].sudo().set_param('ecosphere.badge_toggle', 'True')

        participation = self.env['esg.challenge.participation'].create({
            'challenge_id': self.challenge.id,
            'employee_id': self.employee.id,
            'progress': 100.0,
            'approval_status': 'draft',
        })

        participation.action_approve_challenge()
        self.assertEqual(participation.approval_status, 'approved')
        self.assertEqual(participation.xp_awarded, 100)

        # Approve again to check double allocation prevention
        participation.action_approve_challenge()
        self.assertEqual(participation.xp_awarded, 100)

    def test_csr_approval(self):
        """Test CSR participation points allocation and evaluation."""
        self.env['ir.config_parameter'].sudo().set_param('ecosphere.badge_toggle', 'True')

        participation = self.env['esg.employee.participation'].create({
            'activity_id': self.csr_activity.id,
            'employee_id': self.employee.id,
            'approval_status': 'draft',
        })

        participation.action_approve_participation()
        self.assertEqual(participation.approval_status, 'approved')
        self.assertEqual(participation.points_earned, 50)

        # Approve again to verify duplicate prevention
        participation.action_approve_participation()
        self.assertEqual(participation.points_earned, 50)

    def test_reward_redemption_validation(self):
        """Test reward redemption checks stock, status, employee points."""
        inactive_reward = self.env['esg.reward'].create({
            'name': 'Inactive Reward',
            'points_required': 10,
            'stock': 5,
            'status': 'draft',
        })
        with self.assertRaises(ValidationError):
            inactive_reward.action_redeem_reward(self.employee)

        out_of_stock_reward = self.env['esg.reward'].create({
            'name': 'Out of Stock Reward',
            'points_required': 10,
            'stock': 0,
            'status': 'active',
        })
        with self.assertRaises(ValidationError):
            out_of_stock_reward.action_redeem_reward(self.employee)

        # Insufficient points check
        with self.assertRaises(ValidationError):
            self.reward.action_redeem_reward(self.employee)

        # Successful redemption with mock XP in context
        res = self.reward.with_context(mock_total_xp=200).action_redeem_reward(self.employee)
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(self.reward.stock, 4)

        # Inactivate when stock becomes 0
        single_stock_reward = self.env['esg.reward'].create({
            'name': 'Single Stock Reward',
            'points_required': 50,
            'stock': 1,
            'status': 'active',
        })
        single_stock_reward.with_context(mock_total_xp=100).action_redeem_reward(self.employee)
        self.assertEqual(single_stock_reward.stock, 0)
        self.assertEqual(single_stock_reward.status, 'inactive')

    def test_badge_evaluation_disabled(self):
        """Test badge evaluation skips when settings toggle is disabled."""
        self.env['ir.config_parameter'].sudo().set_param('ecosphere.badge_toggle', 'False')
        res = self.badge_xp.action_evaluate_badge(self.employee)
        self.assertEqual(res['params']['message'], 'Badge auto-awarding is currently disabled in settings.')

    def test_badge_evaluation_eligible(self):
        """Test badge evaluates eligibility based on unlock rules."""
        self.env['ir.config_parameter'].sudo().set_param('ecosphere.badge_toggle', 'True')

        # Eligible
        res = self.badge_xp.with_context(mock_total_xp=600).action_evaluate_badge(self.employee)
        self.assertEqual(res['params']['title'], 'Badge Awarded!')

        # Ineligible
        res = self.badge_xp.with_context(mock_total_xp=400).action_evaluate_badge(self.employee)
        self.assertEqual(res['params']['title'], 'Badge Evaluation')
        self.assertIn('does not meet requirements', res['params']['message'])

        # Duplicate check mock context
        res = self.badge_xp.with_context(
            mock_total_xp=600,
            mock_badge_ids=[self.badge_xp.id]
        ).action_evaluate_badge(self.employee)
        self.assertIn('already assigned', res['params']['message'])

    def test_badge_evaluation_invalid_rule(self):
        """Test invalid badge rule raises ValidationError."""
        self.env['ir.config_parameter'].sudo().set_param('ecosphere.badge_toggle', 'True')
        invalid_badge = self.env['esg.badge'].create({
            'name': 'Invalid',
            'unlock_rule': 'InvalidRuleExpression',
        })
        with self.assertRaises(ValidationError):
            invalid_badge.action_evaluate_badge(self.employee)
