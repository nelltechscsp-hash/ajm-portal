from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'


    ajm_portal_access = fields.Selection(
        [('sales', 'Sales Portal'), ('cancellations', 'Cancellations Portal')],
        string='AJM Portal Access',
        compute='_compute_ajm_portal_access',
        inverse='_inverse_ajm_portal_access',
        store=False,
        help='Select portal access for this user. Automatically sets user as Portal and assigns department permissions.'
    )

    @api.depends('group_ids')
    def _compute_ajm_portal_access(self):
        """Compute which AJM portal the user has access to"""
        sales_group = self.env.ref('ajm_employee_portal.group_sales_portal_user', raise_if_not_found=False)
        cancel_group = self.env.ref('ajm_employee_portal.group_cancellations_portal_user', raise_if_not_found=False)

        for user in self:
            if sales_group and sales_group in user.group_ids:
                user.ajm_portal_access = 'sales'
            elif cancel_group and cancel_group in user.group_ids:
                user.ajm_portal_access = 'cancellations'
            else:
                user.ajm_portal_access = False

    def _inverse_ajm_portal_access(self):
        """Set AJM portal access - automatically converts user to Portal and assigns department group"""
        sales_group = self.env.ref('ajm_employee_portal.group_sales_portal_user')
        cancel_group = self.env.ref('ajm_employee_portal.group_cancellations_portal_user')
        portal_group = self.env.ref('base.group_portal')
        user_group = self.env.ref('base.group_user')
        public_group = self.env.ref('base.group_public')

        for user in self:
            commands = []

            # Remove both AJM portal groups
            commands.append((3, sales_group.id))
            commands.append((3, cancel_group.id))

            if user.ajm_portal_access:
                # Remove User/Employee group (backend access)
                commands.append((3, user_group.id))
                # Remove Public group if present (mutually exclusive with Portal)
                commands.append((3, public_group.id))
                # Ensure Portal group
                commands.append((4, portal_group.id))

                # Add selected portal group
                if user.ajm_portal_access == 'sales':
                    commands.append((4, sales_group.id))
                elif user.ajm_portal_access == 'cancellations':
                    commands.append((4, cancel_group.id))
                # Gmail prompt handled by ajm_user_gmail module

            if commands:
                user.sudo().write({'group_ids': commands})

    @api.model
    def create(self, vals):
        """Create user; Gmail configuration handled by ajm_user_gmail."""
        return super().create(vals)

    def write(self, vals):
        """Update user; Gmail configuration handled by ajm_user_gmail."""
        return super().write(vals)
