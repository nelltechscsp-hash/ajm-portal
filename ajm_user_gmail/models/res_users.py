from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    gmail_address = fields.Char(
        string='Gmail Address',
        help='Personal Gmail address to use for outgoing email (SMTP). Defaults to the user login.'
    )
    gmail_app_password = fields.Char(
        string='Gmail App Password',
        help='16-character App Password generated in Google Account (Security > App passwords).',
    )
    needs_gmail_setup = fields.Boolean(
        string='Needs Gmail Setup',
        default=True,
        help='If enabled, the user will be prompted in the Portal to complete Gmail setup.'
    )

    def _get_mail_server_name(self):
        self.ensure_one()
        return f"Gmail: {self.login or self.email or self.name}"

    def _ensure_user_mail_server(self):
        """Create or update an ir.mail_server dedicated to this user.

        Uses smtp.gmail.com:587 (STARTTLS). Server is active only if both
        gmail_address and gmail_app_password are provided.
        """
        MailServer = self.env['ir.mail_server'].sudo()
        for user in self:
            name = user._get_mail_server_name()
            smtp_user = (user.gmail_address or user.login or '').strip()
            smtp_pass = (user.gmail_app_password or '').strip()
            active = bool(smtp_user and smtp_pass)
            sequence = 1000 + user.id

            server = MailServer.with_context(active_test=False).search([('name', '=', name)], limit=1)
            vals = {
                'name': name,
                'smtp_host': 'smtp.gmail.com',
                'smtp_port': 587,
                'smtp_encryption': 'starttls',
                'smtp_user': smtp_user,
                'smtp_pass': smtp_pass,
                'active': active,
                'sequence': sequence,
            }
            if server:
                server.write(vals)
            else:
                MailServer.create(vals)

    @api.model
    def create(self, vals):
        if not vals.get('gmail_address') and vals.get('login'):
            vals['gmail_address'] = vals['login']
        if 'needs_gmail_setup' not in vals:
            vals['needs_gmail_setup'] = True
        user = super().create(vals)
        user._ensure_user_mail_server()
        return user

    def write(self, vals):
        res = super().write(vals)
        if 'gmail_app_password' in vals:
            for user in self:
                if user.gmail_app_password:
                    user.needs_gmail_setup = False
        if {'gmail_address', 'gmail_app_password'} & set(vals.keys()):
            self._ensure_user_mail_server()
        return res
