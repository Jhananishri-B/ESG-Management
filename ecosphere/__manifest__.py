# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere – ESG Management Platform',
    'version': '18.0.1.0.0',
    'summary': 'Enterprise-grade ESG (Environmental, Social, Governance) Management Platform.',
    'description': """
EcoSphere – ESG Management Platform
===================================
A clean, scalable, and enterprise-grade ESG Management Platform for Odoo 18.
Provides features to track environmental, social, and governance metrics,
along with gamification elements and detailed reports.
""",
    'category': 'Sustainability',
    'author': 'Antigravity',
    'website': 'https://github.com/Jhananishri-B/ESG-Management',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'portal',
        'website',
        'ecosphere_core',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/dashboard_views.xml',
        'views/master_views.xml',
        'views/environment_views.xml',
        'views/social_views.xml',
        'views/governance_views.xml',
        'views/gamification_views.xml',
        'views/reports_views.xml',
        'views/settings_views.xml',
        'views/menus_views.xml',
        'views/frontend_templates.xml',
        'demo/demo_data.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {},
}
