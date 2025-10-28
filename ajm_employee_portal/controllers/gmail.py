import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AJMGmailSettings(http.Controller):

    @http.route('/my/settings/gmail', type='http', auth='user', website=True)
    def ajm_gmail_settings(self, **kw):
        """Render a simple form for users to configure their Gmail App Password."""
        user = request.env.user
        values = {
            'page_name': 'ajm_gmail_settings',
            'gmail_address': user.gmail_address or user.login,
            'needs_gmail_setup': user.needs_gmail_setup,
        }
        return request.render('ajm_employee_portal.portal_gmail_settings_page', values)

    @http.route('/my/settings/gmail/save', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def ajm_gmail_settings_save(self, **post):
        """Save Gmail address and app password for the current user."""
        user = request.env.user.sudo()
        gmail_address = (post.get('gmail_address') or '').strip()
        gmail_app_password = (post.get('gmail_app_password') or '').strip()

        vals = {}
        if gmail_address:
            vals['gmail_address'] = gmail_address
        if gmail_app_password:
            vals['gmail_app_password'] = gmail_app_password
            vals['needs_gmail_setup'] = False

        if vals:
            user.write(vals)
            # Ensure user's outgoing mail server is updated/created
            user._ensure_user_mail_server()
            message = 'Gmail settings updated successfully.'
        else:
            message = 'No changes to save.'

        request.session['portal_status_message'] = message
        return request.redirect('/my/settings/gmail')
