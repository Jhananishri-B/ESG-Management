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
        
        # Evaluate badges
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
        challenges = env['esg.challenge'].search([('state', '=', 'active')])
        if not challenges:
            challenges = env['esg.challenge'].search([])
        rewards = env['esg.reward'].search([('active', '=', True)])
        
        # Joined Challenges for current employee
        ch_parts = env['challenge.participation'].search([
            ('employee_id.user_id', '=', request.uid)
        ])
        joined_challenges = ch_parts.mapped('challenge_id.id')
        challenge_progress = {p.challenge_id.id: p.progress_pct for p in ch_parts}
        
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
            
        # 1. Environmental Score
        if environmental_goals:
            env_progress = []
            for goal in environmental_goals:
                if goal.target_value:
                    progress = goal.current_value / goal.target_value
                    env_progress.append(min(1.0, progress))
                else:
                    env_progress.append(0.0)
            environmental_score = round((sum(env_progress) / len(environmental_goals)) * 100)
        else:
            environmental_score = 85  # Default baseline
            
        # 2. Social Score
        all_social_participations = env['esg.employee.participation'].search([])
        if all_social_participations:
            approved_social = all_social_participations.filtered(lambda p: p.approval_status == 'approved')
            social_score = round((len(approved_social) / len(all_social_participations)) * 100)
        else:
            social_score = 75  # Default baseline
            
        # 3. Governance Score
        all_policies = env['esg.policy'].search([])
        all_acknowledgements = env['esg.policy.acknowledgement'].search([])
        if all_acknowledgements:
            acknowledged = all_acknowledgements.filtered(lambda a: a.status == 'acknowledged')
            policy_rate = (len(acknowledged) / len(all_acknowledgements)) * 100
        else:
            policy_rate = 90.0
            
        all_issues = env['esg.compliance.issue'].search([])
        if all_issues:
            resolved_issues = all_issues.filtered(lambda i: i.status == 'resolved')
            issue_rate = (len(resolved_issues) / len(all_issues)) * 100
        else:
            issue_rate = 95.0
            
        governance_score = round((policy_rate + issue_rate) / 2)
        
        # 4. Overall Score
        overall_score = round((environmental_score + social_score + governance_score) / 3)

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
            'environmental_score': environmental_score,
            'social_score': social_score,
            'governance_score': governance_score,
            'overall_score': overall_score,
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
            # Check if already joined
            existing = request.env['esg.employee.participation'].search([
                ('activity_id', '=', activity_id),
                ('employee_id', '=', request.uid)
            ], limit=1)
            if not existing:
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

            # Find employee record for the current user
            employee = request.env['hr.employee'].search([('user_id', '=', request.uid)], limit=1)
            if not employee:
                return request.redirect('/ecosphere/dashboard?error=No employee profile found for your account#gamification')

            existing = env['challenge.participation'].search([
                ('challenge_id', '=', challenge_id),
                ('employee_id', '=', employee.id)
            ], limit=1)

            if existing:
                return request.redirect('/ecosphere/dashboard?warning=You have already joined this challenge#gamification')

            env['challenge.participation'].create({
                'challenge_id': challenge_id,
                'employee_id': employee.id,
            })
            return request.redirect(f'/ecosphere/dashboard?success=Successfully joined {challenge.name}#gamification')
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
