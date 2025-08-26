# -*- coding: utf-8 -*-
{
    'name': "Inspection Management",

    'summary': "Inspection Management",

    'description': """
 This module allows management of inspection.
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '17.0.0.1',
    'license': 'LGPL-3',

    'depends': ['base','mail','hr'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/inspectors_views.xml',
        'views/violations.xml',
        'views/penalties.xml',
        'views/inspection_type_views.xml',
        'views/plans_visits.xml',
        'views/menus.xml',
    ],
}
