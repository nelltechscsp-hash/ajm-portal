import base64
import email
import imaplib
import logging
import socket
from email.header import decode_header
from email.utils import getaddresses
from html import escape as html_escape

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


def _decode_header_value(raw):
    if not raw:
        return ''
    parts = decode_header(raw)
    out = []
    for val, enc in parts:
        try:
            if isinstance(val, bytes):
                out.append(val.decode(enc or 'utf-8', errors='replace'))
            else:
                out.append(val)
        except Exception:
            out.append(str(val))
    return ''.join(out)


def _imap_connect(user_email, app_password, timeout=10):
    socket.setdefaulttimeout(timeout)
    m = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    m.login(user_email, app_password)
    return m


def _imap_select_mailbox(m, mailbox):
    # Try direct first
    candidates = [mailbox]
    ml = mailbox.lower()
    if ml == 'sent':
        # Common Gmail special-use or localized names
        candidates = [
            '[Gmail]/Sent Mail',
            'Sent',
            '[Gmail]/Sent',
            '[Gmail]/Enviados',  # es
            'Enviados',          # es
            '[Gmail]/Envoyés',   # fr
            'Envoyés',
            '[Gmail]/Posta inviata', 'Posta inviata',  # it
        ]
        # Try to discover via LIST for \Sent flag
        try:
            typ, data = m.list()
            if typ == 'OK' and data:
                for line in data:
                    try:
                        # IMAP LIST uses modified UTF-7; try utf-8 then fallback
                        try:
                            s = line.decode('utf-8')
                        except Exception:
                            s = line.decode(errors='ignore')
                    except Exception:
                        s = str(line)
                    if '\\Sent' in s or 'HasNoChildren' in s:
                        # Extract the last quoted string as mailbox name
                        last = s.rfind('"')
                        first = s.rfind('"', 0, last)
                        name = None
                        if first != -1 and last != -1 and last > first:
                            name = s[first+1:last]
                        if not name:
                            # Fallback: take last token
                            name = s.split(' ')[-1].strip('"')
                        if name and name not in candidates:
                            candidates.insert(0, name)
        except Exception:
            pass
    for box in candidates:
        typ, _ = m.select(box)
        if typ == 'OK':
            return True
    return False


def _imap_list_messages(user_email, app_password, mailbox='INBOX', limit=25, timeout=10):
    socket.setdefaulttimeout(timeout)
    m = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    try:
        m.login(user_email, app_password)
        if not _imap_select_mailbox(m, mailbox):
            return {'messages': [], 'unseen_count': 0}
        typ, data = m.search(None, 'ALL')
        ids = data[0].split()
        ids = ids[-limit:]
        messages = []
        unseen_count = 0
        # Fetch flags to count UNSEEN quickly
        if ids:
            typ, data = m.search(None, 'UNSEEN')
            unseen = set(data[0].split()) if data and data[0] else set()
            unseen_count = len(unseen)

        for msg_id in reversed(ids):  # newest first
            typ, msg_data = m.fetch(msg_id, '(RFC822.HEADER)')
            if typ != 'OK' or not msg_data or not isinstance(msg_data[0], tuple) or len(msg_data[0]) < 2:
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            from_ = _decode_header_value(msg.get('From'))
            subject = _decode_header_value(msg.get('Subject'))
            date = msg.get('Date')
            messages.append({
                'imap_id': msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id),
                'from': from_,
                'subject': subject,
                'date': date,
                'is_unseen': (msg_id in unseen),
            })
        return {
            'messages': messages,
            'unseen_count': unseen_count,
        }
    finally:
        try:
            m.logout()
        except Exception:
            pass


