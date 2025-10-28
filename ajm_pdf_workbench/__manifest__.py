{
    'name': 'AJM PDF Workbench',
    'version': '1.0.0',
    'summary': 'Generación y edición de cartas y documentos PDF para clientes',
    'description': """
        Módulo para generar, editar y exportar cartas de compromiso y documentos rellenables en PDF,
        con datos autocompletados y formato profesional, desde el portal de clientes.
    """,
    'author': 'AJM Insurance & Trucking Services',
    'category': 'Website/Portal',
    'depends': [
        'base',
        'portal',
        'website',
        'mail',
    ],
    'data': [
        'views/carta_header_template.xml',   # <-- aquí agregamos tu header
        'views/pdf_workbench_sidebar.xml',
        'views/pdf_workbench_header.xml',
        'views/pdf_workbench_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ajm_pdf_workbench/static/src/css/pdf_workbench.css',
            'ajm_pdf_workbench/static/src/js/pdf_workbench.js',
            'ajm_pdf_workbench/static/src/js/pdf_paginator.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
