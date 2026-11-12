# Idempotent seed for AIG master data (company, fiscal years, cost centers,
# warehouses, departments, designations, roles, settings single).
#
# Philosophy:
#  - existence checked before insert; running twice changes nothing
#  - data lives in ./data/*.json so names can be edited without touching code
#  - CoA / GL-level data is deliberately NOT seeded (see data/company.json)
#  - safe on both a fresh install (after_install) and an existing site (patch)
#
# Manual re-run:
#   bench --site <site> execute aig_custom_theme.setup.seed.run_all

import json
import os

import frappe

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

BASE_CURRENCY = "ETB"


def _load(name):
    with open(os.path.join(DATA_DIR, name), encoding="utf-8") as f:
        return json.load(f)


def log(*a):
    print(*a, flush=True)


# ----------------------------------------------------------------- company
def _ensure_warehouse_types():
    """Warehouse Types are only created by ERPNext's setup wizard; a company
    inserted programmatically (like this seed does) triggers Company.on_update
    -> create_default_warehouses() which auto-creates a 'Transit' warehouse and
    fails its link validation when the type is missing (same gap ERPNext's own
    v13_0/stock_entry_enhancements patch had to close). Existence-guarded."""
    for wt in ("Transit", "Manufacturing", "Receivable"):
        if not frappe.db.exists("Warehouse Type", wt):
            frappe.get_doc({"doctype": "Warehouse Type", "name": wt}).insert(
                ignore_permissions=True
            )
            log(f"  warehouse type created: {wt}")


def seed_company():
    """Create the company if missing. Local CoA (custom AIG v2, 177 accounts)
    is preserved as-is on existing sites; a fresh site starts from ERPNext's
    standard chart of accounts and can adopt the AIG CoA via the documented
    importer chain afterwards (aig-erp-config scripts 80-86)."""
    if not frappe.db.exists("Company", _load("company.json")["company_name"]):
        _ensure_warehouse_types()

    cfg = _load("company.json")
    name = cfg["company_name"]
    if frappe.db.exists("Company", name):
        company = frappe.get_doc("Company", name)
        changed = False
        if not company.default_currency:
            company.default_currency = BASE_CURRENCY
            changed = True
        if changed:
            company.save(ignore_permissions=True)
            log(f"  company '{name}' refreshed currency -> {BASE_CURRENCY}")
        log(f"  company exists: {name}")
        return name

    doc = frappe.new_doc("Company")
    doc.company_name = name
    doc.abbr = cfg["abbr"]
    doc.country = cfg["country"]
    doc.domain = cfg["domain"]
    doc.default_currency = BASE_CURRENCY
    doc.tax_id = cfg.get("tax_id")
    if frappe.get_meta("Company").has_field("allow_multi_currency_invoices"):
        doc.allow_multi_currency_invoices = cfg.get("allow_multi_currency_invoices", 0)
    doc.other_payment_rec = None
    doc.flags.ignore_permissions = True
    doc.insert()
    log(f"  company created: {name} ({BASE_CURRENCY}, standard CoA on fresh sites)")
    return name


def company_name():
    cfg = _load("company.json")
    return cfg["company_name"]


def abbr():
    return _load("company.json")["abbr"]


def company_exists():
    return frappe.db.exists("Company", company_name())


# ------------------------------------------------------------- fiscal years
def _overlapping_fiscal_year(start_date, end_date):
    """Name of an existing fiscal year that covers any part of the range."""
    return frappe.db.get_value(
        "Fiscal Year",
        {
            "year_start_date": ("<=", end_date),
            "year_end_date": (">=", start_date),
        },
        "name",
    )


def seed_fiscal_years():
    # Fiscal Year.validate() rejects overlapping ranges outright, so a site that
    # already has its own fiscal year (ERPNext creates e.g. "2026-2027" for a
    # new company) would abort the whole migrate. Skip what the site already
    # covers instead of fighting site data -- this patch must stay re-runnable
    # on a live database, not just on a fresh one.
    n = 0
    for fy in _load("fiscal_years.json")["fiscal_years"]:
        if frappe.db.exists("Fiscal Year", fy["name"]):
            continue
        overlap = _overlapping_fiscal_year(fy["year_start_date"], fy["year_end_date"])
        if overlap:
            log(
                f"  fiscal year skipped: {fy['name']} overlaps existing {overlap}"
            )
            continue
        frappe.get_doc(
            {
                "doctype": "Fiscal Year",
                "year": fy["name"],
                "year_start_date": fy["year_start_date"],
                "year_end_date": fy["year_end_date"],
            }
        ).insert(ignore_permissions=True)
        log(f"  fiscal year created: {fy['name']}")
        n += 1
    log(f"  fiscal years: {n} created")


