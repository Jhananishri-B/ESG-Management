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
        
        # Simple leaderboard simulation based on active users
        users = env['res.users'].search([('share', '=', False)], limit=10)
        
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
            'users': users,
        }
        return request.render('ecosphere.dashboard_frontend', values)

    @http.route('/ecosphere/activity/join', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def join_activity(self, activity_id, **kw):
        try:
            activity_id = int(activity_id)
            request.env['esg.employee.participation'].create({
                'activity_id': activity_id,
                'employee_id': request.uid,
                'hours_contributed': 0.0,
                'status': 'draft',
            })
        except Exception as e:
            _logger.error("Error joining activity: %s", e)
        return request.redirect('/ecosphere/dashboard#social')

    @http.route('/ecosphere/challenge/join', type='http', auth='user', methods=['POST'], website=True, csrf=False)
    def join_challenge(self, challenge_id, **kw):
        try:
            challenge_id = int(challenge_id)
            request.env['esg.challenge.participation'].create({
                'challenge_id': challenge_id,
                'employee_id': request.uid,
                'progress': 0.0,
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
