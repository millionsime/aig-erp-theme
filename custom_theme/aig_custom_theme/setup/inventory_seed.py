# Idempotent seed for the AIG inventory layer.
#
# Covers the ERPNext masters this site was missing entirely (UOMs, Item Groups,
# Stock Entry Types, Price Lists) plus the AIG stock configuration: FIFO
# valuation, hard no-negative-stock, batch/serial off by default, and the
# per-item-group flags a new Item inherits.
#
# Philosophy (same as setup/seed.py):
#  - existence checked before insert; running twice changes nothing
#  - data lives in ./data/inventory_*.json so names can be edited without code
#  - no CoA creation here; the adjustment account is adopted if it exists
#
# Manual re-run:
#   bench --site <site> execute custom_theme.aig_custom_theme.setup.inventory_seed.run_all

import json
import os

import frappe

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Custom fields the inventory layer owns. Created here (not shipped as a
# fixture) so a fresh install has them before any Item Group is inserted.
INVENTORY_CUSTOM_FIELDS = {
	"Cost Center": [
		{
			"fieldname": "aig_default_warehouse",
			"label": "AIG Default Warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"insert_after": "cost_center_name",
			"description": "Store that issues to this enterprise. Defaults onto Material Request.",
		}
	],
	"Item Group": [
		{
			"fieldname": "aig_is_stock_item",
			"label": "AIG: New Items Are Stock Items",
			"fieldtype": "Check",
			"default": "1",
			"insert_after": "is_group",
		},
		{
			"fieldname": "aig_is_fixed_asset",
			"label": "AIG: New Items Are Fixed Assets",
			"fieldtype": "Check",
			"insert_after": "aig_is_stock_item",
		},
		{
			"fieldname": "aig_has_batch_no",
			"label": "AIG: New Items Track Batches",
			"fieldtype": "Check",
			"insert_after": "aig_is_fixed_asset",
		},
		{
			"fieldname": "aig_has_serial_no",
			"label": "AIG: New Items Track Serial Numbers",
			"fieldtype": "Check",
			"insert_after": "aig_has_batch_no",
		},
		{
			"fieldname": "aig_has_expiry_date",
			"label": "AIG: New Items Have Expiry",
			"fieldtype": "Check",
			"insert_after": "aig_has_serial_no",
		},
	],
	"Material Request": [
		{
			"fieldname": "aig_forwarded_to_procurement",
			"label": "Forwarded to Procurement",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "aig_assigned_procurement_officer",
			"description": "Set by the store verification step when the item is not in stock. TODO(procurement): the procurement workflow picks this up.",
		},
		{
			"fieldname": "aig_procurement_reference",
			"label": "Procurement Reference",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "aig_forwarded_to_procurement",
		},
		{
			"fieldname": "aig_rejected_reason",
			"label": "Rejection Reason",
			"fieldtype": "Small Text",
			"insert_after": "aig_purpose_note",
		},
	],
	"Stock Entry": [
		{
			"fieldname": "aig_requires_store_manager_approval",
			"label": "Requires Store Manager Approval",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "aig_needs_main_approval",
		},
		{
			"fieldname": "aig_store_manager_approved",
			"label": "Store Manager Approved",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "aig_requires_store_manager_approval",
		},
		{
			"fieldname": "aig_store_manager_approved_by",
			"label": "Approved By (Store Manager)",
			"fieldtype": "Link",
			"options": "User",
			"read_only": 1,
			"insert_after": "aig_store_manager_approved",
		},
		{
			"fieldname": "aig_handed_over_to_procurement",
			"label": "Handed Over to Procurement",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "aig_store_manager_approved_by",
			"description": "TODO(procurement): set when the receipt document is handed to the procurement workflow.",
		},
	],
	"Stock Reconciliation": [
		{
			"fieldname": "aig_approved_by",
			"label": "Approved By (Store Manager)",
			"fieldtype": "Link",
			"options": "User",
			"read_only": 1,
			"insert_after": "aig_reason_code",
		}
	],
}


def _load(name):
	with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
		return json.load(f)


def log(*a):
	print(*a, flush=True)


def ensure_custom_fields():
	"""Create the inventory Custom Fields. Never overwrites an existing field, so
	an operator's own label/description edits on the site survive a re-seed."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	missing = {}
	for dt, fields in INVENTORY_CUSTOM_FIELDS.items():
		meta = frappe.get_meta(dt)
		todo = [dict(f) for f in fields if not meta.has_field(f["fieldname"])]
		if todo:
			missing[dt] = todo
	if not missing:
		log("  custom fields: already present")
		return
	create_custom_fields(missing, ignore_validate=True)
	for dt, fields in missing.items():
		log(f"  custom fields created on {dt}: {', '.join(f['fieldname'] for f in fields)}")


def seed_warehouse_types():
	n = 0
	for wt in _load("inventory_warehouse_types.json")["types"]:
		if frappe.db.exists("Warehouse Type", wt):
			continue
		frappe.get_doc({"doctype": "Warehouse Type", "name": wt}).insert(ignore_permissions=True)
		n += 1
	log(f"  warehouse types: {n} created")


def seed_uom_categories():
	"""UOM Category is mandatory on a UOM Conversion Factor in v16. Categories
	are derived from the data file, so adding a UOM needs no code change."""
	created = 0
	for cat in _load("inventory_uoms.json").get("categories", []):
		if frappe.db.exists("UOM Category", cat):
			continue
		frappe.get_doc({"doctype": "UOM Category", "category_name": cat}).insert(
			ignore_permissions=True
		)
		created += 1
	log(f"  uom categories: {created} created")


def seed_uoms():
	created = 0
	for uom in _load("inventory_uoms.json")["uoms"]:
		if not frappe.db.exists("UOM", uom["name"]):
			doc = frappe.get_doc({"doctype": "UOM", "uom_name": uom["name"]})
			if uom.get("category"):
				doc.category = uom["category"]
			doc.insert(ignore_permissions=True)
			created += 1
		elif uom.get("category"):
			# keep an existing UOM's category in step with the data file
			frappe.db.set_value(
				"UOM", uom["name"], "category", uom["category"], update_modified=False
			)
		for conv in uom.get("conversions", []):
			exists = frappe.db.exists(
				"UOM Conversion Factor", {"from_uom": uom["name"], "to_uom": conv["to"]}
			)
			if exists:
				continue
			frappe.get_doc(
				{
					"doctype": "UOM Conversion Factor",
					"category": uom.get("category"),
					"from_uom": uom["name"],
					"to_uom": conv["to"],
					"value": conv["factor"],
				}
			).insert(ignore_permissions=True)
			log(f"  conversion: 1 {uom['name']} = {conv['factor']} {conv['to']}")
	log(f"  uoms: {created} created")


def seed_item_groups():
	data = _load("inventory_item_groups.json")
	root = data["root"]
	created = 0
	if not frappe.db.exists("Item Group", root):
		frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": root,
				"parent_item_group": "",
				"is_group": 1,
				"aig_is_stock_item": 1,
			}
		).insert(ignore_permissions=True)
		log(f"  item group root created: {root}")
		created += 1

	flags = (
		"aig_is_stock_item",
		"aig_is_fixed_asset",
		"aig_has_batch_no",
		"aig_has_serial_no",
		"aig_has_expiry_date",
	)
	for g in data["groups"]:
		if frappe.db.exists("Item Group", g["name"]):
			continue
		doc = frappe.new_doc("Item Group")
		doc.item_group_name = g["name"]
		doc.parent_item_group = g["parent"]
		doc.is_group = 0
		# Defaults: a stock item, not an asset, no batch/serial tracking unless
		# the data file says otherwise.
		doc.aig_is_stock_item = 1
		doc.aig_is_fixed_asset = 0
		for flag in flags:
			short = flag.replace("aig_", "")
			if short in g:
				setattr(doc, flag, g[short])
		doc.insert(ignore_permissions=True)
		created += 1
	log(f"  item groups: {created} created")


def seed_stock_entry_types():
	n = 0
	for t in _load("inventory_stock_entry_types.json")["types"]:
		if frappe.db.exists("Stock Entry Type", t["name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "Stock Entry Type",
				"name": t["name"],
				"purpose": t["purpose"],
				"is_standard": 1,
			}
		).insert(ignore_permissions=True)
		n += 1
	log(f"  stock entry types: {n} created")


def seed_price_lists():
	n = 0
	for pl in _load("inventory_price_lists.json")["price_lists"]:
		if frappe.db.exists("Price List", pl["name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "Price List",
				"price_list_name": pl["name"],
				"currency": pl.get("currency", "ETB"),
				"buying": pl["buying"],
				"selling": pl["selling"],
				"enabled": 1,
			}
		).insert(ignore_permissions=True)
		n += 1
	log(f"  price lists: {n} created")




MODULE_DEF = "AIG Custom Theme"


def ensure_module_def():
	"""The app's own Module Def is absent on this site (the shipped fixture only
	carries frappe's modules), and a DocType cannot be created without it."""
	if not frappe.db.exists("Module Def", MODULE_DEF):
		frappe.get_doc(
			{"doctype": "Module Def", "module_name": MODULE_DEF, "app_name": "custom_theme"}
		).insert(ignore_permissions=True)
		log(f"  module def created: {MODULE_DEF}")
		frappe.clear_cache()
	# frappe.local.module_app is a per-request dict built at boot from Module
	# Def; doctype inserts resolve the module through it, so register the module
	# for this process too -- otherwise DocType.on_update raises
	# "Module AIG Custom Theme not found" even though the row exists.
	frappe.local.module_app[frappe.scrub(MODULE_DEF)] = "custom_theme"


def ensure_settings_doctype():
	"""Create or refresh AIG Minimum ERP Settings from its app JSON.

	Model sync does not pick this DocType up (its module folder is skipped), so
	the seed owns it: insert when the row is missing, refresh the field list when
	the JSON carries a newer `modified`. Values already stored in the Single are
	left alone.
	"""
	path = frappe.get_app_path(
		"custom_theme",
		"aig_custom_theme",
		"doctype",
		"aig_minimum_erp_settings",
		"aig_minimum_erp_settings.json",
	)
	with open(path, encoding="utf-8") as f:
		spec = json.load(f)

	name = spec["name"]
	stored = frappe.db.get_value("DocType", name, "modified")
	# in_patch: Frappe only allows creating a *standard* (non-custom) DocType
	# outside developer mode while in a patch/test context. Production keeps
	# developer_mode off, so the seed borrows the patch flag for this step.
	had_flag = frappe.flags.in_patch
	frappe.flags.in_patch = True
	try:
		if not stored:
			doc = frappe.get_doc(spec)
			doc.flags.ignore_permissions = True
			# The Module Def for this app was only just created; link checks on
			# this one insert would otherwise reject it from a stale registry.
			frappe.flags.ignore_links = True
			try:
				doc.insert()
			finally:
				frappe.flags.ignore_links = False
			log(f"  settings doctype created: {name}")
			return

		if str(stored) >= str(spec.get("modified") or ""):
			log("  settings doctype: up to date")
			return

		doc = frappe.get_doc("DocType", name)
		doc.set("fields", [])
		for field in spec["fields"]:
			doc.append("fields", field)
		doc.field_order = spec.get("field_order")
		doc.permissions = [p for p in doc.permissions]
		doc.flags.ignore_permissions = True
		doc.save()
		log(f"  settings doctype refreshed: {name} ({len(spec['fields'])} fields)")
	finally:
		frappe.flags.in_patch = had_flag


def apply_stock_settings():
	data = _load("inventory_settings.json")["stock_settings"]
	doc = frappe.get_single("Stock Settings")
	meta = frappe.get_meta("Stock Settings")
	changed = []
	for field, value in data.items():
		if not meta.has_field(field):
			continue
		if doc.get(field) != value:
			doc.set(field, value)
			changed.append(field)
	doc.flags.ignore_permissions = True
	if changed:
		doc.save()
		log(f"  stock settings set: {', '.join(changed)}")
	else:
		log("  stock settings: already set")
	return doc


def adopt_adjustment_account():
	"""Point the company at an existing stock-adjustment account. Never creates
	one: the AIG CoA importer (aig-erp-config scripts 80-86) owns the chart."""
	company = frappe.db.get_value("Company", {}, "name")
	if not company:
		log("  adjustment account: no company")
		return
	if not frappe.get_meta("Company").has_field("stock_adjustment_account"):
		log("  adjustment account: company field missing")
		return
	current = frappe.db.get_value("Company", company, "stock_adjustment_account")
	if current and frappe.db.exists("Account", current):
		log(f"  adjustment account: already set ({current})")
		return
	candidate = frappe.db.get_value(
		"Account",
		{"company": company, "account_type": "Stock Adjustment", "is_group": 0},
		"name",
	)
	if not candidate:
		log("  adjustment account: none in CoA (aig-erp-config CoA not imported?) -- left unset")
		return
	frappe.db.set_value("Company", company, "stock_adjustment_account", candidate, update_modified=False)
	log(f"  adjustment account adopted: {candidate}")



# Gates that must default ON even on a site where the Single has never been
# saved: an unset Check reads back as 0, which would silently disable a control.
SETTING_DEFAULTS = {
	"enable_isolated_issue_gate": 1,
	"enable_transfer_approval": 1,
	"block_cross_enterprise_transfer": 1,
	"enable_reorder_alerts": 1,
	"reorder_alert_recipient_roles": "AIG Store Expert,AIG Store Manager",
	"enable_stock_count_reminder": 1,
	"stock_count_reminder_day": 1,
	"enable_closest_boss_guard": 1,
}


def apply_settings_defaults():
	"""Write the gate defaults only where the field has never been stored, so an
	operator's explicit 0 is never overwritten by a re-seed."""
	written = []
	for field, default in SETTING_DEFAULTS.items():
		stored = frappe.db.sql(
			"select value from tabSingles where doctype=%s and field=%s",
			("AIG Minimum ERP Settings", field),
		)
		if stored:
			continue
		frappe.db.set_single_value("AIG Minimum ERP Settings", field, default)
		written.append(field)
	if written:
		log(f"  inventory settings defaulted: {', '.join(written)}")
	else:
		log("  inventory settings: already stored")


def run_all(report_only=False):
	# in_patch / in_install: migrate and after_install run without a user context.
	if not (frappe.flags.in_patch or frappe.flags.in_install):
		frappe.only_for("System Manager")
	if report_only:
		log(
			f"uoms={frappe.db.count('UOM')} item_groups={frappe.db.count('Item Group')} "
			f"se_types={frappe.db.count('Stock Entry Type')} price_lists={frappe.db.count('Price List')}"
		)
		return
	log("=== AIG inventory seed ===")
	ensure_module_def()
	ensure_settings_doctype()
	ensure_custom_fields()
	seed_warehouse_types()
	seed_uom_categories()
	seed_uoms()
	seed_item_groups()
	seed_stock_entry_types()
	seed_price_lists()
	apply_stock_settings()
	apply_settings_defaults()
	adopt_adjustment_account()
	log("=== inventory seed complete (idempotent) ===")


run = run_all