# ------------------------------------------------------------- cost centers
def seed_cost_centers():
    data = _load("cost_centers.json")
    company = data["company"]
    root_name = data["root"]["name"]
    created = 0

    if not frappe.db.exists("Company", company):
        log("  cost centers: company missing -- run company seed first")
        return 0

    if not frappe.db.exists("Cost Center", root_name):
        frappe.get_doc(
            {
                "doctype": "Cost Center",
                "cost_center_name": data["root"]["name"].replace(f" - {abbr()}", ""),
                "company": company,
                "is_group": 1,
                "parent_cost_center": None,
            }
        ).insert(ignore_permissions=True)
        log(f"  cost center root created: {root_name}")
        created += 1

    for node in data["nodes"]:
        if frappe.db.exists("Cost Center", node["name"]):
            continue
        parent = node["parent"]
        name_wo_abbr = node["name"].replace(f" - {abbr()}", "")
        frappe.get_doc(
            {
                "doctype": "Cost Center",
                "cost_center_name": name_wo_abbr,
                "company": company,
                "is_group": node["is_group"],
                "parent_cost_center": parent,
            }
        ).insert(ignore_permissions=True)
        created += 1
    log(f"  cost centers: {created} created")


# ---------------------------------------------------------------- warehouses
def seed_warehouses():
    data = _load("warehouses.json")
    company = data["company"]
    root_name = data["root"]["name"]
    created = 0

    if not frappe.db.exists("Company", company):
        log("  warehouses: company missing -- run company seed first")
        return

    if not frappe.db.exists("Warehouse", root_name):
        # ERPNext normally creates this root with the company; create missing only.
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": "All Warehouses",
                "company": company,
                "is_group": 1,
                "parent_warehouse": None,
            }
        ).insert(ignore_permissions=True)
        log(f"  warehouse root created: {root_name}")
        created += 1

    for node in data["nodes"]:
        if frappe.db.exists("Warehouse", node["name"]):
            continue
        frappe.get_doc(
            {
                "doctype": "Warehouse",
                "warehouse_name": node["name"].replace(f" - {abbr()}", ""),
                "company": company,
                "is_group": node["is_group"],
                "parent_warehouse": node["parent"],
            }
        ).insert(ignore_permissions=True)
        created += 1
    log(f"  warehouses: {created} created")


# -------------------------------------------------------------- departments
def seed_departments():
    data = _load("departments.json")
    company = data["company"]
    ab = abbr()
    created = 0
    for d in data["departments"]:
        if frappe.db.exists("Department", f"{d} - {ab}"):
            continue
        # erpnext/hrms Department autoname appends the company abbr.
        frappe.get_doc(
            {
                "doctype": "Department",
                "department_name": d,
                "company": company,
                "parent_department": data["parent_department"],
            }
        ).insert(ignore_permissions=True)
        created += 1
    log(f"  departments: {created} created (under: {data['parent_department']})")


# -------------------------------------------------------------- designations
def seed_designations():
    data = _load("designations.json")
    created = 0
    for d in data["designations"]:
        if frappe.db.exists("Designation", d):
            continue
        frappe.get_doc({"doctype": "Designation", "designation_name": d}).insert(ignore_permissions=True)
        created += 1
    log(f"  designations: {created} created")


# -------------------------------------------------------------------- roles
def seed_roles():
    data = _load("role_map.json")
    created = 0
    for role in data["seed_creates"]:
        if frappe.db.exists("Role", role):
            continue
        d = frappe.new_doc("Role")
        d.role_name = role
        d.desk_access = 1
        # developer guardrails keep the core for System Manager only
        if role.endswith("Developer"):
            d.dont_add_standard_role_permissions = 1
        d.insert(ignore_permissions=True)
        created += 1
    log(f"  roles: {created} created ({', '.join(data['seed_creates'])})")


