# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class EsgDashboardController(http.Controller):

    @http.route('/ecosphere/dashboard_data', type='json', auth='user')
    def get_dashboard_data(self, **kwargs):
        """
        Provides aggregated ESG data for the OWL Dashboard component.
        """
        env = request.env
        
        # 1. Overall Company Score (Average of all active departments)
        departments = env['esg.department'].search([])
        total_depts = len(departments) or 1
        
        total_env = sum(departments.mapped('env_score'))
        total_soc = sum(departments.mapped('social_score'))
        total_gov = sum(departments.mapped('governance_score'))
        
        avg_env = round(total_env / total_depts, 1)
        avg_soc = round(total_soc / total_depts, 1)
        avg_gov = round(total_gov / total_depts, 1)
        
        overall_score = round((avg_env + avg_soc + avg_gov) / 3, 1)
        
        # 2. Leaderboard
        leaderboard = []
        for dept in sorted(departments, key=lambda d: d.total_esg_score, reverse=True)[:5]:
            leaderboard.append({
                'id': dept.id,
                'name': dept.name,
                'score': dept.total_esg_score,
                'env': dept.env_score,
                'soc': dept.social_score,
                'gov': dept.governance_score,
            })
            
        # 3. Trends (Mock historical data for chart.js - in a real app this would query a snapshot model)
        # We will generate a 6-month synthetic trend for the demo
        trend_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        trend_data = {
            'env': [max(0, avg_env - 10), max(0, avg_env - 8), max(0, avg_env - 5), max(0, avg_env - 4), max(0, avg_env - 2), avg_env],
            'soc': [max(0, avg_soc - 15), max(0, avg_soc - 12), max(0, avg_soc - 10), max(0, avg_soc - 6), max(0, avg_soc - 3), avg_soc],
            'gov': [max(0, avg_gov - 5), max(0, avg_gov - 4), max(0, avg_gov - 4), max(0, avg_gov - 3), max(0, avg_gov - 1), avg_gov],
        }
        
        # 4. Critical Alerts (Audits failing, overdue compliance)
        alerts = []
        critical_issues = env['compliance.issue'].search([('state', 'in', ('open', 'in_progress')), ('severity', '=', 'critical')], limit=5)
        for issue in critical_issues:
            alerts.append({
                'title': f"Critical Issue: {issue.name}",
                'type': 'danger',
                'date': str(issue.reported_date),
            })
            
        pending_policies = env['esg.policy'].search([('state', '=', 'published'), ('ack_rate', '<', 50.0)], limit=5)
        for pol in pending_policies:
            alerts.append({
                'title': f"Low Acknowledgement: {pol.name} ({pol.ack_rate}%)",
                'type': 'warning',
                'date': str(pol.acknowledgement_deadline),
            })

        return {
            'scores': {
                'overall': overall_score,
                'env': avg_env,
                'soc': avg_soc,
                'gov': avg_gov,
            },
            'leaderboard': leaderboard,
            'trends': {
                'labels': trend_labels,
                'data': trend_data,
            },
            'alerts': alerts[:5], # Keep top 5 alerts
        }
