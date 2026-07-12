# -*- coding: utf-8 -*-

import logging
import re
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class EcoSphereController(http.Controller):

    @http.route('/ecosphere/dashboard', type='http', auth='user', website=True)
    def esg_dashboard(self, **kw):
        env = request.env
        employee = request.env.user
        employee.invalidate_recordset(['total_xp', 'completed_challenges', 'spent_xp'])
        
        # Retroactively evaluate badges for current employee
        if 'esg.badge' in env:
            badges = env['esg.badge'].sudo().search([])
            for badge in badges:
                try:
                    badge.sudo().action_evaluate_badge(employee=employee)
                except Exception as e:
                    _logger.warning("Error evaluating badge %s: %s", badge.name, e)
        
        employee.invalidate_recordset(['esg_badge_ids'])
        
        # Capture notification messages
        success = kw.get('success')
        warning = kw.get('warning')
        error = kw.get('error')
        
        # Fetching Data
        dashboard_cards = env['esg.dashboard.card'].search([])
        environmental_goals = env['esg.environmental.goal'].search([])
        carbon_transactions = env['esg.carbon.transaction'].search([], limit=10)
        csr_activities = env['esg.csr.activity'].search([])
        participations = env['esg.employee.participation'].search([], limit=10)
        policies = env['esg.policy'].search([])
        audits = env['esg.audit'].search([])
        compliance_issues = env['esg.compliance.issue'].search([])
        departments = env['esg.department'].search([])
        
        # Gamification: Fetch only active challenges and active rewards
        challenges = env['esg.challenge'].search([('status', '=', 'active')])
        if not challenges:
            challenges = env['esg.challenge'].search([])
        rewards = env['esg.reward'].search([('status', '=', 'active')])
        if not rewards:
            rewards = env['esg.reward'].search([])
        
        # Joined Challenges for current employee
        ch_parts = env['esg.challenge.participation'].search([
            ('employee_id', '=', request.uid)
        ])
        joined_challenges = ch_parts.mapped('challenge_id.id')
        challenge_progress = {p.challenge_id.id: p.progress for p in ch_parts}
        
        # Joined CSR activities for current employee
        csr_parts = env['esg.employee.participation'].search([
            ('employee_id', '=', request.uid)
        ])
        joined_activities = csr_parts.mapped('activity_id.id')
        
        # Employee Stats from DB
        employee_total_xp = employee.total_xp
        employee_joined_challenges_count = len(joined_challenges)
        employee_earned_badges_count = len(employee.esg_badge_ids)
        employee_rewards_redeemed_count = employee.rewards_redeemed_count

        # Leaderboard (directly ordered by ORM search)
        users = env['res.users'].search([('share', '=', False)], order="total_xp desc")
        
        leaderboard_data = []
        for user in users:
            leaderboard_data.append({
                'name': user.name,
                'xp': user.total_xp,
                'badge_count': len(user.esg_badge_ids),
                'status': 'Active' if user.active else 'Inactive',
            })
            
        # Render View
        values = {
            'dashboard_cards': dashboard_cards,
            'environmental_goals': environmental_goals,
            'carbon_transactions': carbon_transactions,
            'csr_activities': csr_activities,
            'participations': participations,
            'policies': policies,
            'audits': audits,
            'compliance_issues': compliance_issues,
            'challenges': challenges,
            'rewards': rewards,
            'joined_challenges': joined_challenges,
            'joined_activities': joined_activities,
            'challenge_progress': challenge_progress,
            'earned_badges': employee.esg_badge_ids,
            'leaderboard': leaderboard_data,
            'departments': departments,
            'employee': employee,
            'employee_total_xp': employee_total_xp,
            'employee_joined_challenges_count': employee_joined_challenges_count,
            'employee_earned_badges_count': employee_earned_badges_count,
            'employee_rewards_redeemed_count': employee_rewards_redeemed_count,
            'success_message': success,
            'warning_message': warning,
            'error_message': error,
        }
        return request.render('ecosphere.dashboard_frontend', values)

    @http.route('/ecosphere/activity/join', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def join_activity(self, activity_id, **kw):
        try:
            activity_id = int(activity_id)
            request.env['esg.employee.participation'].create({
                'activity_id': activity_id,
                'employee_id': request.uid,
                'approval_status': 'draft',
            })
        except Exception as e:
            _logger.error("Error joining activity: %s", e)
        return request.redirect('/ecosphere/dashboard#social')

    @http.route([
        '/ecosphere/challenge/join',
        '/ecosphere/challenge/join/<int:challenge_id>'
    ], type='http', auth='user', methods=['POST', 'GET'], website=True, csrf=False)
    def join_challenge(self, challenge_id=None, **kw):
        try:
            if not challenge_id:
                challenge_id = int(kw.get('challenge_id', 0))
            challenge_id = int(challenge_id)
            env = request.env
            challenge = env['esg.challenge'].browse(challenge_id)
            if not challenge.exists():
                return request.redirect('/ecosphere/dashboard?error=Challenge not found#gamification')

            existing = env['esg.challenge.participation'].search([
                ('challenge_id', '=', challenge_id),
                ('employee_id', '=', request.uid)
            ], limit=1)

            if existing:
                return request.redirect('/ecosphere/dashboard?warning=You have already joined this challenge#gamification')

            env['esg.challenge.participation'].create({
                'challenge_id': challenge_id,
                'employee_id': request.uid,
                'progress': 0.0,
                'approval_status': 'draft',
                'xp_awarded': 0,
            })
            return request.redirect(f'/ecosphere/dashboard?success=Successfully joined {challenge.title}#gamification')
        except Exception as e:
            _logger.error("Error joining challenge: %s", e)
            return request.redirect('/ecosphere/dashboard?error=An error occurred trying to join the challenge#gamification')

    @http.route('/ecosphere/reward/redeem', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def redeem_reward(self, reward_id, **kw):
        try:
            reward_id = int(reward_id)
            env = request.env
            reward = env['esg.reward'].browse(reward_id)
            if reward.exists():
                request.env.user.invalidate_recordset(['total_xp', 'spent_xp'])
                # Call action_redeem_reward directly using user DB field total_xp
                reward.action_redeem_reward(employee=request.env.user)
                return request.redirect(f'/ecosphere/dashboard?success=Successfully redeemed {reward.name}#gamification')
        except ValidationError as e:
            return request.redirect(f'/ecosphere/dashboard?warning={e.args[0]}#gamification')
        except Exception as e:
            _logger.error("Error redeeming reward: %s", e)
            return request.redirect('/ecosphere/dashboard?error=An error occurred trying to redeem the reward#gamification')
        return request.redirect('/ecosphere/dashboard#gamification')

    @http.route('/ecosphere/carbon/log', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def log_carbon(self, name, quantity, emission_factor_id, department_id, **kw):
        try:
            request.env['esg.carbon.transaction'].create({
                'name': name,
                'quantity': float(quantity),
                'emission_factor_id': int(emission_factor_id),
                'department_id': int(department_id),
                'date': fields.Date.today(),
            })
        except Exception as e:
            _logger.error("Error logging carbon transaction: %s", e)
        return request.redirect('/ecosphere/dashboard#environmental')
