# Test factory: builds the users, employees and stock a verification run needs.
#
# TEST SITES ONLY. create_all() refuses to run unless developer_mode is on, the
# AIG_TEST_SITE env var is set, or frappe.flags.aig_test_site is True, so it can
# never fire from a production migrate or an ordinary desk request.
#
# Everything it creates carries the "AIGTEST" tag (email domain / employee
# naming / item prefix) and teardown() removes exactly those records.

import os

import frappe
from frappe.utils import add_days, today

TAG = "AIGTEST"
EMAIL_DOMAIN = "aigtest.local"
COMPANY = "Adama Investment Group"
ABBR = "AIG"

# key -> (first name, [roles], designation)
PEOPLE = {
	"employee": ("Test Employee", ["AIG End User"], "Officer"),
	"team_leader": ("Test Team Leader", ["AIG Team Leader", "AIG End User"], "Team Leader"),
	"enterprise_head": ("Test Enterprise Head", ["AIG Enterprise Head"], "Enterprise Head"),
	"ceo": ("Test CEO", ["AIG CEO"], "Chief Executive"),
	"store_keeper": ("Test Store Keeper", ["AIG Store Keeper"], "Store Keeper"),
	"store_expert": ("Test Store Expert", ["AIG Store Expert"], "Store Expert"),
	"store_manager": ("Test Store Manager", ["AIG Store Manager"], "Store Manager"),
	"hr_expert": ("Test HR Expert", ["AIG HR Expert"], "HR Officer"),
	"hr_director": ("Test HR Director", ["AIG HR Director"], "HR Director"),
	"accountant": ("Test Accountant", ["AIG Accountant"], "Accountant"),
	"proc_dev": ("Test Procurement Developer", ["AIG Procurement Developer"], "Developer"),
	"hr_dev": ("Test HR Developer", ["AIG HR Developer"], "Developer"),
}

# key -> reports_to key (the closest-boss chain)
CHAIN = {
	"enterprise_head": "ceo",
	"team_leader": "enterprise_head",
	"employee": "team_leader",
	"hr_expert": "hr_director",
	"hr_director": "ceo",
	"store_keeper": "store_expert",
	"store_expert": "store_manager",
}

COST_CENTERS = ["Administration - AIG", "Construction Enterprise - AIG", "Agro Enterprise - AIG"]


def _allowed():
	return bool(
		frappe.conf.get("developer_mode")
		or os.environ.get("AIG_TEST_SITE")
		or frappe.flags.get("aig_test_site")
	)


def _guard():
	if not _allowed():
		frappe.throw(
			"Test factory refused: set AIG_TEST_SITE=1 (or developer_mode) and run "
			"against a throwaway site. It must never run on production.",
			frappe.PermissionError,
		)


def email(key):
	return f"{key}@{EMAIL_DOMAIN}"


def user(key):
	return email(key)


# --------------------------------------------------------------------- users
def create_users():
	_guard()
	made = []
	for key, (first_name, roles, designation) in PEOPLE.items():
		mail = email(key)
		if frappe.db.exists("User", mail):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": mail,
				"first_name": first_name,
				"last_name": TAG,
				"send_welcome_email": 0,
				"user_type": "System User",
				"enabled": 1,
				"roles": [{"role": r} for r in roles if frappe.db.exists("Role", r)],
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		made.append(mail)
	return made


# ----------------------------------------------------------------- employees
def create_employees():
	"""Employees wired into the Employee -> Team Leader -> Enterprise Head -> CEO
	chain, each with a cost center from the seeded tree so the enterprise rules
	have something to test against."""
	_guard()
	made = {}
	for key in PEOPLE:
		existing = frappe.db.get_value("Employee", {"user_id": email(key)}, "name")
		if existing:
			made[key] = existing
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Employee",
				"first_name": PEOPLE[key][0],
				"last_name": TAG,
				"employee_name": f"{PEOPLE[key][0]} {TAG}",
				"company": COMPANY,
				"user_id": email(key),
				"status": "Active",
				"gender": "Other",
				"date_of_birth": "1990-01-01",
				"date_of_joining": "2024-01-01",
				"designation": PEOPLE[key][2] if frappe.db.exists("Designation", PEOPLE[key][2]) else None,
				"holiday_list": frappe.db.get_value("Holiday List", {}, "name"),
				"cost_center": COST_CENTERS[0] if frappe.db.exists("Cost Center", COST_CENTERS[0]) else None,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
		made[key] = doc.name

	# second pass: reports_to (needs all employees to exist)
	for key, boss_key in CHAIN.items():
		if made.get(key) and made.get(boss_key):
			frappe.db.set_value("Employee", made[key], "reports_to", made[boss_key], update_modified=False)
	return made


