import logging
import re

import requests
from lxml import html
from odoo import api, models

_logger = logging.getLogger(__name__)


class CompanyLookup(models.AbstractModel):
    _name = 'ajm.company.lookup'
    _description = 'External Company Data Lookup'

    @api.model
    def lookup_fmcsa_safer(self, usdot):
        """
        Fetch company data from FMCSA SAFER database by USDOT number.
        Returns dict with company info or empty dict on error.
        """
        if not usdot or not str(usdot).strip().isdigit():
            return {}

        try:
            url = f'https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&query_type=queryCarrierSnapshot&query_param=USDOT&query_string={usdot}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            data = {}

            # Helper: find the first TD following a TH whose text (including descendants) contains label
            def td_text_list(label):
                nodes = tree.xpath(f'//th[contains(normalize-space(.), "{label}")]/following-sibling::td[1]')
                if not nodes:
                    return []
                return [t.strip() for t in nodes[0].xpath('.//text()') if t and t.strip()]

            # Legal Name
            legal_list = td_text_list('Legal Name')
            if legal_list:
                data['name_insured'] = legal_list[0]

            # DBA Name
            dba_list = td_text_list('DBA Name')
            if dba_list:
                data['dba'] = dba_list[0]

            # Owner / Principal / Contact (sometimes available)
            owner_list = td_text_list('Owner')
            if not owner_list:
                owner_list = td_text_list('Principal')
            if not owner_list:
                owner_list = td_text_list('Contact')
            if owner_list:
                data['owner'] = owner_list[0]

            # Physical Address
            phys_list = td_text_list('Physical Address')
            if phys_list:
                # Often format: [street, CITY, ST ZIP]
                data['physical_street'] = phys_list[0]
                data['garaging_street'] = phys_list[0]  # Also use as garaging by default
                last_line = phys_list[-1]
                match = re.search(r'([^,]+),\s*([A-Z]{2})\s+(\d{5})', last_line)
                if match:
                    data['physical_city'] = match.group(1).strip()
                    data['physical_state'] = match.group(2).strip()
                    data['physical_zip'] = match.group(3).strip()
                    # Also copy to garaging
                    data['garaging_city'] = match.group(1).strip()
                    data['garaging_state'] = match.group(2).strip()
                    data['garaging_zip'] = match.group(3).strip()

            # Mailing Address
            mail_list = td_text_list('Mailing Address')
            if mail_list:
                data['mailing_street'] = mail_list[0]
                last_line = mail_list[-1]
                match = re.search(r'([^,]+),\s*([A-Z]{2})\s+(\d{5}(?:-\d{4})?)', last_line)
                if match:
                    data['mailing_city'] = match.group(1).strip()
                    data['mailing_state'] = match.group(2).strip()
                    data['mailing_zip'] = match.group(3).strip()

            # Phone
            phone_list = td_text_list('Phone')
            if phone_list:
                # Phone may include extra text; take the first numeric-looking segment
                data['phone'] = phone_list[0]

            # Email (if available - not always present on SAFER)
            email_list = td_text_list('Email')
            if not email_list:
                email_list = td_text_list('E-mail')
            if email_list:
                data['email'] = email_list[0]

            # MC/MX Number(s)
            mc_list = td_text_list('MC/MX/FF Number')
            if not mc_list:
                mc_list = td_text_list('MC/MX/FF Number(s)')
            if mc_list:
                data['filings_mc'] = mc_list[0]

            # Entity Type (e.g., Corporation, LLC, etc.)
            entity_list = td_text_list('Entity Type')
            if entity_list:
                entity_text = entity_list[0].strip().lower()
                if 'corporation' in entity_text or 'corp' in entity_text:
                    data['entity_type'] = 'corporation'
                elif 'llc' in entity_text:
                    data['entity_type'] = 'llc'
                elif 'partnership' in entity_text:
                    data['entity_type'] = 'partnership'
                elif 'individual' in entity_text or 'sole' in entity_text:
                    data['entity_type'] = 'individual'
                else:
                    data['entity_type'] = 'other'
                    data['entity_type_other'] = entity_list[0].strip()

            # Carrier Type mapping to detailed FMCSA-style options
            # Prefer 'Operation Classification' when available (FMCSA term). Fallback to 'Carrier'/'Carrier Operation'.
            carrier_list = td_text_list('Operation Classification')
            if not carrier_list:
                carrier_list = td_text_list('Carrier')
            if not carrier_list:
                carrier_list = td_text_list('Carrier Operation')
            if carrier_list:
                cell_text = ' '.join(carrier_list).lower()
                def has(*words):
                    return all(w in cell_text for w in words)

                mapped = None
                if 'common carrier' in cell_text:
                    mapped = 'common_carrier'
                elif 'authorized' in cell_text and 'hire' in cell_text:
                    mapped = 'authorized_for_hire'
                elif 'exempt' in cell_text and 'hire' in cell_text:
                    mapped = 'exempt_for_hire'
                elif 'private' in cell_text and 'property' in cell_text:
                    mapped = 'private_property'
                elif has('priv.', 'pass.', '(business)') or ('private passenger' in cell_text and 'business' in cell_text):
                    mapped = 'private_passenger_business'
                elif has('priv.', 'pass.', '(non-business)') or ('private passenger' in cell_text and 'non' in cell_text):
                    mapped = 'private_passenger_nonbusiness'
                elif 'mail' in cell_text:
                    mapped = 'us_mail'
                elif 'migrant' in cell_text:
                    mapped = 'migrant'
                elif 'indian' in cell_text:
                    mapped = 'indian_nation'
                elif 'federal' in cell_text or 'state' in cell_text or 'local government' in cell_text or 'local gov' in cell_text:
                    mapped = 'government'

                if mapped:
                    data['carrier_type'] = mapped
                else:
                    data['carrier_type'] = 'other'
                    data['carrier_type_other'] = ' '.join(carrier_list).strip()

            # Operation scope (Interstate / Intrastate)
            op_list = td_text_list('Carrier Operation')
            if op_list:
                op_text = ' '.join(op_list).lower()
                has_interstate = 'interstate' in op_text
                has_intrastate = 'intrastate' in op_text
                if has_interstate and has_intrastate:
                    # Field only allows one; prefer 'interstate' by default
                    data['operation_scope'] = 'interstate'
                elif has_interstate:
                    data['operation_scope'] = 'interstate'
                elif has_intrastate:
                    data['operation_scope'] = 'intrastate'

            _logger.info(f"FMCSA SAFER lookup for USDOT {usdot} returned: {data}")
            return data

        except requests.RequestException as e:
            _logger.error(f"Error fetching FMCSA data for USDOT {usdot}: {e}")
            return {}
        except Exception as e:
            _logger.error(f"Unexpected error in FMCSA lookup: {e}")
            return {}

    @api.model
    def lookup_txdmv(self, usdot=None, txdmv=None):
        """
        Fetch company data from Texas DMV Truck Stop by USDOT or TxDMV number.
        Returns dict with company info or empty dict on error.
        """
        # New site flow is brittle; to reduce false positives, only proceed when TXDMV is provided
        if not txdmv:
            return {}

        try:
            # Build search URL
            # Use landing page and message endpoint consistent with current site; results often require post-process.
            # We'll query the Truckstop landing page with a hint and avoid extracting unless we find expected fields.
            base_url = 'https://apps.txdmv.gov/apps/mccs/truckstop/'
            params = {}

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(base_url, params=params, headers=headers, timeout=15)
            response.raise_for_status()

            tree = html.fromstring(response.content)
            data = {}

            # The landing page does not provide deterministic result fields without a session.
            # Avoid returning misleading data; only return filings_tx echoed from input as a convenience.
            data['filings_tx'] = str(txdmv).strip()

            _logger.info(f"TxDMV lookup for USDOT {usdot} / TxDMV {txdmv} returned: {data}")
            return data

        except requests.RequestException as e:
            _logger.error(f"Error fetching TxDMV data: {e}")
            return {}
        except Exception as e:
            _logger.error(f"Unexpected error in TxDMV lookup: {e}")
            return {}