def _extract_best_body(msg):
    # prefer text/html; fallback to text/plain converted to minimal HTML
    html_part = None
    text_part = None
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        ctype = part.get_content_type() or ''
        disp = (part.get('Content-Disposition') or '').lower()
        if 'attachment' in disp:
            continue
        if ctype == 'text/html' and html_part is None:
            html_part = part
        elif ctype == 'text/plain' and text_part is None:
            text_part = part
    if html_part is not None:
        try:
            payload = html_part.get_payload(decode=True) or b''
            charset = html_part.get_content_charset() or 'utf-8'
            return payload.decode(charset, errors='replace')
        except Exception:
            pass
    if text_part is not None:
        try:
            payload = text_part.get_payload(decode=True) or b''
            charset = text_part.get_content_charset() or 'utf-8'
            text = payload.decode(charset, errors='replace')
            return '<pre style="white-space:pre-wrap">%s</pre>' % html_escape(text)
        except Exception:
            pass
    return '<div class="text-muted">(no body)</div>'


def _extract_attachments(msg):
    attachments = []
    def walk_parts(m, prefix=""):
        idx = 0
        for part in m.get_payload() if m.is_multipart() else []:
            idx += 1
            part_id = f"{prefix}{idx}" if prefix else str(idx)
            disp = (part.get('Content-Disposition') or '').lower()
            filename = part.get_filename()
            if filename:
                filename = _decode_header_value(filename)
            if ('attachment' in disp or filename) and part.get_content_maintype() != 'multipart':
                attachments.append({
                    'part_id': part_id,
                    'filename': filename or 'attachment',
                    'content_type': part.get_content_type(),
                })
            # recurse
            if part.is_multipart():
                walk_parts(part, prefix=part_id + ".")
    walk_parts(msg)
    return attachments