def create_leave_allocations():
	_guard()
	from frappe.utils import getdate

	year_start = getdate(f"{getdate(today()).year}-01-01")
	made = []
	for key in ("employee", "team_leader", "hr_expert", "hr_director"):
		employee = frappe.db.get_value("Employee", {"user_id": email(key)}, "name")
		if not employee:
			continue
		for leave_type in ("Annual", "Sick", "Maternity"):
			if not frappe.db.exists("Leave Type", leave_type):
				continue
			exists = frappe.db.exists(
				"Leave Allocation", {"employee": employee, "leave_type": leave_type}
			)
			if exists:
				continue
			doc = frappe.get_doc(
				{
					"doctype": "Leave Allocation",
					"employee": employee,
					"leave_type": leave_type,
					"from_date": year_start,
					"to_date": add_days(year_start, 364),
					"new_leaves_allocated": 20 if leave_type != "Maternity" else 90,
				}
			)
			doc.flags.ignore_permissions = True
			doc.insert()
			doc.submit()
			made.append(doc.name)
	return made


# --------------------------------------------------------------------- stock
def create_item_and_stock():
	"""One stock item with stock in a mixed store and in an isolated store."""
	_guard()
	item_code = f"{TAG}-ITEM"
	if not frappe.db.exists("Item", item_code):
		doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_name": "AIG test stock item",
				"item_group": "Consumables",
				"stock_uom": "Nos",
				"is_stock_item": 1,
			}
		)
		doc.flags.ignore_permissions = True
		doc.insert()
	return item_code


def _receive(item_code, warehouse, qty, rate):
	"""Open stock via Stock Reconciliation.

	Chosen over a Stock Entry receipt because the Stock Entry is workflow-bound
	(AIG Store Receiving): a test factory must not be the one place that bypasses
	the workflow. Reconciliation has no workflow, so instead it exercises the
	inventory layer's own rule -- a store role drafts, Store Manager submits.
	"""
	user = frappe.session.user
	# Store Keeper drafts (AIG Store Expert has no create perm on Stock
	# Reconciliation -- a real permissions gap, recorded in the report).
	frappe.set_user(email("store_keeper"))
	try:
		rec = frappe.get_doc(
			{
				"doctype": "Stock Reconciliation",
				"company": COMPANY,
				"purpose": "Stock Reconciliation",
				"items": [
					{
						"item_code": item_code,
						"warehouse": warehouse,
						"qty": qty,
						"valuation_rate": rate,
					}
				],
			}
		)
		rec.flags.ignore_permissions = True
		rec.insert()
	finally:
		frappe.set_user(user)

	frappe.set_user(email("store_manager"))
	try:
		rec.flags.ignore_permissions = True
		rec.submit()
	finally:
		frappe.set_user(user)
	return rec.name


def create_stock(item_code=None, warehouses=("Main Store - AIG", "Project Store - AIG")):
	_guard()
	item_code = item_code or f"{TAG}-ITEM"
	made = []
	for warehouse in warehouses:
		if not frappe.db.exists("Warehouse", warehouse):
			continue
		if frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty"):
			continue
		made.append(_receive(item_code, warehouse, 100, 10))
	return made


# ------------------------------------------------------------------ entrypoint
def create_all():
	_guard()
	frappe.flags.aig_test_site = True
	out = {
		"users": create_users(),
		"employees": create_employees(),
		"leave_allocations": create_leave_allocations(),
		"item": create_item_and_stock(),
	}
	out["stock"] = create_stock(out["item"])
	frappe.db.commit()
	return out


# ------------------------------------------------------------------- teardown
def teardown():
	_guard()
	removed = {"users": 0, "employees": 0}
	for doctype, filters in (
		("Leave Allocation", {"employee": ("like", "%" + TAG)}),
	):
		for name in frappe.get_all(doctype, filters=filters, pluck="name"):
			try:
				doc = frappe.get_doc(doctype, name)
				if doc.docstatus == 1:
					doc.flags.ignore_permissions = True
					doc.cancel()
				frappe.delete_doc(doctype, name, force=1, ignore_permissions=True)
			except Exception:
				pass
			removed[doctype] = removed.get(doctype, 0) + 1

	for name in frappe.get_all("Employee", filters={"last_name": TAG}, pluck="name"):
		frappe.delete_doc("Employee", name, force=1, ignore_permissions=True)
		removed["employees"] += 1

	for name in frappe.get_all("User", filters={"last_name": TAG}, pluck="name"):
		frappe.delete_doc("User", name, force=1, ignore_permissions=True)
		removed["users"] += 1

	frappe.db.commit()
	return removed
