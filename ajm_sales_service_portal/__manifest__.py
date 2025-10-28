{
    'name': 'AJM Sales Service Portal',
    'version': '19.0.1.0.0',
    'summary': 'Customer service forms for Sales (portal)',
    'description': """
        Adds a Sales customer service portal with a menu of service requests and
        a comprehensive 'Contratación de seguro' form (based on Quick Quote PDF).
        Submissions are stored and visible in the backend for processing.
    """,
    'author': 'AJM Insurance & Trucking Services',
    'category': 'Website/Portal',
    'depends': [
        'base',
        'portal',
        'website',
        'mail',
        'ajm_employee_portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/backend_views.xml',
        'views/client_views.xml',
        'views/portal_form_partials.xml',
        'views/portal_forms.xml',
        'views/portal_interviews.xml',
        'views/portal_clients.xml',
        'views/dashboard_inject.xml',
    ],
        'external_dependencies': {
            'python': ['requests', 'lxml'],
        },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