# ------------------------------------------------------------------ settings
# ------------------------------------------------------------- holiday lists
def seed_holiday_lists():
    """One company-level Holiday List per Gregorian anchor year, covering the
    fixed Ethiopian public holidays. Islamic (Eid) dates are approximate and
    flagged; the user corrects them in Desk once the Hijri calendar is
    announced. Existence-guarded by Holiday List name.
    Conversion anchors: EC 13th month (Pagume) detects leap years: EC 2018
    Pagume=6 -> Gregorian 2026-02-29 inside EC-year span.
    """
    from frappe.utils import getdate

    lists = _load("holiday_lists.json")["holiday_lists"]
    n = 0
    for hl in lists:
        if frappe.db.exists("Holiday List", hl["name"]):
            log(f"  holiday list exists: {hl['name']}")
            continue
        doc = frappe.new_doc("Holiday List")
        doc.holiday_list_name = hl["name"]
        # v16 Holiday List has no is_default field; the data file key is advisory.
        if frappe.get_meta("Holiday List").has_field("is_default"):
            doc.is_default = 1 if hl.get("is_default") else 0
        doc.weekly_off = hl.get("weekly_off")
        doc.company = hl["company"]
        doc.from_date = getdate(hl["from_date"])
        doc.to_date = getdate(hl["to_date"])
        for h in hl["holidays"]:
            doc.append("holidays", {
                "description": h["description"],
                "holiday_date": getdate(h["date"]),
                "weekly_off": 0,
            })
        doc.insert(ignore_permissions=True)
        log(f"  holiday list created: {hl['name']} ({len(hl['holidays'])} holidays)")
        n += 1
    # Existing lists keep their old rows (never rewritten), but the weekly off is
    # reconciled: without it a leave crossing two lists counts Sundays on one
    # side of the boundary and not the other.
    for hl in lists:
        current = frappe.db.get_value("Holiday List", hl["name"], "weekly_off")
        if hl.get("weekly_off") and current != hl["weekly_off"]:
            frappe.db.set_value(
                "Holiday List", hl["name"], "weekly_off", hl["weekly_off"], update_modified=False
            )
            log(f"  holiday list weekly off set: {hl['name']} -> {hl['weekly_off']}")

    # hrms v16 resolves holidays through Holiday List Assignment (docstatus 1)
    # assigned to the employee OR the company; the plain company default field
    # is not consulted. Seed one company-wide assignment per list.
    co = company_name()
    for hl in lists:
        exists = frappe.db.exists(
            "Holiday List Assignment",
            {"assigned_to": co, "holiday_list": hl["name"]},
        )
        if exists:
            doc = frappe.get_doc("Holiday List Assignment", exists)
            if doc.docstatus != 1:
                doc.flags.ignore_permissions = True
                doc.submit()
            continue
        ah = frappe.new_doc("Holiday List Assignment")
        ah.applicable_for = "Company"
        ah.assigned_to = co
        ah.holiday_list = hl["name"]
        ah.from_date = getdate(hl["from_date"])
        ah.flags.ignore_permissions = True
        ah.insert()
        ah.flags.ignore_permissions = True
        ah.submit()
        log(f"  holiday list assignment: company {co} -> {hl['name']}")
    log(f"  holiday lists: {n} created")


def seed_settings():
    if not frappe.get_meta("AIG Minimum ERP Settings").issingle:
        log("  settings doctype missing -- migrate first")
        return
    doc = frappe.get_single("AIG Minimum ERP Settings")

    changed = False
    if not doc.enable_committee:
        doc.enable_committee = 1
        changed = True
    if not doc.purchase_order_threshold:
        doc.purchase_order_threshold = 5000000
        changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save()
    log("  settings: " + ("seeded defaults" if changed else "already set"))


# ------------------------------------------------------------------- main
def run_all(report_only=False):
    frappe.only_for("System Manager")
    if report_only:
        log(f"company exists: {company_exists()}")
        return
    log("=== AIG foundation seed ===")
    seed_company()
    seed_fiscal_years()
    seed_cost_centers()
    seed_warehouses()
    seed_departments()
    seed_designations()
    seed_roles()
    seed_holiday_lists()
    seed_settings()
    log("=== seed complete (idempotent) ===")
