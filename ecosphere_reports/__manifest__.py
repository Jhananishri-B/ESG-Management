# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Reports',
    'version': '18.0.1.0.0',
    'summary': 'QWeb PDF Reports and Analytics for ESG data',
    'description': """
        EcoSphere Reports provides printable QWeb PDF reports:
        - Department ESG Scorecard
        - Full ESG Audit Report
        - Policy Acknowledgement Status Report
        - Carbon Emission Summary
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'ecosphere_core',
        'ecosphere_environment',
        'ecosphere_governance',
    ],
    'data': [
        'reports/report_paperformat.xml',
        'reports/esg_department_report.xml',
        'reports/esg_audit_report.xml',
        'reports/esg_policy_report.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
