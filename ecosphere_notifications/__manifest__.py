# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Notifications',
    'version': '18.0.1.0.0',
    'summary': 'Automated ESG Notifications and Email Templates',
    'description': """
        Handles automated email communications:
        - Policy acknowledgement reminders
        - Gamification level-up congratulations
        - Compliance issue escalations
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'mail',
        'ecosphere_core',
        'ecosphere_governance',
        'ecosphere_gamification',
    ],
    'data': [
        'data/mail_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
