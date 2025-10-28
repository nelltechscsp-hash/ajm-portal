import base64
from odoo.tools.misc import file_open


def post_init_hook(env):
    """Initialize Gmail defaults and per-user outgoing mail servers for existing users.

    Also ensures the Website header logo is set to the AJM logo if currently empty.
    """
    Users = env['res.users'].sudo().search([])
    for u in Users:
        if not getattr(u, 'gmail_address', None) and u.login:
            u.gmail_address = u.login
        if not getattr(u, 'gmail_app_password', None):
            u.needs_gmail_setup = True
        try:
            u._ensure_user_mail_server()
        except Exception:
            # Never block installation due to email server creation errors
            pass

    # Set website logo if not set
    try:
        website = env['website'].sudo().search([], limit=1)
        if website and not website.logo:
            with file_open('ajm_user_gmail/static/img/mail_logo.png', 'rb') as f:
                data = base64.b64encode(f.read())
            website.write({'logo': data})
    except Exception:
        # Logo setup should never block installation/upgrade
        pass