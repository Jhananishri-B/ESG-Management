# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class EsgPortal(http.Controller):

    @http.route(['/esg'], type='http', auth="public", website=True)
    def esg_scorecard(self, **kwargs):
        """
        Public ESG Scorecard showing aggregate scores for external stakeholders.
        """
        env = request.env
        departments = env['esg.department'].sudo().search([])
        total_depts = len(departments) or 1
        
        avg_env = round(sum(departments.mapped('env_score')) / total_depts, 1)
        avg_soc = round(sum(departments.mapped('social_score')) / total_depts, 1)
        avg_gov = round(sum(departments.mapped('governance_score')) / total_depts, 1)
        overall_score = round((avg_env + avg_soc + avg_gov) / 3, 1)

        values = {
            'overall_score': overall_score,
            'avg_env': avg_env,
            'avg_soc': avg_soc,
            'avg_gov': avg_gov,
            'department_count': total_depts,
        }
        return request.render("ecosphere_portal.public_esg_scorecard", values)

    @http.route(['/esg/report'], type='http', auth="public", website=True)
    def esg_report_issue(self, **kwargs):
        """
        Public form to report compliance or ethics issues (whistleblower function).
        """
        return request.render("ecosphere_portal.public_esg_report_form", {})

    @http.route(['/esg/report/submit'], type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def esg_report_submit(self, **post):
        """
        Handles the submission of the external report.
        """
        name = post.get('name', 'Anonymous')
        description = post.get('description', '')
        severity = post.get('severity', 'low')
        
        # Create compliance issue as sudo (since it's public)
        request.env['compliance.issue'].sudo().create({
            'name': f"External Report: {name}",
            'description': description,
            'severity': severity,
            'state': 'open',
        })
        
        return request.render("ecosphere_portal.public_esg_report_success", {})
