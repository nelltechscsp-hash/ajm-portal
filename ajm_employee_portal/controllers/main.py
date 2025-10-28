import logging
from datetime import datetime, timedelta

import pytz
from odoo import fields, http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request
from werkzeug.utils import redirect as werkzeug_redirect
from werkzeug.wrappers import Response

_logger = logging.getLogger(__name__)


# Simple department -> route map. Extend here as new department portals are added.
DEPARTMENT_ROUTE_MAP = {
    'Sales': '/my/sales',
    'Cancellations': '/my/cancellations',
    'cancellations': '/my/cancellations',  # lowercase variant
}


def _get_department_route(employee):
    """Return the portal route path for the employee's department, or None.

    Contract:
    - Input: hr.employee record
    - Output: string route like '/my/sales' or None
    - If employee has no department or it's unmapped, returns None
    """
    try:
        dept_name = (employee.department_id and employee.department_id.name) or None
        if dept_name and dept_name in DEPARTMENT_ROUTE_MAP:
            return DEPARTMENT_ROUTE_MAP[dept_name]
    except Exception:
        # If department field isn't present or accessible, fail safe
        _logger.debug("Department route lookup failed; missing field or unmapped department")
    return None


from odoo.addons.web.controllers.home import Home


class AJMLoginRedirect(Home):
    """Override login to redirect portal users to their department after authentication"""

    def _login_redirect(self, uid, redirect=None):
        """Redirect users to their department portal after login"""
        user = request.env['res.users'].sudo().browse(uid)

        # Admin and internal users go to backend
        if user.has_group('base.group_system') or user.has_group('base.group_user'):
            return super()._login_redirect(uid, redirect)

        # Portal users: redirect to their department portal
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        if employee:
            route = _get_department_route(employee)
            if route:
                return route

        # Fallback to /my
        return '/my'


