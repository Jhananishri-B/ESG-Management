# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Dashboard',
    'version': '18.0.1.0.0',
    'summary': 'Executive ESG Dashboard using OWL',
    'description': """
        Provides a real-time, interactive ESG executive dashboard:
        - Environmental, Social, and Governance scorecards
        - Department leaderboards
        - Trend analysis charts using Chart.js
        - AI Insights hook
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'ecosphere_core',
        'ecosphere_environment',
        'ecosphere_social',
        'ecosphere_governance',
        'web',
    ],
    'data': [
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecosphere_dashboard/static/src/scss/dashboard.scss',
            'ecosphere_dashboard/static/src/xml/dashboard.xml',
            'ecosphere_dashboard/static/src/js/dashboard.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
