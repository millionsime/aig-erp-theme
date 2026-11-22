"""Hand item naming to ERPNext's Stock Settings (decision S-9).

custom_theme used to generate item codes itself and shipped the Item form
property setters for "Item Code" naming (item code required and read-only,
naming series hidden). Items are now named by the series AIG-ITEM-.YYYY.-,
which ERPNext configures on its own when Stock Settings.item_naming_by is
"Naming Series" (set by aig_stock). Remove the old setters so they cannot
override ERPNext's; it recreates the ones it needs the next time Stock
Settings is saved.
"""

import frappe

OBSOLETE = (
	"Item-item_code-hidden",
	"Item-item_code-reqd",
	"Item-item_code-read_only",
	"Item-naming_series-hidden",
	"Item-naming_series-reqd",
)


def execute():
	for name in OBSOLETE:
		if frappe.db.exists("Property Setter", name):
			frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=True)
	frappe.clear_cache(doctype="Item")
