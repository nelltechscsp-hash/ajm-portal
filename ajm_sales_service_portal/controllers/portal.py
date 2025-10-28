import base64
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AJMSalesServicePortal(http.Controller):

    def _sales_group(self):
        return 'ajm_employee_portal.group_sales_portal_user'

    @http.route('/my/sales/forms', type='http', auth='user', website=True, groups='ajm_employee_portal.group_sales_portal_user')
    def sales_forms_home(self, **kw):
        menu = [
            {'key': 'new_company', 'label': 'Nueva compañía', 'url': '/my/sales/forms/new-company'},
            {'key': 'renewal', 'label': 'Renovación', 'url': '/my/sales/forms/renewal'},
            {'key': 'contract_insurance', 'label': 'Contratación de seguro', 'url': '/my/sales/forms/contract'},
            {'key': 'endorsement', 'label': 'Endorsement', 'url': '/my/sales/forms/endorsement'},
            {'key': 'permits', 'label': 'Permisos', 'url': '/my/sales/forms/permits'},
            {'key': 'audits', 'label': 'Auditorías', 'url': '/my/sales/forms/audits'},
        ]
        return request.render('ajm_sales_service_portal.portal_sales_forms_home', {'menu': menu})

    @http.route('/my/sales/forms/contract', type='http', auth='user', website=True, methods=['GET'], groups='ajm_employee_portal.group_sales_portal_user')
    def form_contract_get(self, **kw):
        return request.render('ajm_sales_service_portal.portal_form_contract', {})

    @http.route('/my/sales/forms/contract/submit', type='http', auth='user', website=True, methods=['POST'], csrf=True, groups='ajm_employee_portal.group_sales_portal_user')
    def form_contract_submit(self, **post):
        U = request.env.user.sudo()
        vals = {
            'service_type': 'contract_insurance',
            'agent': (post.get('agent') or '').strip(),
            'client_since': post.get('client_since') or False,
            'client_name': (post.get('client_name') or '').strip(),
                'effective_date': post.get('effective_date') or False,
            'entity_number': (post.get('entity_number') or '').strip(),
            'name_insured': (post.get('name_insured') or '').strip(),
            'dba': (post.get('dba') or '').strip(),
            'owner': (post.get('owner') or '').strip(),
            'entity_type': post.get('entity_type') or False,
            'entity_type_other': (post.get('entity_type_other') or '').strip(),
            'carrier_type': post.get('carrier_type') or False,
            'carrier_type_other': (post.get('carrier_type_other') or '').strip(),
            'operation_scope': post.get('operation_scope') or False,
            'mailing_street': (post.get('mailing_street') or '').strip(),
            'mailing_city': (post.get('mailing_city') or '').strip(),
            'mailing_state': (post.get('mailing_state') or '').strip(),
            'mailing_zip': (post.get('mailing_zip') or '').strip(),
            'physical_street': (post.get('physical_street') or '').strip(),
            'physical_city': (post.get('physical_city') or '').strip(),
            'physical_state': (post.get('physical_state') or '').strip(),
            'physical_zip': (post.get('physical_zip') or '').strip(),
            'garaging_street': (post.get('garaging_street') or '').strip(),
            'garaging_city': (post.get('garaging_city') or '').strip(),
            'garaging_state': (post.get('garaging_state') or '').strip(),
            'garaging_zip': (post.get('garaging_zip') or '').strip(),
            'phone': (post.get('phone') or '').strip(),
            'email': (post.get('email') or '').strip(),
            'years_in_business': int(post.get('years_in_business') or 0),
            'trailer_type': post.get('trailer_type') or False,
            'trailer_type_other': (post.get('trailer_type_other') or '').strip(),
            'ein': (post.get('ein') or '').strip(),
            'coverages_json': post.get('coverages_json') or '',
            'commodities_json': post.get('commodities_json') or '',
            'drivers_json': post.get('drivers_json') or '',
            'filings_json': post.get('filings_json') or '',
            'vehicles_json': post.get('vehicles_json') or '',
            'history_json': post.get('history_json') or '',
            'notes': post.get('notes') or '',
            'user_id': U.id,
        }
        app = request.env['ajm.service.application'].sudo().create(vals)
        # handle attachments
        files = []
        try:
            files = request.httprequest.files.getlist('attachments')
        except Exception:
            files = []
        for f in files:
            if not getattr(f, 'filename', None):
                continue
            content = f.read() or b''
            if not content:
                continue
            att = request.env['ir.attachment'].sudo().create({
                'name': f.filename,
                'datas': base64.b64encode(content).decode(),
                'type': 'binary',
                'res_model': 'ajm.service.application',
                'res_id': app.id,
            })
            app.attachment_ids = [(4, att.id)]
        request.session['portal_status_message'] = 'Solicitud enviada. Gracias.'
        return request.redirect('/my/sales/forms/contract/success')

    @http.route('/my/sales/forms/contract/success', type='http', auth='user', website=True, groups='ajm_employee_portal.group_sales_portal_user')
    def form_contract_success(self, **kw):
        return request.render('ajm_sales_service_portal.portal_form_success', {})

    @http.route('/my/sales/forms/lookup', type='jsonrpc', auth='user', methods=['POST'], csrf=False, groups='ajm_employee_portal.group_sales_portal_user')
    def company_lookup(self, usdot=None, txdmv=None, mc=None, **kw):
        """
        AJAX endpoint to lookup company data from external sources.
        Returns JSON with company information.
        """
        lookup_model = request.env['ajm.company.lookup'].sudo()
        result = {}

        # Try FMCSA SAFER first if USDOT provided
        if usdot:
            _logger.info('AJM Lookup: FMCSA request for USDOT=%s', usdot)
            fmcsa_data = lookup_model.lookup_fmcsa_safer(usdot)
            result.update(fmcsa_data)

        # Try Texas DMV only if TxDMV provided (avoid false positives when only USDOT is present)
        if txdmv:
            _logger.info('AJM Lookup: TxDMV request for USDOT=%s TXDMV=%s', usdot, txdmv)
            txdmv_data = lookup_model.lookup_txdmv(usdot=usdot, txdmv=txdmv)
            # Merge but don't overwrite existing data from FMCSA
            for key, value in txdmv_data.items():
                if key not in result or not result[key]:
                    result[key] = value

        _logger.info('AJM Lookup: result keys=%s', list(result.keys()))
        return result

    @http.route('/my/sales/clients', type='http', auth='user', website=True)
    def clients_home(self, client_type=None, search=None, **kw):
        """
        Main clients page with search and recent clients list.
        Accessible to all authenticated users.
        """
        Partner = request.env['res.partner'].sudo()
        domain = [('client_type', 'in', ['transport', 'health'])]

        # Filter by client type if specified
        if client_type in ['transport', 'health']:
            domain.append(('client_type', '=', client_type))

        # Search by USDOT or company name
        if search:
            search_domain = [
                '|', '|',
                ('name', 'ilike', search),
                ('usdot', 'ilike', search),
                ('mc_number', 'ilike', search),
            ]
            domain = ['&'] + domain + search_domain

        # Get recent clients (last 30 days) or search results
        clients = Partner.search(domain, order='create_date desc', limit=50)

        # Count by type
        transport_count = Partner.search_count([('client_type', '=', 'transport')])
        health_count = Partner.search_count([('client_type', '=', 'health')])

        return request.render('ajm_sales_service_portal.portal_clients_home', {
            'clients': clients,
            'client_type': client_type,
            'search_term': search or '',
            'transport_count': transport_count,
            'health_count': health_count,
        })

    @http.route('/my/sales/clients/verify-password', type='json', auth='user', methods=['POST'])
    def verify_password(self, password=None, **kw):
        """Verify user password for delete confirmation."""
        if not password:
            return {'valid': False}

        user = request.env.user
        try:
            # Try to authenticate with current user and provided password
            request.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id=%s",
                [user.id]
            )
            encrypted = request.env.cr.fetchone()[0]
            valid = user._crypt_context().verify(password, encrypted)
            return {'valid': valid}
        except Exception:
            return {'valid': False}

    @http.route('/my/sales/clients/<int:client_id>/delete', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def client_delete(self, client_id, **post):
        """Delete a client and all related interviews from the portal."""
        Partner = request.env['res.partner'].sudo()
        client = Partner.browse(client_id)
        if not client.exists():
            return request.redirect('/my/sales/clients')
        name = client.name
        try:
            # Delete all related interviews first
            Application = request.env['ajm.service.application'].sudo()
            interviews = Application.search([('partner_id', '=', client_id)])
            interviews.unlink()
            # Delete the client
            client.unlink()
            request.session['portal_status_message'] = f'Client {name} and related interviews deleted.'
        except Exception:
            request.session['portal_error_message'] = 'Could not delete client.'
        return request.redirect('/my/sales/clients')


    # -------- Interview portal pages --------
    @http.route('/my/sales/interviews', type='http', auth='user', website=True)
    def interviews_index(self, **kw):
        """Entry point for Interviews.
        - If the current user has at least one interview, redirect to the most recent one.
        - Otherwise, render the Insurance Application creation form so they can start.
        """
        Application = request.env['ajm.service.application'].sudo()
        # Prefer interviews created by the current user
        last = Application.search([('user_id', '=', request.env.user.id)], order='create_date desc', limit=1)
        if last:
            return request.redirect(f'/my/sales/interviews/{last.id}')
        # No interviews yet: show the creation form directly
        return request.render('ajm_sales_service_portal.portal_form_contract', {})
    @http.route('/my/sales/interviews/<int:interview_id>', type='http', auth='user', website=True)
    def interview_detail(self, interview_id, **kw):
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.browse(interview_id)
        if not interview.exists():
            return request.redirect('/my/sales/clients')
        attachments = request.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'ajm.service.application'),
            ('res_id', '=', interview.id)
        ])
        status = request.session.pop('portal_status_message', False)
        error = request.session.pop('portal_error_message', False)
        return request.render('ajm_sales_service_portal.portal_interview_detail', {
            'interview': interview,
            'attachments': attachments,
            'status_message': status,
            'error_message': error,
        })

    @http.route('/my/sales/interviews/<int:interview_id>/delete', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def interview_delete(self, interview_id, **post):
        """Delete an interview from the portal and return to the client detail or list."""
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.browse(interview_id)
        if not interview.exists():
            return request.redirect('/my/sales/clients')
        # Keep target for redirect (client detail if known)
        client_id = interview.partner_id.id or False
        name = interview.name
        try:
            interview.unlink()
            request.session['portal_status_message'] = f'Interview {name} deleted.'
        except Exception:
            request.session['portal_error_message'] = 'Could not delete interview.'
        if client_id:
            return request.redirect(f'/my/sales/clients/{client_id}')
        return request.redirect('/my/sales/clients')

    @http.route('/my/sales/interviews/<int:interview_id>/save', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def interview_save(self, interview_id, **post):
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.browse(interview_id)
        if not interview.exists():
            return request.redirect('/my/sales/clients')
        vals = {}
        # Simple field updates (text/selection/integer)
        simple_fields = [
            'notes', 'name_insured', 'phone', 'email', 'dba', 'owner', 'agent', 'client_name', 'entity_number',
            'entity_type', 'entity_type_other', 'operation_scope', 'trailer_type',
            'carrier_type', 'carrier_type_other',
            'mailing_street', 'mailing_city', 'mailing_state', 'mailing_zip',
            'physical_street', 'physical_city', 'physical_state', 'physical_zip',
            'garaging_street', 'garaging_city', 'garaging_state', 'garaging_zip',
            'years_in_business', 'ein'
        ]
        for key in simple_fields:
            if key in post:
                vals[key] = post.get(key)
        if 'effective_date' in post:
            vals['effective_date'] = post.get('effective_date') or False
        # JSON fields with validation
        json_fields = ['coverages_json', 'commodities_json', 'filings_json', 'drivers_json', 'vehicles_json', 'history_json']
        for jf in json_fields:
            if jf in post:
                content = post.get(jf) or ''
                if content.strip():
                    try:
                        json.loads(content)
                        vals[jf] = content
                    except Exception:
                        # accumulate errors
                        prev = request.session.get('portal_error_message') or ''
                        request.session['portal_error_message'] = (prev + ' Invalid JSON in %s.' % jf).strip()
                else:
                    vals[jf] = ''
        if vals:
            interview.write(vals)
        request.session['portal_status_message'] = 'Interview updated successfully.'
        active_tab = (post.get('active_tab') or '').strip()
        redirect_url = f'/my/sales/interviews/{interview_id}'
        if active_tab:
            redirect_url += f'?tab={active_tab}'
        return request.redirect(redirect_url)

    @http.route('/my/sales/interviews/<int:interview_id>/upload', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def interview_upload(self, interview_id, **post):
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.browse(interview_id)
        if not interview.exists():
            return request.redirect('/my/sales/clients')
        files = []
        try:
            files = request.httprequest.files.getlist('files')
        except Exception:
            files = []
        for f in files:
            if not getattr(f, 'filename', None):
                continue
            content = f.read() or b''
            if not content:
                continue
            att = request.env['ir.attachment'].sudo().create({
                'name': f.filename,
                'datas': base64.b64encode(content).decode(),
                'type': 'binary',
                'res_model': 'ajm.service.application',
                'res_id': interview.id,
            })
            interview.attachment_ids = [(4, att.id)]
        request.session['portal_status_message'] = 'Files uploaded successfully.'
        active_tab = (post.get('active_tab') or '').strip()
        redirect_url = f'/my/sales/interviews/{interview_id}'
        if active_tab:
            redirect_url += f'?tab={active_tab}'
        return request.redirect(redirect_url)

    @http.route('/my/sales/interviews/<int:interview_id>/attachment/<int:att_id>/delete', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def interview_delete_attachment(self, interview_id, att_id, **post):
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.browse(interview_id)
        if not interview.exists():
            return request.redirect('/my/sales/clients')
        att = request.env['ir.attachment'].sudo().browse(att_id)
        if att.exists() and att.res_model == 'ajm.service.application' and att.res_id == interview.id:
            att.unlink()
            request.session['portal_status_message'] = 'Attachment removed.'
        active_tab = (post.get('active_tab') or '').strip()
        redirect_url = f'/my/sales/interviews/{interview_id}'
        if active_tab:
            redirect_url += f'?tab={active_tab}'
        return request.redirect(redirect_url)

    @http.route('/my/sales/interviews/email/send', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def interview_send_email(self, interview_id=None, email_to=None, subject=None, body=None, attachment_ids=None, **kw):
        if not interview_id or not email_to:
            return {'ok': False, 'error': 'missing_parameters'}
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.browse(int(interview_id))
        if not interview.exists():
            return {'ok': False, 'error': 'interview_not_found'}
        # Build mail values
        vals = {
            'subject': subject or f'Documents for Interview {interview.name}',
            'email_to': email_to,
            'body_html': body or '',
            'auto_delete': True,
        }
        mail = request.env['mail.mail'].sudo().create(vals)
        # Attach selected attachments
        ids = []
        if attachment_ids:
            # attachment_ids may be list of strings
            ids = [int(a) for a in attachment_ids if str(a).isdigit()]
        if ids:
            atts = request.env['ir.attachment'].sudo().browse(ids)
            mail.write({'attachment_ids': [(6, 0, atts.ids)]})
        mail.sudo().send()
        return {'ok': True}
