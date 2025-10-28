# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Client Type
    client_type = fields.Selection([
        ('transport', 'Transport'),
        ('health', 'Health'),
    ], string='Client Type', help='Type of insurance client')

    # Agent Category for organization
    agent_category_id = fields.Many2one(
        'res.partner.category',
        string='Agent Group',
        help='Sales agent group for organization'
    )

    # Transport-specific fields
    usdot = fields.Char(string='USDOT#')
    mc_number = fields.Char(string='MC#')
    ca_number = fields.Char(string='CA#')
    tx_number = fields.Char(string='TX#')
    or_number = fields.Char(string='OR#')
    uiia_number = fields.Char(string='UIIA#')
    ein = fields.Char(string='EIN#')

    entity_type = fields.Selection([
        ('individual', 'Individual'),
        ('corporation', 'Corporation'),
        ('llc', 'LLC'),
        ('partnership', 'Partnership'),
        ('other', 'Other'),
    ], string='Entity Type')
    entity_type_other = fields.Char(string='Entity Type Other')

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
    carrier_type_other = fields.Char(string='Carrier Type Other')

    operation_scope = fields.Selection([
        ('interstate', 'Interstate'),
        ('intrastate', 'Intrastate'),
    ], string='Type of Operation')

    trailer_type = fields.Selection([
        ('flatbed', 'Flatbed Operation'),
        ('reefer', 'Reefer Operation'),
        ('dry_van', 'Dry Van'),
        ('dump', 'Dump'),
        ('tanker', 'Tanker'),
        ('lowboy', 'Lowboy'),
        ('other', 'Other'),
    ], string='Trailer Type / Operation')
    trailer_type_other = fields.Char(string='Trailer Type Other')

    years_in_business = fields.Integer(string='Years in Business')

    # Owner/Contact info (for transport companies)
    owner_name = fields.Char(string='Owner Name')
    dba = fields.Char(string='DBA (Doing Business As)')

    # Address fields (Odoo already has street, city, state, zip)
    # Physical address
    physical_street = fields.Char(string='Physical Address Street')
    physical_city = fields.Char(string='Physical City')
    physical_state = fields.Char(string='Physical State (Text)')
    physical_state_id = fields.Many2one('res.country.state', string='Physical State')
    physical_zip = fields.Char(string='Physical Zip')

    # Garaging address
    garaging_street = fields.Char(string='Garaging Address Street')
    garaging_city = fields.Char(string='Garaging City')
    garaging_state = fields.Char(string='Garaging State (Text)')
    garaging_state_id = fields.Many2one('res.country.state', string='Garaging State')
    garaging_zip = fields.Char(string='Garaging Zip')

    # Health-specific fields
    date_of_birth = fields.Date(string='Date of Birth')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], string='Gender')
    ssn = fields.Char(string='SSN (Last 4 digits only)', help='Store only last 4 digits for security')

    # Link to service applications
    application_ids = fields.One2many(
        'ajm.service.application',
        'partner_id',
        string='Insurance Interviews'
    )

    @api.model
    def create_or_update_from_application(self, application_data):
        """
        Create or update partner from service application data
        Returns: partner record
        """
        # Determine client type (default to transport for now)
        client_type = 'transport'

        # Prepare partner values
        vals = {
            'client_type': client_type,
            'is_company': True if client_type == 'transport' else False,
        }

        # Name: For transport = company name, for health = person name
        if client_type == 'transport':
            vals['name'] = application_data.get('name_insured') or 'Unnamed Client'
            vals['owner_name'] = application_data.get('owner')

        # Transport-specific fields
        if client_type == 'transport':
            vals.update({
                'usdot': application_data.get('filings', {}).get('usdot'),
                'mc_number': application_data.get('filings', {}).get('mc'),
                'ca_number': application_data.get('filings', {}).get('ca'),
                'tx_number': application_data.get('filings', {}).get('tx'),
                'or_number': application_data.get('filings', {}).get('or'),
                'uiia_number': application_data.get('filings', {}).get('uiia'),
                'ein': application_data.get('ein'),
                'entity_type': application_data.get('entity_type'),
                'entity_type_other': application_data.get('entity_type_other'),
                'carrier_type': application_data.get('carrier_type'),
                'carrier_type_other': application_data.get('carrier_type_other'),
                'operation_scope': application_data.get('operation_scope'),
                'trailer_type': application_data.get('trailer_type'),
                'trailer_type_other': application_data.get('trailer_type_other'),
                'years_in_business': application_data.get('years_in_business'),
                'dba': application_data.get('dba'),
            })

        # Contact info
        vals.update({
            'phone': application_data.get('phone'),
            'email': application_data.get('email'),
        })

        # Mailing address (default Odoo fields)
        vals.update({
            'street': application_data.get('mailing_street'),
            'city': application_data.get('mailing_city'),
            'state_id': self._get_state_id(application_data.get('mailing_state')),
            'zip': application_data.get('mailing_zip'),
        })

        # Physical address
        vals.update({
            'physical_street': application_data.get('physical_street'),
            'physical_city': application_data.get('physical_city'),
            'physical_state': application_data.get('physical_state'),
            'physical_zip': application_data.get('physical_zip'),
        })

        # Garaging address
        vals.update({
            'garaging_street': application_data.get('garaging_street'),
            'garaging_city': application_data.get('garaging_city'),
            'garaging_state': application_data.get('garaging_state'),
            'garaging_zip': application_data.get('garaging_zip'),
        })

        # Try to find existing partner by USDOT or email
        partner = None
        if client_type == 'transport' and vals.get('usdot'):
            partner = self.search([('usdot', '=', vals['usdot'])], limit=1)
        elif vals.get('email'):
            partner = self.search([('email', '=', vals['email'])], limit=1)

        if partner:
            # Update existing partner
            partner.write(vals)
        else:
            # Create new partner
            partner = self.create(vals)

        return partner

    def _get_state_id(self, state_code):
        """Helper to get state_id from code"""
        if not state_code:
            return False
        state = self.env['res.country.state'].search([
            ('code', '=', state_code.upper()),
            ('country_id.code', '=', 'US')
        ], limit=1)
        return state.id if state else False
