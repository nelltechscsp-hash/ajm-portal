from . import controllers, hooks, models

# Export hook at module level for Odoo to find it by name in manifest
from .hooks import post_init_hook
