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
        joined_challenges = env['esg.challenge.participation'].search([
            ('employee_id', '=', request.uid)
        ]).mapped('challenge_id.id')
        
        # Employee Stats (XP and completions)
        u_challenges = env['esg.challenge.participation'].search([
            ('employee_id', '=', request.uid),
            ('approval_status', '=', 'approved')
        ])
        challenge_xp = sum(u_challenges.mapped('xp_awarded'))
        challenge_count = len(u_challenges)
        
        u_csrs = env['esg.employee.participation'].search([
            ('employee_id', '=', request.uid),
            ('approval_status', '=', 'approved')
        ])
        csr_points = sum(u_csrs.mapped('points_earned'))
        
        total_xp = employee.total_xp if hasattr(employee, 'total_xp') else (challenge_xp + csr_points)
        completed_challenges = employee.completed_challenges if hasattr(employee, 'completed_challenges') else challenge_count
        
        # Earned Badges
        earned_badges = env['esg.badge']
        if hasattr(employee, 'esg_badge_ids'):
            earned_badges = employee.esg_badge_ids
        else:
            for badge in env['esg.badge'].search([]):
                if badge.unlock_rule:
                    match = re.match(r'^(XP|Challenges)\s*(>=|<=|>|<|==|=)\s*(\d+)$', badge.unlock_rule.strip(), re.IGNORECASE)
                    if match:
                        metric, op, val_str = match.groups()
                        val = int(val_str)
                        current_val = total_xp if metric.upper() == 'XP' else completed_challenges
                        is_eligible = False
                        if op == '>=': is_eligible = (current_val >= val)
                        elif op == '<=': is_eligible = (current_val <= val)
                        elif op == '>': is_eligible = (current_val > val)
                        elif op == '<': is_eligible = (current_val < val)
                        elif op in ('==', '='): is_eligible = (current_val == val)
                        if is_eligible:
                            earned_badges |= badge
                            
        # Leaderboard (N+1 query avoided)
        users = env['res.users'].search([('share', '=', False)])
        all_badges = env['esg.badge'].search([])
        all_challenge_parts = env['esg.challenge.participation'].search([('approval_status', '=', 'approved')])
        all_csr_parts = env['esg.employee.participation'].search([('approval_status', '=', 'approved')])
        
        challenge_by_user = {}
        for p in all_challenge_parts:
            challenge_by_user.setdefault(p.employee_id.id, []).append(p)
            
        csr_by_user = {}
        for p in all_csr_parts:
            csr_by_user.setdefault(p.employee_id.id, []).append(p)
            
        leaderboard_data = []
        for user in users:
            u_parts = challenge_by_user.get(user.id, [])
            u_challenge_xp = sum(p.xp_awarded for p in u_parts)
            u_challenge_count = len(u_parts)
            
            u_csrs = csr_by_user.get(user.id, [])
            u_csr_points = sum(p.points_earned for p in u_csrs)
            
            u_xp = user.total_xp if hasattr(user, 'total_xp') else (u_challenge_xp + u_csr_points)
            u_comp_challenges = user.completed_challenges if hasattr(user, 'completed_challenges') else u_challenge_count
            
            if hasattr(user, 'esg_badge_ids'):
                badge_count = len(user.esg_badge_ids)
            else:
                badge_count = 0
                for badge in all_badges:
                    if badge.unlock_rule:
                        match = re.match(r'^(XP|Challenges)\s*(>=|<=|>|<|==|=)\s*(\d+)$', badge.unlock_rule.strip(), re.IGNORECASE)
                        if match:
                            metric, op, val_str = match.groups()
                            val = int(val_str)
                            current_val = u_xp if metric.upper() == 'XP' else u_comp_challenges
                            is_eligible = False
                            if op == '>=': is_eligible = (current_val >= val)
                            elif op == '<=': is_eligible = (current_val <= val)
                            elif op == '>': is_eligible = (current_val > val)
                            elif op == '<': is_eligible = (current_val < val)
                            elif op in ('==', '='): is_eligible = (current_val == val)
                            if is_eligible:
                                badge_count += 1
            
            leaderboard_data.append({
                'name': user.name,
                'xp': u_xp,
                'badge_count': badge_count,
                'status': 'Active' if user.active else 'Inactive',
            })
            
        leaderboard_data.sort(key=lambda x: x['xp'], reverse=True)
        
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
            'earned_badges': earned_badges,
            'leaderboard': leaderboard_data,
            'departments': departments,
            'environmental_score': environmental_score,
            'social_score': social_score,
            'governance_score': governance_score,
            'overall_score': overall_score,
            'employee': employee,
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
                # Compute actual XP to pass via context as mock_total_xp
                u_challenges = env['esg.challenge.participation'].search([
                    ('employee_id', '=', request.uid),
                    ('approval_status', '=', 'approved')
                ])
                challenge_xp = sum(u_challenges.mapped('xp_awarded'))
                
                u_csrs = env['esg.employee.participation'].search([
                    ('employee_id', '=', request.uid),
                    ('approval_status', '=', 'approved')
                ])
                csr_points = sum(u_csrs.mapped('points_earned'))
                
                calculated_xp = challenge_xp + csr_points
                
                # Pass calculated_xp in context under mock_total_xp
                reward.with_context(mock_total_xp=calculated_xp).action_redeem_reward(employee=request.env.user)
                return request.redirect(f'/ecosphere/dashboard?success=Successfully redeemed {reward.name}#gamification')
        except ValidationError as e:
            return request.redirect(f'/ecosphere/dashboard?warning={e.name}#gamification')
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
