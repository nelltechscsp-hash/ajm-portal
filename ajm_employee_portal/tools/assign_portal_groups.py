"""
Script de ejemplo para asignar grupos de portal a usuarios desde Odoo shell

Uso:
  cat assign_portal_groups.py | sudo -u odoo odoo shell -c /etc/odoo/odoo.conf -d ajmdb

Este script muestra cómo:
1. Asignar el grupo "Sales Portal User" a un usuario
2. Asignar el grupo "Cancellations Portal User" a un usuario
3. Verificar los grupos asignados

Desde el backend UI:
- Ir a Settings > Users & Companies > Users
- Abrir el usuario
- Pestaña "Access Rights"
- En la sección "AJM Employee Portal" o "Other" seleccionar:
  * "Sales Portal User" o
  * "Cancellations Portal User"
"""

# Ejemplo 1: Asignar Sales Portal User a un usuario por email
user_email = 'sales@example.com'  # CAMBIAR por el email real
user = env['res.users'].search([('login', '=', user_email)], limit=1)

if user:
    sales_group = env.ref('ajm_employee_portal.group_sales_portal_user')
    
    # Agregar al grupo (sin quitar otros grupos)
    user.write({'groups_id': [(4, sales_group.id)]})
    
    print(f"✓ Usuario {user.name} ({user.login}) agregado al grupo: {sales_group.name}")
    print(f"  Grupos actuales: {', '.join([g.name for g in user.groups_id])}")
else:
    print(f"✗ Usuario con email {user_email} no encontrado")

print("\n" + "="*60 + "\n")

# Ejemplo 2: Asignar Cancellations Portal User a un usuario por ID
user_id = 7  # CAMBIAR por el ID real del usuario
user = env['res.users'].browse(user_id)

if user.exists():
    cancel_group = env.ref('ajm_employee_portal.group_cancellations_portal_user')
    
    # Agregar al grupo
    user.write({'groups_id': [(4, cancel_group.id)]})
    
    print(f"✓ Usuario {user.name} ({user.login}) agregado al grupo: {cancel_group.name}")
    print(f"  Grupos actuales: {', '.join([g.name for g in user.groups_id])}")
else:
    print(f"✗ Usuario con ID {user_id} no encontrado")

print("\n" + "="*60 + "\n")

# Ejemplo 3: Listar todos los usuarios con grupos de portal AJM
sales_group = env.ref('ajm_employee_portal.group_sales_portal_user')
cancel_group = env.ref('ajm_employee_portal.group_cancellations_portal_user')

print("Usuarios con Sales Portal User:")
for u in env['res.users'].search([('groups_id', 'in', sales_group.id)]):
    print(f"  - {u.name} ({u.login}) [ID: {u.id}]")

print("\nUsuarios con Cancellations Portal User:")
for u in env['res.users'].search([('groups_id', 'in', cancel_group.id)]):
    print(f"  - {u.name} ({u.login}) [ID: {u.id}]")

# IMPORTANTE: Commit para guardar cambios
env.cr.commit()
print("\n✓ Cambios guardados")