class AJMMailAppController(http.Controller):

    @http.route('/my/mail', type='http', auth='user', website=True)
    def portal_mail_app(self, **kw):
        user = request.env.user
        gmail_address = (user.gmail_address or user.login or '').strip()
        app_password = (user.gmail_app_password or '').strip()
        box = (kw.get('box') or 'inbox').lower()
        # Load user templates
        Tpl = request.env['ajm.mail.template'].sudo()
        templates = Tpl.search([('user_id', '=', user.id)], order='name asc')
        values = {
            'page_name': 'ajm_mail_app',
            'gmail_ok': bool(gmail_address and app_password),
            'gmail_address': gmail_address,
            'box': box,
            'unseen_count': 0,
            'messages': [],
            'error': '',
            'prefill_to': kw.get('to') or '',
            'prefill_cc': kw.get('cc') or '',
            'prefill_bcc': kw.get('bcc') or '',
            'prefill_subject': kw.get('subject') or '',
            'templates': [{'id': t.id, 'name': t.name, 'subject': t.subject or '', 'body_html': t.body_html or ''} for t in templates],
        }
        if not values['gmail_ok']:
            values['error'] = 'Configure your Gmail App Password to use the mailbox.'
            return request.render('ajm_user_gmail.portal_mail_app', values)

        try:
            mb = 'INBOX' if box == 'inbox' else 'sent'
            data = _imap_list_messages(gmail_address, app_password, mailbox=mb, limit=25)
            values.update(data)
        except imaplib.IMAP4.error:
            values['error'] = 'Could not log in to Gmail. Check your App Password.'
        except (socket.timeout, socket.error):
            values['error'] = 'Connection timeout while connecting to Gmail.'
        except Exception as e:
            _logger.exception('Error listing IMAP messages: %s', e)
            values['error'] = 'Unknown error reading messages.'

        return request.render('ajm_user_gmail.portal_mail_app', values)

    @http.route('/my/mail/template/save', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_mail_template_save(self, **post):
        user = request.env.user.sudo()
        name = (post.get('tpl_name') or '').strip()
        subject = (post.get('subject') or '').strip()
        body = (post.get('body') or '').strip()
        if not name:
            request.session['portal_status_message'] = 'Template name is required.'
            return request.redirect('/my/mail')
        vals = {
            'name': name,
            'subject': subject,
            'body_html': '<div>%s</div>' % (html_escape(body).replace('\n', '<br/>')) if body else '',
            'user_id': user.id,
        }
        try:
            request.env['ajm.mail.template'].sudo().create(vals)
            request.session['portal_status_message'] = 'Template saved successfully.'
        except Exception:
            request.session['portal_status_message'] = 'Could not save template.'
        return request.redirect('/my/mail')

    @http.route('/my/mail/template/delete', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_mail_template_delete(self, **post):
        user = request.env.user.sudo()
        tpl_id = post.get('tpl_id')
        if not tpl_id:
            request.session['portal_status_message'] = 'Invalid template ID.'
            return request.redirect('/my/mail')
        try:
            tpl = request.env['ajm.mail.template'].sudo().browse(int(tpl_id))
            if tpl.exists() and tpl.user_id.id == user.id:
                tpl.unlink()
                request.session['portal_status_message'] = 'Template deleted successfully.'
            else:
                request.session['portal_status_message'] = 'Template not found or no permission.'
        except Exception:
            request.session['portal_status_message'] = 'Could not delete template.'
        return request.redirect('/my/mail')

    @http.route('/my/mail/message', type='http', auth='user', website=True)
    def portal_mail_message(self, **kw):
        user = request.env.user
        gmail_address = (user.gmail_address or user.login or '').strip()
        app_password = (user.gmail_app_password or '').strip()
        box = (kw.get('box') or 'inbox').lower()
        msg_id = kw.get('id')
        values = {
            'page_name': 'ajm_mail_app',
            'gmail_ok': bool(gmail_address and app_password),
            'gmail_address': gmail_address,
            'box': box,
            'error': '',
            'message': None,
            'body_html': '',
            'attachments': [],
        }
        if not values['gmail_ok'] or not msg_id:
            values['error'] = 'Missing credentials or message ID.'
            return request.render('ajm_user_gmail.portal_mail_app', values)
        m = None
        try:
            m = _imap_connect(gmail_address, app_password)
            if not _imap_select_mailbox(m, 'INBOX' if box == 'inbox' else 'sent'):
                values['error'] = 'Could not open mailbox.'
                return request.render('ajm_user_gmail.portal_mail_app', values)
            typ, msg_data = m.fetch(msg_id, '(RFC822)')
            if typ != 'OK' or not msg_data or not isinstance(msg_data[0], tuple) or len(msg_data[0]) < 2:
                values['error'] = 'Could not retrieve message.'
                return request.render('ajm_user_gmail.portal_mail_app', values)
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            from_ = _decode_header_value(msg.get('From'))
            to_ = _decode_header_value(msg.get('To'))
            cc_ = _decode_header_value(msg.get('Cc'))
            subject = _decode_header_value(msg.get('Subject'))
            date = msg.get('Date')
            body_html = _extract_best_body(msg)
            atts = _extract_attachments(msg)
            values.update({
                'message': {
                    'imap_id': msg_id,
                    'from': from_,
                    'to': to_,
                    'cc': cc_,
                    'subject': subject,
                    'date': date,
                },
                'body_html': body_html,
                'attachments': atts,
            })
            # Build reply/reply-all/forward links
            # Parse addresses
            all_to_cc = getaddresses([to_ or '', cc_ or ''])
            from_list = getaddresses([from_ or ''])
            from_addr = from_list[0][1] if from_list else ''
            me = (user.gmail_address or user.login or '').lower()
            reply_to = from_addr
            reply_all = []
            for _, addr in all_to_cc + [('', from_addr)]:
                if addr and addr.lower() != me and addr not in reply_all:
                    reply_all.append(addr)
            fwd_subject = subject if (subject or '').lower().startswith('fwd:') else f"Fwd: {subject or ''}"
            values.update({
                'reply_to': reply_to,
                'reply_all': ', '.join(reply_all),
                'forward_subject': fwd_subject,
            })
        except Exception as e:
            _logger.exception('Error fetching message: %s', e)
            values['error'] = 'Error obteniendo el mensaje.'
        finally:
            try:
                if m:
                    m.logout()
            except Exception:
                pass
        return request.render('ajm_user_gmail.portal_mail_app', values)

    @http.route('/my/mail/attachment', type='http', auth='user', methods=['GET'], website=True)
    def portal_mail_attachment(self, **kw):
        user = request.env.user
        gmail_address = (user.gmail_address or user.login or '').strip()
        app_password = (user.gmail_app_password or '').strip()
        box = (kw.get('box') or 'inbox').lower()
        msg_id = kw.get('id')
        part_id = kw.get('part')
        filename = kw.get('filename') or 'attachment'
        if not (gmail_address and app_password and msg_id and part_id):
            return request.not_found()
        m = None
        try:
            m = _imap_connect(gmail_address, app_password)
            if not _imap_select_mailbox(m, 'INBOX' if box == 'inbox' else 'sent'):
                return request.not_found()
            # Gmail supports BODY[<part>]
            typ, msg_data = m.fetch(msg_id, f'(BODY[{part_id}])')
            if typ != 'OK' or not msg_data or not isinstance(msg_data[0], tuple) or len(msg_data[0]) < 2:
                return request.not_found()
            content = msg_data[0][1] or b''
            headers = [
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', f'attachment; filename="{filename}"'),
            ]
            return request.make_response(content, headers)
        except Exception:
            return request.not_found()
        finally:
            try:
                if m:
                    m.logout()
            except Exception:
                pass
    @http.route('/my/mail/send', type='http', auth='user', methods=['POST'], website=True, csrf=True)
    def portal_mail_send(self, **post):
        user = request.env.user.sudo()
        httpreq = request.httprequest
        email_to_raw = (post.get('email_to') or '').strip()
        email_cc_raw = (post.get('email_cc') or '').strip()
        email_bcc_raw = (post.get('email_bcc') or '').strip()
        subject = (post.get('subject') or '').strip()
        body = (post.get('body') or '').strip()

        def _parse_addresses(raw):
            if not raw:
                return []
            addrs = [a for _, a in getaddresses([raw]) if a]
            return list(dict.fromkeys(addrs))  # dedupe preserve order

        email_to = _parse_addresses(email_to_raw)
        email_cc = _parse_addresses(email_cc_raw)
        email_bcc = _parse_addresses(email_bcc_raw)

        if not email_to or not subject:
            request.session['portal_status_message'] = 'Recipient and subject are required.'
            return request.redirect('/my/mail')

        body_html = '<div>%s</div>' % (html_escape(body).replace('\n', '<br/>'))
        vals = {
            'subject': subject,
            'email_from': (user.gmail_address or user.login or ''),
            'email_to': ', '.join(email_to),
            'email_cc': ', '.join(email_cc) if email_cc else False,
            'email_bcc': ', '.join(email_bcc) if email_bcc else False,
            'body_html': body_html,
            'author_id': user.partner_id.id if user.partner_id else False,
        }
        try:
            mail = request.env['mail.mail'].sudo().create(vals)
            # attachments
            files = []
            try:
                files = httpreq.files.getlist('attachments')
            except Exception:
                pass
            for f in files or []:
                if not getattr(f, 'filename', None):
                    continue
                content = f.read()
                if not content:
                    continue
                att = request.env['ir.attachment'].sudo().create({
                    'name': f.filename,
                    'datas': base64.b64encode(content).decode(),
                    'type': 'binary',
                    'res_model': 'mail.mail',
                    'res_id': mail.id,
                })
                # link by m2m too
                mail.attachment_ids = [(4, att.id)]
            request.session['portal_status_message'] = 'Email queued for sending.'
        except Exception as e:
            _logger.exception('Error creating mail: %s', e)
            request.session['portal_status_message'] = 'Could not queue email.'
        return request.redirect('/my/mail')

    @http.route('/my/mail/suggest', type='json', auth='user')
    def portal_mail_suggest(self, q=None, limit=10):
        user = request.env.user
        q = (q or '').strip()
        Partner = request.env['res.partner'].sudo()
        # Suggest contacts under user's commercial partner
        domain = [('email', '!=', False)]
        if user.partner_id and user.partner_id.commercial_partner_id:
            domain += ['|', ('parent_id', '=', user.partner_id.commercial_partner_id.id),
                       ('commercial_partner_id', '=', user.partner_id.commercial_partner_id.id)]
        if q:
            domain += ['|', ('name', 'ilike', q), ('email', 'ilike', q)]
        recs = Partner.search(domain, limit=limit)
        return [{'name': p.name, 'email': p.email, 'label': f"{p.name} <{p.email}>"} for p in recs]
