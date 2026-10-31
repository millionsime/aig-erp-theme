# Patch: apply the AIG foundation seed on an existing site during migrate.
# Idempotent by construction (seed functions check existence first).


import frappe


def execute():
    from custom_theme.aig_custom_theme.setup import seed

    try:
        seed.run_all()
    except Exception:
        frappe.logger("foundation_seed").error("foundation seed failed", exc_info=True)
        raise
