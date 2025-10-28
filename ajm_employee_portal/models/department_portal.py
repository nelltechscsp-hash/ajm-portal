from odoo import fields, models


class AjmDepartmentPortal(models.Model):
    _name = 'ajm.department.portal'
    _description = 'Department Portal'

    name = fields.Char(required=True)
    department_id = fields.Many2one('hr.department', required=True)
    route_url = fields.Char(string='Route URL', required=True)
