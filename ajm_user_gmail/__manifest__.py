{
    'name': 'AJM User Gmail',
    'version': '19.0.1.0.0',
    'summary': 'Per-user Gmail SMTP setup and portal settings',
    'description': """
        Adds Gmail configuration per user (App Password), creates/updates an
        outgoing SMTP server (ir.mail_server) for each user, and provides a portal
        page for users to manage their Gmail settings. Also injects Gmail quick
        links into department dashboards and adds a top-level 'Correo' menu.
    """,
    'author': 'AJM Insurance & Trucking Services',
    'category': 'Tools',
    'depends': [
        'base',
        'mail',
        'website',
        'portal',
        'ajm_employee_portal',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/rules.xml',
        'views/portal_layout_logo.xml',
        'views/portal_gmail_settings.xml',
        'views/portal_mail_app.xml',
        'views/website_mail_tools.xml',
        'views/dashboard_inject.xml',
        'views/res_users_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
