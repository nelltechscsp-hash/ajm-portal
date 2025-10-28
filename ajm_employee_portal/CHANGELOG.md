# Changelog

All notable changes to the AJM Employee Portal module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-24

### Added

- **Security Groups**: Created `group_sales_portal_user` and `group_cancellations_portal_user` for role-based access control
- **User Form Field**: Added `ajm_portal_access` selection field in user form (Access Rights tab) to easily assign portal roles
- **Automatic Role Assignment**: Selecting a portal automatically sets user as Portal and removes backend access
- **Website Menu Groups**: Sales and Cancellations menus now only visible to authorized users via `group_ids`
- **Login Template**: Custom branding on login page via QWeb inheritance
- **Dynamic Timezone Support**: Users' attendance times now display in their configured timezone using `pytz`

### Changed

- **Security Architecture** (BREAKING): Replaced custom `_check_portal_access()` with native Odoo `groups=` decorator in HTTP routes
- **Controller Simplification**: Removed 70+ lines of manual access validation code
- **Timezone Handling**: Changed from hardcoded Houston offset (`-5 hours`) to dynamic timezone using `user.tz` field
- **Login Flow**: Replaced full `/web/login` override with inheritance of `web.Home._login_redirect()` method
- **Record Rules**: Updated `ir.rule` to use new specific groups instead of generic `base.group_portal`

### Removed

- **Legacy Files**: Deleted `views/department_dashboard.xml` and `views/department_placeholder.xml`
- **Unused Templates**: Removed commented-out portal_templates.xml, website_quicklinks.xml, website_menu.xml references
- **Custom Login HTML**: Removed 90-line inline HTML login form in favor of QWeb template
- **Helper Method**: Removed `_check_portal_access()` method (replaced by native framework)

### Fixed

- **Menu Visibility**: Website menus no longer visible to unauthorized users (403 error prevention)
- **Timezone Accuracy**: DST (Daylight Saving Time) now handled automatically by pytz
- **Group Conflicts**: Resolved "mutual exclusivity" error between Portal/Public groups
- **Field References**: Fixed `sel_groups_portal_dept` → `ajm_portal_access` migration

### Security

- **Access Control**: HTTP routes now enforce permissions at framework level using `groups=` parameter
- **Data Isolation**: Users can only access their own attendance records via `ir.rule` domain filters
- **Menu Restrictions**: Website navigation automatically filtered by user group membership

### Technical Debt Reduced

- **Code Lines**: Reduced controller code by ~150 lines
- **Manifest Entries**: Cleaned from 15 data files to 9 essential files
- **Dependencies**: Clarified module depends (base, web, website, portal, auth_signup, hr_attendance)

---

## [1.0.0] - 2025-10-XX (Initial Development)

### Added

- Initial employee portal with department-specific dashboards
- Check-in/check-out functionality for attendance tracking
- Sales and Cancellations department support
- Custom login controller
- Website menu integration
- Basic timezone handling for Houston (America/Chicago)

### Features

- Department-based access control
- Employee attendance dashboard with last check-in/out display
- Portal home override to prevent unwanted redirects
- Legacy redirect support (`/my/ajm` → `/my/department`)

---

## Migration Notes

### Upgrading from 1.0.0 to 1.1.0

**Database Changes Required:**

```bash
# Stop Odoo
sudo systemctl stop odoo

# Run upgrade
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d ajmdb -u ajm_employee_portal --stop-after-init

# Start Odoo
sudo systemctl start odoo
```

**Post-Upgrade Steps:**

1. Reassign portal users to new groups via Settings > Users > Access Rights > AJM Portal Access
2. Verify website menus only show for authorized users
3. Test login redirect for portal users
4. Confirm timezone displays correctly for users in different timezones

**Breaking Changes:**

- Users previously assigned only `base.group_portal` will need explicit `Portal / Sales` or `Portal / Cancellations` group
- Custom code calling `_check_portal_access()` will break (method removed)
- Website menus require group membership to be visible

---

## Development Notes

### Architecture Decisions

**Why native groups= instead of custom validation?**

- Framework handles 403 responses automatically
- Better integration with Odoo security audit tools
- Reduces maintenance burden
- Follows Odoo best practices

**Why pytz for timezone?**

- Handles DST transitions automatically
- Supports all IANA timezone database
- Future-proof for international expansion
- Uses user's configured timezone preference

**Why QWeb inheritance for login?**

- Preserves Odoo features (OAuth, 2FA, password reset)
- Easier to customize with standard Odoo tools
- Reduces security risk from custom auth code
- Maintainable across Odoo versions

### Future Enhancements

**Planned for 1.2.0:**

- [ ] Operations and HR department portals (currently removed)
- [ ] Attendance reports and analytics
- [ ] Mobile-responsive dashboard improvements
- [ ] Email notifications for missed check-outs

**Under Consideration:**

- [ ] Multi-company support
- [ ] Custom dashboard widgets per department
- [ ] Integration with HR payroll
- [ ] Geolocation validation for check-in

---

## Contributors

- Development Team: AJM Insurance & Trucking Services
- Technical Lead: GitHub Copilot
- Framework: Odoo 19.0

---

## License

LGPL-3.0
