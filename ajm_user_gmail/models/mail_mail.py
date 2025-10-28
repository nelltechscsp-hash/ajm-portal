from odoo import api, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _ajm_find_user_gmail_server(self):
        """Return ir.mail_server for the author user (if any) matching this mail, active and configured.
        Fallback: None if not possible.
        """
        self.ensure_one()
        MailServer = self.env['ir.mail_server'].sudo()

        # Determine user from author partner
        user = False
        if self.author_id:
            # partner -> related users (One2many)
            if hasattr(self.author_id, 'user_ids') and self.author_id.user_ids:
                user = self.author_id.user_ids[:1]
        if not user:
            # fallback to current user
            user = self.env.user
        if not user:
            return False

        name = False
        if hasattr(user, '_get_mail_server_name'):
            name = user._get_mail_server_name()
        if not name:
            return False

        server = MailServer.with_context(active_test=False).search([('name', '=', name)], limit=1)
        if server and server.active and server.smtp_user and server.smtp_pass:
            return server
        return False

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        try:
            # Do not override explicit assignment
            if not rec.mail_server_id:
                server = rec._ajm_find_user_gmail_server()
                if server:
                    rec.mail_server_id = server.id
        except Exception:
            # Never block mail creation due to heuristic failures
            pass
        return rec
