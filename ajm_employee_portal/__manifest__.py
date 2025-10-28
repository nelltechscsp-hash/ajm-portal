{
    'name': 'AJM Employee Portal',
    'version': '19.0.1.0.0',
    'sequence': 100,
    'summary': 'Employee portal for AJM Insurance & Trucking Services',
    'description': """
        Employee web portal for AJM with:
        - Login and authentication
        - Personalized dashboard
        - Timecard (check-in/out)
        - Daily work tools
        - Form and PDF generation
    """,
    'author': 'AJM Insurance & Trucking Services',
    'category': 'Website',
    'depends': [
        'base',
        'web',
        'website',
        'portal',
        'auth_signup',
        'hr_attendance',
    ],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'data/hr_department.xml',
        'data/ajm_department_portal.xml',
        'views/employee_dashboard.xml',
        'views/cancellations_dashboard.xml',
        'views/website_top_menus.xml',
        'views/res_users_views.xml',
        'views/login_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ajm_employee_portal/static/src/css/portal.css',
            'ajm_employee_portal/static/src/js/portal.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
