# Inventory guards, item defaults and scheduler jobs (app code, not Server Scripts).
#
# Everything here is additive on top of what the site already does:
#  - "AIG - SE Guard Raw Submit" still forces posting through the Posted state.
#  - "AIG - SE Issue Validation" still requires an approved Model 19 request.
#  - "AIG - MR Approval Guard" still blocks self-approval on a request.
# These hooks only add the store-manager gate and the cross-enterprise rules.
#
# Warehouse ownership (mixed / isolated + owning enterprise) is read from
# setup/data/warehouses.json, never from hard-coded store names.

import json
import os

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, today

SETTINGS_DOCTYPE = "AIG Minimum ERP Settings"
WAREHOUSE_DATA = os.path.join(
	os.path.dirname(__file__), "..", "setup", "data", "warehouses.json"
)

ISTOCK_ITEM_FLAGS = (
	("aig_is_stock_item", "is_stock_item", 1),
	("aig_is_fixed_asset", "is_fixed_asset", 0),
	("aig_has_batch_no", "has_batch_no", 0),
	("aig_has_serial_no", "has_serial_no", 0),
	("aig_has_expiry_date", "has_expiry_date", 0),
)


def _setting(field, default=None):
	try:
		value = frappe.db.get_single_value(SETTINGS_DOCTYPE, field)
	except Exception:
		return default
	return default if value in (None, "") else value


def _warehouse_profiles():
	"""name -> (type, enterprise) from the warehouse data file."""
	try:
		with open(WAREHOUSE_DATA, encoding="utf-8") as f:
			data = json.load(f)
	except OSError:
		return {}
	out = {}
	root = data.get("root") or {}
	if root.get("name"):
		out[root["name"]] = (root.get("type") or "mixed", root.get("enterprise"))
	for node in data.get("nodes", []):
		out[node["name"]] = (node.get("type") or "mixed", node.get("enterprise"))
	return out


def warehouse_profile(warehouse):
	if not warehouse:
		return ("mixed", None)
	profile = _warehouse_profiles().get(warehouse)
	if profile:
		return profile
	# Fallback for a warehouse created after the data file: an enterprise link
	# on the Warehouse means the store belongs to that enterprise only.
	enterprise = frappe.db.get_value("Warehouse", warehouse, "aig_cost_center")
	return ("isolated", enterprise) if enterprise else ("mixed", None)


def is_isolated(warehouse):
	return warehouse_profile(warehouse)[0] == "isolated"


def _first(values):
	for value in values:
		if value:
			return value
	return None


def _entry_warehouses(doc, table_field):
	source, target = [], []
	for row in doc.get(table_field) or []:
		if row.get("s_warehouse"):
			source.append(row.get("s_warehouse"))
		if row.get("t_warehouse"):
			target.append(row.get("t_warehouse"))
	return source, target


# ------------------------------------------------------------------ item defaults
def apply_item_group_defaults(doc, method=None):
	"""New Items inherit the batch / serial / fixed-asset flags of their group.

	Only new documents: an existing Item keeps whatever the operator set, so a
	data-file edit can never silently rewrite history.
	"""
	if not doc.is_new():
		return
	group = doc.get("item_group")
	if not group:
		return
	meta = frappe.get_meta("Item Group")
	values = frappe.db.get_value(
		"Item Group",
		group,
		[flag for flag, _field, _default in ISTOCK_ITEM_FLAGS if meta.has_field(flag)],
		as_dict=True,
	)
	if not values:
		return
	for flag, item_field, _default in ISTOCK_ITEM_FLAGS:
		if flag not in values:
			continue
		wanted = cint(values.get(flag))
		if item_field == "is_fixed_asset" and wanted:
			doc.is_fixed_asset = 1
			doc.auto_create_assets = cint(doc.get("auto_create_assets") or 1)
			continue
		if flag == "aig_is_stock_item":
			doc.is_stock_item = wanted
			continue
		if wanted:
			doc.set(item_field, 1)


