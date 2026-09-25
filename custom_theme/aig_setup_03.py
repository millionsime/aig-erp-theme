# AIG config - step 03: demo Budgets.
# Run with: bench --site frontend execute custom_theme.aig_setup_03.run
import frappe
import traceback

COMPANY = "Adama Investment Group"
LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


def get_or_create(dt, filters, values, label):
    name = frappe.db.get_value(dt, filters)
    if name:
        log("EXISTS", f"{label}: {name}")
        return name
    merged = {"doctype": dt}
    merged.update(values)
    try:
        doc = frappe.get_doc(merged)
        doc.insert(ignore_permissions=True)
        log("CREATE", f"{label}: {doc.name}")
        return doc.name
    except Exception:
        print(f"!! FAILED {label}")
        print(traceback.format_exc())
        return None


def cc(name):
    return frappe.db.get_value("Cost Center", {"company": COMPANY, "cost_center_name": name})


COGS = frappe.db.get_value("Account", {"company": COMPANY, "account_name": "Cost of Goods Sold"})
FY = "2026-27"

# Warn-budget: Dairy Farm (main demo) - PO + actual expense
get_or_create("Budget", {"company": COMPANY, "cost_center": cc("Dairy Farm"), "account": COGS}, {
    "doctype": "Budget", "budget_against": "Cost Center", "company": COMPANY,
    "cost_center": cc("Dairy Farm"), "account": COGS, "budget_amount": 2000000,
    "from_fiscal_year": FY, "to_fiscal_year": FY, "distribution_frequency": "Yearly",
    "applicable_on_purchase_order": 1, "action_if_annual_budget_exceeded_on_po": "Warn",
    "action_if_accumulated_monthly_budget_exceeded_on_po": "Warn",
    "applicable_on_booking_actual_expenses": 1, "action_if_annual_budget_exceeded": "Warn",
    "action_if_accumulated_monthly_budget_exceeded": "Warn",
}, "Budget Dairy Farm 2,000,000 (Warn)")

# Warn-budget: Fuel Station (secondary demo)
get_or_create("Budget", {"company": COMPANY, "cost_center": cc("Fuel Station"), "account": COGS}, {
    "doctype": "Budget", "budget_against": "Cost Center", "company": COMPANY,
    "cost_center": cc("Fuel Station"), "account": COGS, "budget_amount": 500000,
    "from_fiscal_year": FY, "to_fiscal_year": FY, "distribution_frequency": "Yearly",
    "applicable_on_purchase_order": 1, "action_if_annual_budget_exceeded_on_po": "Warn",
    "action_if_accumulated_monthly_budget_exceeded_on_po": "Warn",
    "applicable_on_booking_actual_expenses": 1, "action_if_annual_budget_exceeded": "Warn",
    "action_if_accumulated_monthly_budget_exceeded": "Warn",
}, "Budget Fuel Station 500,000 (Warn)")

# Stop-budget: Poultry Farm, deliberately tiny - hard-block demo
get_or_create("Budget", {"company": COMPANY, "cost_center": cc("Poultry Farm"), "account": COGS}, {
    "doctype": "Budget", "budget_against": "Cost Center", "company": COMPANY,
    "cost_center": cc("Poultry Farm"), "account": COGS, "budget_amount": 50000,
    "from_fiscal_year": FY, "to_fiscal_year": FY, "distribution_frequency": "Yearly",
    "applicable_on_purchase_order": 1, "action_if_annual_budget_exceeded_on_po": "Stop",
    "action_if_accumulated_monthly_budget_exceeded_on_po": "Stop",
    "applicable_on_booking_actual_expenses": 1, "action_if_annual_budget_exceeded": "Stop",
    "action_if_accumulated_monthly_budget_exceeded": "Stop",
}, "Budget Poultry Farm 50,000 (Stop)")

frappe.db.commit()
print(f"STEP03_COMPLETE {len(LOG)} actions")
