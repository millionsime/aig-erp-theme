"""Free the module name "AIG HR" for the aig_hr app.

This app used to ship a Module Def "AIG HR" (left over from the dropped
custom_app) holding 8 server and 3 client scripts that are really theme
inventory/procurement logic. Installing aig_hr, whose own module is also
"AIG HR", would then fail with a duplicate Module Def. Move those scripts to
"AIG Custom Theme" and delete the stale Module Def, unless aig_hr owns it.
"""

import frappe


def execute():
	if not frappe.db.exists("Module Def", "AIG HR"):
		return
	if frappe.db.get_value("Module Def", "AIG HR", "app_name") == "aig_hr":
		return
	for dt in ("Server Script", "Client Script"):
		frappe.db.set_value(dt, {"module": "AIG HR"}, "module", "AIG Custom Theme",
		                    update_modified=False)
	frappe.db.delete("Module Def", {"name": "AIG HR"})
