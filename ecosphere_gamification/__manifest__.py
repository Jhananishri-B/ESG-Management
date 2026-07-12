# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere Gamification',
    'version': '18.0.1.0.0',
    'summary': 'XP, Badges, Challenges, and Rewards for ESG Engagement',
    'description': """
        EcoSphere Gamification provides:
        - Employee XP tracking (ledger) and automatic leveling
        - ESG Badges (automated and manual awards)
        - Challenges (individual & team)
        - Reward store for redeeming XP
        - Leaderboards and engagement analytics
    """,
    'author': 'EcoSphere Team',
    'category': 'Sustainability/ESG',
    'license': 'LGPL-3',
    'depends': [
        'ecosphere_core',
        'ecosphere_social',
        'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/badge_data.xml',
        'views/hr_employee_views.xml',
        'views/xp_ledger_views.xml',
        'views/esg_badge_views.xml',
        'views/esg_challenge_views.xml',
        'views/esg_reward_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo_challenges.xml',
        'demo/demo_rewards.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecosphere_gamification/static/src/scss/gamification.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
