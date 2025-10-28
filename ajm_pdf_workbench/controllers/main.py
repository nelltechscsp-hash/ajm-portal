# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request


class AJMPDFWorkbench(http.Controller):
    @http.route('/my/sales/clients/<int:client_id>/pdf', type='http', auth='user', website=True)
    def pdf_redirect(self, client_id, **kw):
        """
        Redirect antigua ruta /pdf a la nueva /cartas
        """
        return request.redirect(f'/my/sales/clients/{client_id}/cartas')

    @http.route('/my/sales/clients/<int:client_id>/cartas', type='http', auth='user', website=True)
    def cartas_menu(self, client_id, **kw):
        """
        Página del menú de cartas y documentos (sin contenido, solo lista).
        """
        Partner = request.env['res.partner'].sudo()
        client = Partner.browse(client_id)

        cartas = [
            {'id': 'carta1', 'name': 'Carta 1: Cotización y DownPayment'},
            {'id': 'carta2', 'name': 'Carta 2: Endoso de Póliza'},
            {'id': 'carta3', 'name': 'Carta 3: Renuncia a Physical Damage'},
            {'id': 'carta4', 'name': 'Carta 4: Autorización de Commodities'},
            {'id': 'carta5', 'name': 'Carta 5: Lista de Choferes Asegurados'},
            {'id': 'carta6', 'name': 'Carta 6: Pagaré (Promissory Note)'},
            {'id': 'carta7', 'name': 'Carta 7: Avisos y Responsabilidades'},
            {'id': 'carta8', 'name': 'Carta 8: Firmas Finales'},
        ]
        docs = [
            {'id': 'info_sheet', 'name': 'Information Sheet'},
            {'id': 'new_venture', 'name': 'NEW VENTURE QUESTIONNAIRE'},
            {'id': 'qeo_trucking', 'name': 'QEO Trucking Supplemental'},
            {'id': 'quit_quote', 'name': 'Quit Quote v2025'},
        ]

        return request.render('ajm_pdf_workbench.cartas_menu_page', {
            'client': client,
            'cartas': cartas,
            'docs': docs,
        })

    @http.route('/my/sales/clients/<int:client_id>/cartas/<string:doc_type>', type='http', auth='user', website=True)
    def carta_view(self, client_id, doc_type, **kw):
        """
        Vista de una carta individual (sin menú lateral, solo la carta).
        """
        Partner = request.env['res.partner'].sudo()
        client = Partner.browse(client_id)
        Application = request.env['ajm.service.application'].sudo()
        interview = Application.search([('partner_id', '=', client_id)], order='create_date desc', limit=1)

        # Preparse interview JSON so QWeb doesn't need json.loads (safer and faster)
        drivers_data = []
        commodities_data = []
        vehicles_data = []
        coverages_data = []
        coverages_text = ''
        if interview:
            try:
                if interview.drivers_json:
                    drivers_data = json.loads(interview.drivers_json) or []
            except Exception:
                drivers_data = []
            try:
                if interview.commodities_json:
                    commodities_data = json.loads(interview.commodities_json) or []
            except Exception:
                commodities_data = []
            try:
                if interview.vehicles_json:
                    vehicles_data = json.loads(interview.vehicles_json) or []
            except Exception:
                vehicles_data = []
            try:
                if interview.coverages_json:
                    coverages_data = json.loads(interview.coverages_json) or []
                    # Build a compact text for the textarea
                    parts = []
                    for c in coverages_data:
                        ctype = c.get('type', '')
                        limit = c.get('limit', '')
                        deductible = c.get('deductible', '')
                        if any([ctype, limit, deductible]):
                            parts.append(f"{ctype} Limit {limit} deductible {deductible}")
                    coverages_text = "\n".join(parts)
            except Exception:
                coverages_data = []

        # 🔑 Construimos el nombre completo del template
        tpl_name = f"ajm_pdf_workbench.{doc_type}_template"

        return request.render('ajm_pdf_workbench.carta_view_page', {
            'client': client,
            'interview': interview,
            'drivers_data': drivers_data,
            'commodities_data': commodities_data,
            'vehicles_data': vehicles_data,
            'coverages_data': coverages_data,
            'coverages_text': coverages_text,
            'doc_type': doc_type,
            'tpl_name': tpl_name,   # <-- pasamos el nombre completo
            'company': request.env.company,
        })
