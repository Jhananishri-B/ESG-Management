# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Core',
    'version': '18.0.1.0.0',
    'summary': 'EcoSphere ESG Management Platform — Core Foundation',
    'description': """
        EcoSphere Core provides the foundational models, configuration,
        security framework, and global theming for the EcoSphere ESG
        Management Platform. All other EcoSphere modules depend on this.
    """,
    'author': 'EcoSphere Team',
    'website': 'https://ecosphere.io',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web',
        'base_setup',
    ],
    'data': [
        # Security (must load first)
        'security/security.xml',
        'security/ir.model.access.csv',
        # Seed data
        'data/esg_category_data.xml',
        'data/esg_weight_config_data.xml',
        # Views
        'views/esg_category_views.xml',
        'views/esg_department_views.xml',
        'views/esg_goal_views.xml',
        'views/esg_weight_config_views.xml',
        'views/res_config_settings_views.xml',
        # Menus (load last)
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo_departments.xml',
        'demo/demo_goals.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecosphere_core/static/src/scss/ecosphere_theme.scss',
            'ecosphere_core/static/src/scss/ecosphere_components.scss',
            'ecosphere_core/static/src/js/ecosphere_utils.js',
        ],
        'web.assets_frontend': [
            'ecosphere_core/static/src/scss/ecosphere_portal.scss',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 1,
}
