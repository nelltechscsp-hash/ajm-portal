from odoo import api, SUPERUSER_ID


def _ensure_top_menu(env, website, xmlid, name=None, url=None, sequence=None):
    """
    Ensure a website.menu with given xmlid is parented to the website root menu
    and has the expected url/sequence. Create it if missing.
    """
    Menu = env['website.menu']
    root = website.menu_id
    rec = None
    try:
        rec = env.ref(xmlid)
    except ValueError:
        rec = None

    if rec and rec.exists():
        values = {}
        if rec.parent_id.id != root.id:
            values['parent_id'] = root.id
        if url and rec.url != url:
            values['url'] = url
        if name and rec.name != name:
            values['name'] = name
        if sequence is not None and rec.sequence != sequence:
            values['sequence'] = sequence
        if rec.website_id.id != website.id:
            values['website_id'] = website.id
        if values:
            rec.write(values)
        return rec

    # Create if not found
    vals = {
        'name': name or 'Menu',
        'url': url or '/',
        'parent_id': root.id,
        'website_id': website.id,
    }
    if sequence is not None:
        vals['sequence'] = sequence
    new_rec = Menu.create(vals)
    # set xmlid for future upgrades
    env['ir.model.data'].create({
        'name': xmlid.split('.')[-1],
        'module': xmlid.split('.')[0],
        'model': 'website.menu',
        'res_id': new_rec.id,
        'noupdate': False,
    })
    return new_rec


def post_init_hook(*args):
    """Post-init tasks compatible with multiple Odoo versions.
    Accepts either (env,) on newer versions or (cr, registry) on older ones.
    - Ensure Sales and Cancellations menus are properly parented.
    - Initialize Gmail setup flags for existing users and prefill gmail_address.
    """
    if len(args) == 1:
        env = args[0]
    else:
        cr, _registry = args
        env = api.Environment(cr, SUPERUSER_ID, {})
    website = env['website'].search([], limit=1, order='id')
    if not website:
        return

    _ensure_top_menu(env, website,
                     'ajm_employee_portal.menu_top_sales',
                     name='Sales', url='/my/sales', sequence=25)
    _ensure_top_menu(env, website,
                     'ajm_employee_portal.menu_top_cancellations',
                     name='Cancellations', url='/my/cancellations', sequence=55)

    # Gmail initialization is handled by the ajm_user_gmail module
