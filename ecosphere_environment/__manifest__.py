# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Environment',
    'version': '18.0.1.0.0',
    'summary': 'Carbon tracking, emission factors, environmental goals and forecasting',
    'description': """
        EcoSphere Environment module handles:
        - Emission factor library (scope 1, 2, 3)
        - Automatic carbon transaction creation from business events
        - Environmental goal tracking
        - Carbon forecasting with trend analysis
        - Department carbon hotspot visualization
        - Product ESG profiles
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'ecosphere_core',
        'product',       # for product ESG profiles
        'stock',         # for inventory-related emissions
        'purchase',      # for purchase order ESG integration
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/emission_factor_data.xml',
        'data/scheduled_actions.xml',
        'views/carbon_transaction_views.xml',
        'views/emission_factor_views.xml',
        'views/env_goal_views.xml',
        'views/product_esg_profile_views.xml',
        'views/menu.xml',
        'demo/demo_emission_factors.xml',
        'demo/demo_carbon_transactions.xml',
    ],
    'demo': [],
    'assets': {
        'web.assets_backend': [
            'ecosphere_environment/static/src/scss/environment.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
