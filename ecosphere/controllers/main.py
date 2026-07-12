# -*- coding: utf-8 -*-

import logging
from odoo import http, fields
from odoo.http import request

_logger = logging.getLogger(__name__)

class EcoSphereController(http.Controller):

    @http.route('/ecosphere/dashboard', type='http', auth='user', website=True)
    def esg_dashboard(self, **kw):
        env = request.env
        
        # Fetching Data
        dashboard_cards = env['esg.dashboard.card'].search([])
        environmental_goals = env['esg.environmental.goal'].search([])
        carbon_transactions = env['esg.carbon.transaction'].search([], limit=10)
        csr_activities = env['esg.csr.activity'].search([])
        participations = env['esg.employee.participation'].search([], limit=10)
        policies = env['esg.policy'].search([])
        audits = env['esg.audit'].search([])
        compliance_issues = env['esg.compliance.issue'].search([])
        challenges = env['esg.challenge'].search([])
        badges = env['esg.badge'].search([])
        departments = env['esg.department'].search([])
        
        # ----------------------------------------------------
        # Dynamic Score Calculations
        # ----------------------------------------------------
        
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

        # ----------------------------------------------------
        # Dynamic Leaderboard Simulation
        # ----------------------------------------------------
        users = env['res.users'].search([('share', '=', False)], limit=15)
        leaderboard = []
        for user in users:
            # Sum up points from approved CSR participations
            csr_points = sum(env['esg.employee.participation'].search([
                ('employee_id', '=', user.id),
                ('approval_status', '=', 'approved')
            ]).mapped('points_earned'))
            
            # Sum up XP from approved challenge participations
            challenge_xp = sum(env['esg.challenge.participation'].search([
                ('employee_id', '=', user.id),
                ('approval_status', '=', 'approved')
            ]).mapped('challenge_id.xp'))
            
            total_xp = csr_points + challenge_xp
            leaderboard.append({
                'user': user,
                'xp': total_xp or 100, # default minimum for display aesthetics
            })
            
        # Sort leaderboard by XP descending
        leaderboard = sorted(leaderboard, key=lambda k: k['xp'], reverse=True)

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
            'badges': badges,
            'departments': departments,
            'leaderboard': leaderboard,
            'environmental_score': environmental_score,
            'social_score': social_score,
            'governance_score': governance_score,
            'overall_score': overall_score,
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

    @http.route('/ecosphere/challenge/join', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def join_challenge(self, challenge_id, **kw):
        try:
            challenge_id = int(challenge_id)
            # Check if already joined
            existing = request.env['esg.challenge.participation'].search([
                ('challenge_id', '=', challenge_id),
                ('employee_id', '=', request.uid)
            ], limit=1)
            if not existing:
                request.env['esg.challenge.participation'].create({
                    'challenge_id': challenge_id,
                    'employee_id': request.uid,
                    'approval_status': 'draft',
                })
        except Exception as e:
            _logger.error("Error joining challenge: %s", e)
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
