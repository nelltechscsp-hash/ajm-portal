from odoo import api, fields, models


class AjmMailTemplate(models.Model):
    _name = 'ajm.mail.template'
    _description = 'AJM Portal Mail Template'

    name = fields.Char(required=True)
    subject = fields.Char()
    body_html = fields.Html(sanitize=True)
    user_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user, index=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True)