# ------------------------------------------------------------- stock entry gates
def classify_stock_entry(doc, method=None):
	"""Decide whether this movement needs a Store Manager, and enforce the
	cross-enterprise rule. Runs before save so the flag is visible on the form."""
	gate_issues = cint(_setting("enable_isolated_issue_gate", 1))
	gate_transfers = cint(_setting("enable_transfer_approval", 1))
	block_cross = cint(_setting("block_cross_enterprise_transfer", 1))

	purpose = doc.get("purpose")
	source, target = _entry_warehouses(doc, "items")
	source_wh = _first(source) or doc.get("from_warehouse")
	target_wh = _first(target) or doc.get("to_warehouse")

	requires = 0

	if purpose in ("Material Issue", "Material Transfer for Manufacture") and gate_issues:
		if any(is_isolated(wh) for wh in source) or is_isolated(source_wh):
			requires = 1

	if purpose == "Material Transfer":
		if gate_transfers:
			requires = 1
		if block_cross:
			src_type, src_ent = warehouse_profile(source_wh)
			dst_type, dst_ent = warehouse_profile(target_wh)
			both_isolated = src_type == "isolated" and dst_type == "isolated"
			if both_isolated and src_ent and dst_ent and src_ent != dst_ent:
				frappe.throw(
					_(
						"AIG: transfer blocked. {0} belongs to {1} and {2} belongs to {3}. "
						"An isolated store can only transfer to a mixed warehouse; "
						"route the goods through the main store instead."
					).format(source_wh, src_ent, target_wh, dst_ent),
					title=_("Cross-enterprise transfer blocked"),
				)

	if not requires:
		# Nothing to approve: clear a stale approval so the audit trail stays true.
		doc.aig_requires_store_manager_approval = 0
		doc.aig_store_manager_approved = 0
		doc.aig_store_manager_approved_by = None
		return

	doc.aig_requires_store_manager_approval = 1


def validate_store_manager_approval(doc, method=None):
	"""Block posting an isolated-store issue / any transfer without a Store
	Manager approval, and never let the mover approve their own document."""
	if not cint(doc.get("aig_requires_store_manager_approval")):
		return
	if not cint(doc.get("aig_store_manager_approved")):
		frappe.throw(
			_(
				"AIG: this Stock Entry needs Store Manager approval before it can be "
				"posted. The approving manager uses 'Approve Store Manager Gate' on "
				"the document."
			),
			title=_("Store Manager approval required"),
		)
	approver = doc.get("aig_store_manager_approved_by")
	if approver and approver in (doc.get("owner"), frappe.session.user):
		frappe.throw(
			_("AIG: nobody approves their own stock movement (approver {0}).").format(approver),
			title=_("Self-approval blocked"),
		)


@frappe.whitelist()
def approve_store_manager_gate(stock_entry):
	"""Record a Store Manager approval on the document. Role-checked here so the
	button cannot be reached by a Store Keeper via API."""
	user = frappe.session.user
	if "System Manager" not in frappe.get_roles(user) and "AIG Store Manager" not in frappe.get_roles(user):
		frappe.throw(
			_("Only an AIG Store Manager can approve this movement."),
			frappe.PermissionError,
		)
	doc = frappe.get_doc("Stock Entry", stock_entry)
	if doc.docstatus != 0:
		frappe.throw(_("Only a draft Stock Entry can be approved."))
	if doc.get("owner") == user:
		frappe.throw(
			_("AIG: nobody approves their own stock movement."),
			title=_("Self-approval blocked"),
		)
	doc.aig_requires_store_manager_approval = 1
	doc.aig_store_manager_approved = 1
	doc.aig_store_manager_approved_by = user
	doc.flags.ignore_permissions = True
	doc.save()
	return {"name": doc.name, "approved_by": user}


def require_store_manager_for_reconciliation(doc, method=None):
	"""Stock Reconciliation is submitted by a Store Manager, never by the person
	who drafted the count."""
	if doc.docstatus != 0:
		return
	user = frappe.session.user
	roles = frappe.get_roles(user)
	if "System Manager" in roles or "AIG Store Manager" in roles:
		return
	frappe.throw(
		_(
			"AIG: a stock count is drafted by Store Expert and submitted by Store "
			"Manager. Only an AIG Store Manager can submit this reconciliation."
		),
		frappe.PermissionError,
	)


