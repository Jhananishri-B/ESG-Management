# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere AI',
    'version': '18.0.1.0.0',
    'summary': 'AI Integration for ESG Processes',
    'description': """
        Integrates AI (e.g., OpenAI) to assist with ESG tasks:
        - Auto-generate ESG Policies
        - Suggest carbon reduction strategies
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'base_setup',
        'ecosphere_core',
        'ecosphere_governance',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/ai_policy_generator_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
