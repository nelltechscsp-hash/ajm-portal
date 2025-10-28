# Guía: Grupos de Seguridad por Portal

## Resumen

Se han creado **dos grupos de seguridad** para controlar el acceso a los portales de Sales y Cancellations:

- **Sales Portal User**: Solo accede a `/my/sales`
- **Cancellations Portal User**: Solo accede a `/my/cancellations`

Los usuarios con estos grupos:

- ✅ Pueden acceder a su portal específico
- ✅ Pueden hacer check-in/check-out en su portal
- ✅ Solo ven su propia asistencia y datos de empleado
- ❌ NO pueden acceder al backend (`/web`)
- ❌ NO pueden ver datos de otros empleados
- ❌ NO pueden acceder al portal del otro departamento

**Admin (base.group_system)** siempre tiene acceso completo a todos los portales.

---

## Cómo Asignar Grupos desde el Backend

### Método 1: Desde la UI de Odoo

1. Ir a **Settings > Users & Companies > Users**
2. Abrir el usuario (ej: `http://localhost:8069/odoo/users/7`)
3. Pestaña **"Access Rights"**
4. Buscar la sección de grupos (puede aparecer como "Other" o sin categoría)
5. Marcar el checkbox de:
   - **Sales Portal User** (para acceso a Sales), o
   - **Cancellations Portal User** (para acceso a Cancellations)
6. Guardar

> **Nota**: El grupo "Portal" (base.group_portal) se asigna automáticamente porque está en `implied_ids`.

---

## Cómo Asignar Grupos via Odoo Shell

### Opción A: Script completo de ejemplo

```bash
cat /opt/odoo/custom_addons/ajm_employee_portal/tools/assign_portal_groups.py | \
  sudo -u odoo odoo shell -c /etc/odoo/odoo.conf -d ajmdb
```

### Opción B: Asignar manualmente desde shell

```bash
sudo -u odoo odoo shell -c /etc/odoo/odoo.conf -d ajmdb
```

Dentro del shell:

```python
# Asignar Sales Portal User a un usuario
user = env['res.users'].search([('login', '=', 'sales@ajm.com')], limit=1)
sales_group = env.ref('ajm_employee_portal.group_sales_portal_user')
user.write({'groups_id': [(4, sales_group.id)]})
env.cr.commit()

# Asignar Cancellations Portal User a otro usuario
user = env['res.users'].browse(7)  # Por ID
cancel_group = env.ref('ajm_employee_portal.group_cancellations_portal_user')
user.write({'groups_id': [(4, cancel_group.id)]})
env.cr.commit()
```

---

## Reglas de Seguridad Aplicadas

### Record Rules (ir.rule)

Cada grupo tiene reglas que restringen el acceso a:

1. **hr.attendance**: Solo puede ver/crear sus propios registros

   - Domain: `[('employee_id.user_id', '=', user.id)]`
   - Permisos: Read ✓, Write ✓, Create ✓, Delete ✗

2. **hr.employee**: Solo puede ver su propio registro de empleado
   - Domain: `[('user_id', '=', user.id)]`
   - Permisos: Read ✓, Write ✗, Create ✗, Delete ✗

### Access Rights (ir.model.access.csv)

Los grupos tienen acceso a los modelos necesarios:

- `hr.attendance`: Read, Write, Create
- `hr.employee`: Read only

---

## Validación en Controllers

Los controllers verifican el grupo antes de mostrar el dashboard:

```python
# En /my/sales
has_access, employee = self._check_portal_access('ajm_employee_portal.group_sales_portal_user')
if not has_access:
    return 403 Forbidden

# En /my/cancellations
has_access, employee = self._check_portal_access('ajm_employee_portal.group_cancellations_portal_user')
if not has_access:
    return 403 Forbidden
```

Si el usuario intenta acceder sin permiso, recibe un error **403 Forbidden**.

---

## Verificar Grupos Asignados

Desde Odoo shell:

```python
# Ver todos los usuarios con Sales Portal
sales_group = env.ref('ajm_employee_portal.group_sales_portal_user')
users = env['res.users'].search([('groups_id', 'in', sales_group.id)])
for u in users:
    print(f"{u.name} ({u.login})")

# Ver todos los usuarios con Cancellations Portal
cancel_group = env.ref('ajm_employee_portal.group_cancellations_portal_user')
users = env['res.users'].search([('groups_id', 'in', cancel_group.id)])
for u in users:
    print(f"{u.name} ({u.login})")
```

---

## Testing

### Prueba 1: Usuario con Sales Portal User

1. Login con un usuario que tenga **Sales Portal User**
2. Navegar a `/my/sales` → ✅ Debería ver el dashboard
3. Intentar `/my/cancellations` → ❌ Error 403 Forbidden

### Prueba 2: Usuario con Cancellations Portal User

1. Login con un usuario que tenga **Cancellations Portal User**
2. Navegar a `/my/cancellations` → ✅ Debería ver el dashboard
3. Intentar `/my/sales` → ❌ Error 403 Forbidden

### Prueba 3: Admin

1. Login con admin
2. Puede acceder a ambos portales sin restricción

---

## Archivos Modificados

```
ajm_employee_portal/
├── security/
│   ├── security_groups.xml      [NUEVO] Define grupos Sales/Cancellations
│   └── ir.model.access.csv      [MODIFICADO] Access rights por grupo
├── controllers/
│   └── main.py                  [MODIFICADO] Validación con _check_portal_access()
├── tools/
│   └── assign_portal_groups.py  [NUEVO] Script de ejemplo
└── __manifest__.py              [MODIFICADO] Agregado security_groups.xml
```

---

## Comandos de Mantenimiento

```bash
# Upgrade del módulo (después de cambios en security/)
sudo systemctl stop odoo
sudo -u odoo odoo -c /etc/odoo/odoo.conf -d ajmdb -u ajm_employee_portal --stop-after-init
sudo systemctl start odoo

# Restart (después de cambios en controllers/)
sudo systemctl restart odoo

# Ver logs
journalctl -u odoo -f
```