# ------------------------------------------------------------------ notifications
def _notify(user, subject, message, document_type=None, document_name=None):
	"""One Notification Log row per user/subject per day -- the dedupe key."""
	if not user:
		return False
	already = frappe.db.exists(
		"Notification Log",
		{
			"for_user": user,
			"subject": subject,
			"creation": (">", today() + " 00:00:00"),
		},
	)
	if already:
		return False
	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"subject": subject,
			"for_user": user,
			"type": "Alert",
			"email_content": message,
			"document_type": document_type,
			"document_name": document_name,
		}
	).insert(ignore_permissions=True)
	return True


def _role_users(roles):
	users = set()
	for role in roles:
		users.update(
			frappe.get_all(
				"Has Role",
				filters={"role": role, "parenttype": "User"},
				pluck="parent",
			)
		)
	return {u for u in users if frappe.db.get_value("User", u, "enabled")}


def _alert_recipients():
	roles = _setting("reorder_alert_recipient_roles") or "AIG Store Expert,AIG Store Manager"
	role_list = [r.strip() for r in str(roles).split(",") if r.strip()]
	return _role_users(role_list)


def daily_reorder_alerts():
	"""Notify Store Expert / Store Manager per warehouse when an item is at or
	below its reorder level. No Material Requests are created (auto_indent=0)."""
	if not cint(_setting("enable_reorder_alerts", 1)):
		return 0
	rows = frappe.db.sql(
		"""
		select ir.parent as item, ir.warehouse, ir.warehouse_reorder_level as level,
		       ifnull(sum(bin.actual_qty), 0) as qty
		from `tabItem Reorder` ir
		left join tabBin bin on bin.item_code = ir.parent and bin.warehouse = ir.warehouse
		where ifnull(ir.warehouse_reorder_level, 0) > 0
		group by ir.parent, ir.warehouse, ir.warehouse_reorder_level
		""",
		as_dict=True,
	)
	recipients = _alert_recipients()
	sent = 0
	for row in rows:
		if (row.qty or 0) > (row.level or 0):
			continue
		subject = _("AIG low stock: {0} at {1}").format(row.item, row.warehouse)
		message = _(
			"{0} is at {1} in {2}; the reorder level is {3}. Raise a Model 19 request "
			"if more is needed."
		).format(row.item, row.qty, row.warehouse, row.level)
		for user in recipients:
			if _notify(user, subject, message, "Item", row.item):
				sent += 1
	frappe.db.commit()
	return sent


def monthly_stock_count_reminder():
	"""Monthly nudge to Store Manager per isolated/mixed store that holds stock."""
	if not cint(_setting("enable_stock_count_reminder", 1)):
		return 0
	wanted_day = cint(_setting("stock_count_reminder_day", 1)) or 1
	if getdate(today()).day != wanted_day:
		return 0
	recipients = _role_users(["AIG Store Manager"])
	warehouses = frappe.get_all(
		"Warehouse",
		filters={"is_group": 0, "disabled": 0},
		pluck="name",
	)
	sent = 0
	for warehouse in warehouses:
		if not frappe.db.exists("Bin", {"warehouse": warehouse}):
			continue
		subject = _("AIG monthly stock count: {0}").format(warehouse)
		message = _(
			"Physical count due for {0}. Store Expert drafts the Stock "
			"Reconciliation; the Store Manager submits it."
		).format(warehouse)
		for user in recipients:
			if _notify(user, subject, message, "Warehouse", warehouse):
				sent += 1
	frappe.db.commit()
	return sent


# ------------------------------------------------------------------ diagnostics
@frappe.whitelist()
def inventory_gate_report():
	"""Small read-only summary used by the verification scripts."""
	return {
		"enable_isolated_issue_gate": cint(_setting("enable_isolated_issue_gate", 1)),
		"enable_transfer_approval": cint(_setting("enable_transfer_approval", 1)),
		"block_cross_enterprise_transfer": cint(_setting("block_cross_enterprise_transfer", 1)),
		"enable_reorder_alerts": cint(_setting("enable_reorder_alerts", 1)),
		"enable_stock_count_reminder": cint(_setting("enable_stock_count_reminder", 1)),
		"isolated_warehouses": [w for w, p in _warehouse_profiles().items() if p[0] == "isolated"],
		"mixed_warehouses": [w for w, p in _warehouse_profiles().items() if p[0] == "mixed"],
	}