class AJMEmployeePortal(CustomerPortal):

    @http.route(['/my', '/my/home'], type='http', auth='user', website=True)
    def home(self, **kw):
        """Override /my and /my/home - show portal home without redirects"""
        # Simply call the parent portal home method
        return super().home(**kw)

    @http.route('/my/sales', type='http', auth='user', website=True, groups='ajm_employee_portal.group_sales_portal_user')
    def sales_dashboard(self, **kw):
        """Sales Department Portal - exclusive dashboard for Sales employees"""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        is_admin = user.has_group('base.group_system')
        values = self._get_dashboard_values(user, employee, is_admin=is_admin)
        return request.render('ajm_employee_portal.employee_dashboard', values)

    def _get_dashboard_values(self, user, employee, is_admin=False):

        # Get employee attendance data if exists
        attendance_obj = request.env['hr.attendance'].sudo()
        last_attendance = attendance_obj.search([
            ('employee_id.user_id', '=', user.id)
        ], order='check_in desc', limit=1)

        is_checked_in = last_attendance and not last_attendance.check_out

        # Use user's timezone (defaults to America/Chicago if not set)
        user_tz = pytz.timezone(user.tz or 'America/Chicago')
        ci_display = None
        ci_time_display = None
        co_display = None
        try:
            if last_attendance and last_attendance.check_in:
                # Convert UTC to user's local timezone
                check_in_utc = pytz.utc.localize(last_attendance.check_in)
                check_in_local = check_in_utc.astimezone(user_tz)
                ci_display = check_in_local.strftime('%m/%d/%Y %I:%M %p')
                ci_time_display = check_in_local.strftime('%I:%M %p')
            if last_attendance and last_attendance.check_out:
                check_out_utc = pytz.utc.localize(last_attendance.check_out)
                check_out_local = check_out_utc.astimezone(user_tz)
                co_display = check_out_local.strftime('%m/%d/%Y %I:%M %p')
        except Exception as e:
            _logger.error('Error formatting datetime: %s', e)

        return {
            'user': user,
            'employee': employee,
            'is_admin': is_admin,
            'is_checked_in': is_checked_in if employee else False,
            'last_attendance': last_attendance if employee else None,
            'tz': user.tz or 'America/Chicago',
            'ci_display': ci_display,
            'ci_time_display': ci_time_display,
            'co_display': co_display,
            'page_name': 'ajm_dashboard',
        }

    @http.route('/my/cancellations', type='http', auth='user', website=True, groups='ajm_employee_portal.group_cancellations_portal_user')
    def cancellations_dashboard(self, **kw):
        """Cancellations Department Portal - full dashboard for Cancellations employees"""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        is_admin = user.has_group('base.group_system')
        values = self._get_dashboard_values(user, employee, is_admin=is_admin)
        return request.render('ajm_employee_portal.cancellations_dashboard', values)

    # Removed generic department route by request

    @http.route('/my/ajm', type='http', auth='user', website=True)
    def ajm_legacy_redirect(self, **kw):
        """Legacy redirect: /my/ajm is deprecated, redirect to /my/department"""
        return werkzeug_redirect('/my/department')

    @http.route('/my/department', type='http', auth='user', website=True)
    def ajm_department_redirect(self, **kw):
        """Redirect to the current user's department portal route if mapped, else /my/home."""
        user = request.env.user
        is_admin = user.has_group('base.group_system')

        # Admin always goes to Sales (can see all departments)
        if is_admin:
            return werkzeug_redirect('/my/sales')

        # Non-admin: redirect based on their employee department
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        route = _get_department_route(employee) if employee else None

        # If no route found, go to /my/home (NOT /my to avoid loops)
        return werkzeug_redirect(route or '/my/home')

    # Helper route removed by request: no shortcut assignment to Sales

    @http.route('/my/sales/check-in', type='jsonrpc', auth='user')
    def ajm_check_in(self, **kw):
        """Check-in employee"""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if not employee:
            return {'error': 'No employee record found for this user'}

        # Check if already checked in
        last_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)

        if last_attendance:
            return {'error': 'Already checked in'}

        # Create check-in with UTC time
        # Add 5 hours to Houston time to get UTC
        utc_now = datetime.utcnow()
        attendance = request.env['hr.attendance'].sudo().create({
            'employee_id': employee.id,
            'check_in': utc_now,
        })

        return {
            'success': True,
            'check_in': attendance.check_in.strftime('%Y-%m-%d %H:%M:%S')
        }

    @http.route('/my/sales/check-out', type='jsonrpc', auth='user')
    def ajm_check_out(self, **kw):
        """Check-out employee"""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if not employee:
            return {'error': 'No employee record found for this user'}

        # Find open attendance
        attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False)
        ], limit=1)

        if not attendance:
            return {'error': 'Not checked in'}

        # Update check-out with UTC time
        utc_now = datetime.utcnow()
        attendance.sudo().write({
            'check_out': utc_now
        })

        return {
            'success': True,
            'check_out': attendance.check_out.strftime('%Y-%m-%d %H:%M:%S'),
            'worked_hours': attendance.worked_hours
        }

    # HTTP fallbacks so the page still works even if JS/assets fail
    @http.route('/my/sales/checkin', type='http', auth='user', website=True, csrf=False)
    def ajm_check_in_http(self, **kw):
        """HTTP fallback: perform check-in and redirect back to dashboard."""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if employee:
            last_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)
            if not last_attendance:
                utc_now = datetime.utcnow()
                request.env['hr.attendance'].sudo().create({
                    'employee_id': employee.id,
                    'check_in': utc_now,
                })

        return werkzeug_redirect('/my/sales')

    @http.route('/my/sales/checkout', type='http', auth='user', website=True, csrf=False)
    def ajm_check_out_http(self, **kw):
        """HTTP fallback: perform check-out and redirect back to dashboard."""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if employee:
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)
            if attendance:
                utc_now = datetime.utcnow()
                attendance.sudo().write({'check_out': utc_now})

        return werkzeug_redirect('/my/sales')

    @http.route('/my/cancellations/checkin', type='http', auth='user', website=True, csrf=False)
    def cancellations_check_in_http(self, **kw):
        """HTTP fallback: perform check-in and redirect back to cancellations dashboard."""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if employee:
            last_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)
            if not last_attendance:
                utc_now = datetime.utcnow()
                request.env['hr.attendance'].sudo().create({
                    'employee_id': employee.id,
                    'check_in': utc_now,
                })

        return werkzeug_redirect('/my/cancellations')

    @http.route('/my/cancellations/checkout', type='http', auth='user', website=True, csrf=False)
    def cancellations_check_out_http(self, **kw):
        """HTTP fallback: perform check-out and redirect back to cancellations dashboard."""
        user = request.env.user
        employee = request.env['hr.employee'].sudo().search([
            ('user_id', '=', user.id)
        ], limit=1)

        if employee:
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_out', '=', False)
            ], limit=1)
            if attendance:
                utc_now = datetime.utcnow()
                attendance.sudo().write({'check_out': utc_now})

        return werkzeug_redirect('/my/cancellations')
