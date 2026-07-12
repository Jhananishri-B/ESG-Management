# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Social',
    'version': '18.0.1.0.0',
    'summary': 'CSR activities, employee participation, volunteer hours, diversity metrics',
    'description': """
        EcoSphere Social module provides:
        - CSR activity calendar and management
        - Employee participation with evidence upload
        - Volunteer hours tracking
        - Training records
        - Diversity and inclusion metrics
        - Department engagement scoring
        - Participation approval workflow
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'ecosphere_core',
        'hr',
        'calendar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_actions.xml',
        'views/employee_participation_views.xml',
        'views/csr_activity_views.xml',
        'views/volunteer_hours_views.xml',
        'views/diversity_metric_views.xml',
        'views/menu.xml',
        'demo/demo_csr_activities.xml',
        'demo/demo_participation.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'ecosphere_social/static/src/scss/social.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
