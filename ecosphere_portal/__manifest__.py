# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Portal',
    'version': '18.0.1.0.0',
    'summary': 'Public ESG Portal and Whistleblower Reporting',
    'description': """
        Exposes ESG data to external stakeholders:
        - Public ESG Scorecard (/esg)
        - External Compliance/Whistleblower Reporting Form (/esg/report)
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'ecosphere_core',
        'ecosphere_governance',
    ],
    'data': [
        'views/portal_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
