# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Governance',
    'version': '18.0.1.0.0',
    'summary': 'Policy lifecycle, audits, compliance tracking, and risk register',
    'description': """
        EcoSphere Governance provides:
        - Policy creation and lifecycle management (draft → published → archived)
        - Employee policy acknowledgement tracking
        - Audit planning and execution
        - Compliance issue tracking with severity levels
        - Risk register with scoring matrix
        - Governance score calculation
        - Deadline reminders and escalation
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'ecosphere_core',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_actions.xml',
        'views/esg_policy_views.xml',
        'views/esg_audit_views.xml',
        'views/compliance_issue_views.xml',
        'views/risk_register_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo_policies.xml',
        'demo/demo_audits.xml',
        'demo/demo_compliance.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecosphere_governance/static/src/scss/governance.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
