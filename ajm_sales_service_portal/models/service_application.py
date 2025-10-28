import json

from odoo import api, fields, models


class AjmServiceApplication(models.Model):
    _name = 'ajm.service.application'
    _description = 'Sales Service Application'
    _order = 'create_date desc'

    name = fields.Char(string='Reference', default=lambda self: self._default_name(), readonly=True)
    service_type = fields.Selection([
        ('new_company', 'Nueva compañía'),
        ('renewal', 'Renovación'),
        ('contract_insurance', 'Contratación de seguro'),
        ('endorsement', 'Endorsement'),
        ('permits', 'Permisos'),
        ('audits', 'Auditorías'),
    ], required=True, index=True, default='contract_insurance')

    # Applicant basic info (from Quick Quote)
    agent = fields.Char()
    client_name = fields.Char(string='Client Name (Legacy)')
    client_since = fields.Date(string='Client Since')
    effective_date = fields.Date()
    entity_number = fields.Char()
    name_insured = fields.Char(required=True)
    dba = fields.Char(string='DBA')
    owner = fields.Char()
    entity_type = fields.Selection([
        ('individual', 'Individual'),
        ('corporation', 'Corporation'),
        ('llc', 'LLC'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ])
    entity_type_other = fields.Char()

    carrier_type = fields.Selection([
        ('common_carrier', 'Common Carrier'),
        ('private_property', 'Private Carrier (Property)'),
        ('exempt_for_hire', 'Exempt For Hire'),
        ('authorized_for_hire', 'Authorized For Hire'),
        ('private_passenger_business', 'Priv. Pass. (Business)'),
        ('private_passenger_nonbusiness', 'Priv. Pass. (Non-business)'),
        ('government', 'State/Local/Federal Gov\'t'),
        ('indian_nation', 'Indian Nation'),
        ('migrant', 'Migrant'),
        ('us_mail', 'U.S. Mail'),
        ('other', 'Other'),
    ], string='Carrier Type')
    carrier_type_other = fields.Char()

    # Interstate / Intrastate scope
    operation_scope = fields.Selection([
        ('interstate', 'Interstate'),
        ('intrastate', 'Intrastate'),
    ], string='Operation Scope')

    mailing_street = fields.Char()
    mailing_city = fields.Char()
    mailing_state = fields.Char()
    mailing_zip = fields.Char()

    physical_street = fields.Char()
    physical_city = fields.Char()
    physical_state = fields.Char()
    physical_zip = fields.Char()

    garaging_street = fields.Char()
    garaging_city = fields.Char()
    garaging_state = fields.Char()
    garaging_zip = fields.Char()

    phone = fields.Char()
    email = fields.Char()
    years_in_business = fields.Integer()
    ein = fields.Char(string='EIN #')

    # Trailer/Operation Type
    trailer_type = fields.Selection([
        ('flatbed', 'Flatbed Operation'),
        ('reefer', 'Reefer Operation'),
        ('dry_van', 'Dry Van'),
        ('dump', 'Dump'),
        ('tanker', 'Tanker'),
        ('lowboy', 'Lowboy'),
        ('other', 'Other'),
    ], string='Trailer Type')
    trailer_type_other = fields.Char()

    # JSON payloads for repeating tables
    coverages_json = fields.Text(help='JSON list of coverages: type, limit, deductible, target')
    commodities_json = fields.Text(help='JSON list of commodities with percentage and reefer breakdown flag')
    drivers_json = fields.Text(help='JSON list of drivers: name, state, dl, dob, exp, hired')
    filings_json = fields.Text(help='JSON object with filings numbers (MC, USDOT, CA, TX, OR, UIIA, other)')
    vehicles_json = fields.Text(help='JSON list of vehicles: year, make, type, vin, gvw, radius, stated_value')
    history_json = fields.Text(help='JSON list of insurance history rows for past 3 years')

    notes = fields.Text()

    user_id = fields.Many2one('res.users', string='Submitted by', default=lambda self: self.env.user, index=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # Link to partner (client)
    partner_id = fields.Many2one('res.partner', string='Client', index=True)

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ], default='draft', index=True, string='Status')

    active = fields.Boolean(default=True, help='Set to false to archive the interview')

    def _default_name(self):
        seq = self.env['ir.sequence'].sudo().next_by_code('ajm.service.application')
        return seq or 'Service Application'

    @api.model
    def create(self, vals):
        """Override create to auto-generate partner"""
        record = super(AjmServiceApplication, self).create(vals)
        record.create_or_update_partner()
        return record

    def write(self, vals):
        """Override write to update partner when interview is modified"""
        result = super(AjmServiceApplication, self).write(vals)
        # Only update partner if significant fields changed
        significant_fields = {'name_insured', 'phone', 'email', 'owner', 'entity_type'}
        if any(field in vals for field in significant_fields):
            self.create_or_update_partner()
        return result

    def create_or_update_partner(self):
        """Create or update res.partner from interview data"""
        self.ensure_one()

        # Prepare data for partner creation
        filings = {}
        if self.filings_json:
            try:
                filings = json.loads(self.filings_json)
            except:
                pass

        application_data = {
            'name_insured': self.name_insured,
            'owner': self.owner,
            'dba': self.dba,
            'entity_type': self.entity_type,
            'entity_type_other': self.entity_type_other,
            'carrier_type': self.carrier_type,
            'carrier_type_other': self.carrier_type_other,
            'operation_scope': self.operation_scope,
            'phone': self.phone,
            'email': self.email,
            'years_in_business': self.years_in_business,
            'ein': self.ein,
            'trailer_type': self.trailer_type,
            'trailer_type_other': self.trailer_type_other,
            'mailing_street': self.mailing_street,
            'mailing_city': self.mailing_city,
            'mailing_state': self.mailing_state,
            'mailing_zip': self.mailing_zip,
            'physical_street': self.physical_street,
            'physical_city': self.physical_city,
            'physical_state': self.physical_state,
            'physical_zip': self.physical_zip,
            'garaging_street': self.garaging_street,
            'garaging_city': self.garaging_city,
            'garaging_state': self.garaging_state,
            'garaging_zip': self.garaging_zip,
            'filings': filings,
        }

        # Create or update partner
        partner = self.env['res.partner'].sudo().create_or_update_from_application(application_data)

        # Assign agent category
        agent_user = self.user_id or self.env.user
        category_name = f'Agent: {agent_user.name}'
        agent_category = self.env['res.partner.category'].sudo().search([
            ('name', '=', category_name)
        ], limit=1)

        if not agent_category:
            agent_category = self.env['res.partner.category'].sudo().create({
                'name': category_name,
                'color': (agent_user.id % 11) + 1,  # Random color
            })

        partner.sudo().write({
            'agent_category_id': agent_category.id,
        })

        # Link partner to this application
        if not self.partner_id:
            self.sudo().write({'partner_id': partner.id})

        return partner
