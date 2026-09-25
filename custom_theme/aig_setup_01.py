# AIG config - step 01: fiscal year, accounts, withholding categories,
# cost center tree, demo masters, roles, users, user permissions.
# Additive only; every action printed for the change log.
# Run with: bench --site frontend execute custom_theme.aig_setup_01.run
import frappe
import traceback

COMPANY = "Adama Investment Group"
LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


def exists(dt, name):
    return frappe.db.exists(dt, name)


def insert_doc(values, label):
    doc = frappe.get_doc(values)
    doc.flags.ignore_permissions = True
    try:
        doc.insert(ignore_permissions=True)
        log("CREATE", f"{label}: {doc.name}")
        return doc.name
    except Exception:
        print(f"!! FAILED {label}")
        print(traceback.format_exc())
        return None


def get_or_create(dt, filters, values, label):
    name = frappe.db.get_value(dt, filters)
    if name:
        log("EXISTS", f"{label}: {name}")
        return name
    merged = {"doctype": dt}
    merged.update(values)
    return insert_doc(merged, label)


# ---------------------------------------------------------------- fiscal year
fy_name = "2026-27"
if not exists("Fiscal Year", fy_name):
    fy = frappe.get_doc({
        "doctype": "Fiscal Year",
        "year": fy_name,
        "year_start_date": "2026-07-08",
        "year_end_date": "2027-07-07",
        "fy_companies": [{"company": COMPANY}],
    })
    fy.flags.ignore_permissions = True
    fy.insert(ignore_permissions=True)
    log("CREATE", f"Fiscal Year: {fy_name} (2026-07-08 .. 2027-07-07)")
else:
    log("EXISTS", f"Fiscal Year: {fy_name}")
FY_START, FY_END = "2026-07-08", "2027-07-07"

# ------------------------------------------------------------------- accounts
root_acc = frappe.db.get_value("Account", {"company": COMPANY, "is_group": 1, "parent_account": ["is", "set"]}, "name") or None
root_acc = frappe.db.get_value("Account", {"company": COMPANY, "account_name": "Application of Funds", "is_group": 1}, "name")
if not root_acc:
    root_acc = frappe.db.get_value("Account", {"company": COMPANY, "is_group": 1}, "name", order_by="lft")
log("INFO", f"account root parent: {root_acc}")

duties = frappe.db.get_value("Account", {"company": COMPANY, "account_name": ["like", "%Duties and Taxes%"]})
if duties:
    tax_parent = duties
else:
    tax_parent = insert_doc({
        "doctype": "Account", "company": COMPANY, "account_name": "Duties and Taxes",
        "account_type": "Tax", "is_group": 1, "parent_account": root_acc, "account_currency": "ETB",
    }, "Account group Duties and Taxes")

acc_cbe = get_or_create("Account", {"company": COMPANY, "account_name": "Commercial Bank of Ethiopia"}, {
    "doctype": "Account", "company": COMPANY, "account_name": "Commercial Bank of Ethiopia",
    "account_type": "Bank", "is_group": 0, "parent_account": root_acc, "account_currency": "ETB",
}, "Bank account CBE")

acc_wht = get_or_create("Account", {"company": COMPANY, "account_name": "3% Withholding Tax Payable"}, {
    "doctype": "Account", "company": COMPANY, "account_name": "3% Withholding Tax Payable",
    "account_type": "Tax", "is_group": 0, "parent_account": tax_parent, "account_currency": "ETB",
}, "3% WHT account")

acc_vatwh = get_or_create("Account", {"company": COMPANY, "account_name": "7.5% VAT Withholding Payable"}, {
    "doctype": "Account", "company": COMPANY, "account_name": "7.5% VAT Withholding Payable",
    "account_type": "Tax", "is_group": 0, "parent_account": tax_parent, "account_currency": "ETB",
}, "7.5% VAT W/H account")

get_or_create("Account", {"company": COMPANY, "account_name": "VAT Receivable"}, {
    "doctype": "Account", "company": COMPANY, "account_name": "VAT Receivable",
    "account_type": "Tax", "is_group": 0, "parent_account": tax_parent, "account_currency": "ETB",
}, "VAT Receivable account")

# ------------------------------------------------- tax withholding categories
twh_3 = get_or_create("Tax Withholding Category", {"category_name": "AIG 3% Withholding Tax"}, {
    "doctype": "Tax Withholding Category", "name": "AIG 3% Withholding Tax",
    "category_name": "AIG 3% Withholding Tax", "tax_deduction_basis": "Gross Total",
    "rates": [{"from_date": FY_START, "to_date": FY_END, "tax_withholding_rate": 3,
               "single_threshold": 0, "cumulative_threshold": 0}],
    "accounts": [{"company": COMPANY, "account": acc_wht}],
}, "Tax Withholding Category 3% WHT")

twh_75 = get_or_create("Tax Withholding Category", {"category_name": "AIG 7.5% VAT Withholding"}, {
    "doctype": "Tax Withholding Category", "name": "AIG 7.5% VAT Withholding",
    "category_name": "AIG 7.5% VAT Withholding", "tax_deduction_basis": "Gross Total",
    "rates": [{"from_date": FY_START, "to_date": FY_END, "tax_withholding_rate": 7.5,
               "single_threshold": 0, "cumulative_threshold": 0}],
    "accounts": [{"company": COMPANY, "account": acc_vatwh}],
}, "Tax Withholding Category 7.5% VAT W/H")

# Purchase Taxes and Charges Template per AIG policy:
# 15% VAT charged on invoice; 7.5% VAT W/H and 3% WHT withheld at payment stage.
# For the demo we provide two templates: VAT-only (procurement) and
# VAT + withholdings (invoice template) so Finance can apply policy exactly.
tpt_vat = get_or_create("Purchase Taxes and Charges Template", {"title": "AIG VAT 15% (Purchase)"}, {
    "doctype": "Purchase Taxes and Charges Template",
    "title": "AIG VAT 15% (Purchase)",
    "company": COMPANY,
    "is_default": 0,
    "taxes": [{"category": "Total", "add_deduct_tax": "Add", "charge_type": "On Net Total",
               "account_head": frappe.db.get_value("Account", {"company": COMPANY, "account_name": "VAT Receivable"}),
               "rate": 15, "description": "VAT 15%"}],
}, "Purchase template AIG VAT 15%")

# ------------------------------------------------------------ cost center tree
# The brief's Section 3 shows Agro/Integrated Service/Construction as parents.
# Existing CCs are leaves; flipping is_group is the minimal change that allows
# the documented children (structure/parents unchanged - flagged in change log).
def cc(name):
    return frappe.db.get_value("Cost Center", {"company": COMPANY, "cost_center_name": name})


for ent in ["Agro", "Integrated_Service", "Construction"]:
    p = frappe.get_doc("Cost Center", cc(ent))
    if not p.is_group:
        p.is_group = 1
        p.flags.ignore_permissions = True
        p.save(ignore_permissions=True)
        log("UPDATE", f"Cost Center {ent} -> is_group=1 (to host enterprise children)")


children = {
    "Agro": ["Dairy Farm", "Poultry Farm", "Slaughterhouse", "Animal Feed Factory"],
    "Integrated_Service": ["Fuel Station", "City Mall", "Guaraj (Garage)", "Parking", "Cafeteria and Parks"],
}
for parent_name, kids in children.items():
    p = cc(parent_name)
    if not p:
        print(f"!! parent cost center missing: {parent_name}")
        continue
    for kid in kids:
        get_or_create("Cost Center", {"company": COMPANY, "cost_center_name": kid}, {
            "doctype": "Cost Center", "cost_center_name": kid, "company": COMPANY,
            "parent_cost_center": p, "is_group": 0,
        }, f"Cost Center {kid}")
get_or_create("Cost Center", {"company": COMPANY, "cost_center_name": "Head Office"}, {
    "doctype": "Cost Center", "cost_center_name": "Head Office", "company": COMPANY,
    "parent_cost_center": frappe.db.get_value("Cost Center", {"company": COMPANY, "cost_center_name": "Adama Investment Group"}),
    "is_group": 0,
}, "Cost Center Head Office")

CC = {k: cc(k) for k in ["Agro", "Dairy Farm", "Poultry Farm", "Slaughterhouse", "Animal Feed Factory",
                         "Integrated_Service", "Fuel Station", "City Mall", "Guaraj (Garage)", "Parking",
                         "Cafeteria and Parks", "Construction", "Head Office"]}
log("INFO", f"CC map: {CC}")

# ------------------------------------------------------------- demo masters
uom = get_or_create("UOM", {"uom_name": "Nos"}, {"doctype": "UOM", "uom_name": "Nos"}, "UOM Nos")
ig = get_or_create("Item Group", {"item_group_name": "AIG Procurement"}, {
    "doctype": "Item Group", "item_group_name": "AIG Procurement",
    "parent_item_group": "All Item Groups", "is_group": 0,
}, "Item Group AIG Procurement")
sg = get_or_create("Supplier Group", {"supplier_group_name": "AIG Vendors"}, {
    "doctype": "Supplier Group", "supplier_group_name": "AIG Vendors", "is_group": 0,
}, "Supplier Group AIG Vendors")

for item_code, item_name, rate in [
    ("AIG-DAIRY-FEED", "Dairy Feed Supplement", 30000),
    ("AIG-PACK", "Milk Packaging Materials", 300000),
    ("AIG-STEEL", "Construction Steel Profile", 900000),
    ("AIG-FUEL-EQUIP", "Fuel Station Pump Equipment", 400000),
]:
    get_or_create("Item", {"item_code": item_code}, {
        "doctype": "Item", "item_code": item_code, "item_name": item_name,
        "item_group": ig or "All Item Groups", "stock_uom": uom or "Nos",
        "is_stock_item": 0, "is_purchase_item": 1, "is_fixed_asset": 0,
        "item_defaults": [{"company": COMPANY,
                           "expense_account": frappe.db.get_value("Account", {"company": COMPANY, "account_name": "Cost of Goods Sold"})}],
    }, f"Item {item_code}")

for sup in ["Ethio Dairy Supplies PLC", "Horizon Agro Inputs PLC", "Blue Nile Trade PLC"]:
    get_or_create("Supplier", {"supplier_name": sup}, {
        "doctype": "Supplier", "supplier_name": sup, "supplier_type": "Company",
        "supplier_group": sg or "All Supplier Groups",
    }, f"Supplier {sup}")

# ------------------------------------------------------------------- roles
ROLES = ["AIG Procurement Officer", "AIG Evaluation Committee", "AIG Purchase Committee",
         "AIG Enterprise Head", "AIG Corporate", "AIG CEO", "AIG Finance", "AIG Deputy"]
for r in ROLES:
    get_or_create("Role", {"role_name": r}, {"doctype": "Role", "role_name": r, "desk_access": 1}, f"Role {r}")

# ------------------------------------------------------------------- users
USERS = [
    ("procurement.agro@aig.local", "Procurement Officer - Agro", ["AIG Procurement Officer"], None),
    ("committee1@aig.local", "Purchase Committee Member 1", ["AIG Purchase Committee"], None),
    ("committee2@aig.local", "Purchase Committee Member 2", ["AIG Purchase Committee"], None),
    ("committee3@aig.local", "Purchase Committee Member 3", ["AIG Purchase Committee"], None),
    ("head.agro@aig.local", "Enterprise Head - Agro", ["AIG Enterprise Head"], "Agro"),
    ("head.construction@aig.local", "Enterprise Head - Construction", ["AIG Enterprise Head"], "Construction"),
    ("head.service@aig.local", "Enterprise Head - Integrated Service", ["AIG Enterprise Head"], "Integrated_Service"),
    ("corporate@aig.local", "Corporate - Head Office", ["AIG Corporate"], None),
    ("ceo@aig.local", "CEO - AIG", ["AIG CEO"], None),
    ("finance@aig.local", "Finance - Head Office", ["AIG Finance"], None),
    ("deputy@aig.local", "Deputy - Head Office", ["AIG Deputy"], None),
]
CC_CHILDREN = {
    "Agro": ["Agro", "Dairy Farm", "Poultry Farm", "Slaughterhouse", "Animal Feed Factory"],
    "Integrated_Service": ["Integrated_Service", "Fuel Station", "City Mall", "Guaraj (Garage)", "Parking", "Cafeteria and Parks"],
    "Construction": ["Construction"],
}

for email, full, roles, cc_key in USERS:
    if not exists("User", email):
        u = frappe.get_doc({
            "doctype": "User", "email": email, "first_name": full,
            "enabled": 1, "user_type": "System User", "new_password": "aig2026",
            "send_welcome_email": 0, "language": "en",
        })
        u.flags.ignore_permissions = True
        u.insert(ignore_permissions=True)
        log("CREATE", f"User {email} ({full}) password=aig2026")
    else:
        log("EXISTS", f"User {email}")
    u = frappe.get_doc("User", email)
    u.flags.ignore_permissions = True
    have = {r.role for r in u.roles or []}
    for r in roles + ["Desk User"]:
        if r not in have:
            u.append("roles", {"role": r})
            log("ASSIGN", f"Role {r} -> {email}")
    u.save(ignore_permissions=True)
    # enterprise scoping via User Permission on Cost Center (parent + children)
    if cc_key:
        for kid in CC_CHILDREN[cc_key]:
            val = CC.get(kid)
            if not val:
                continue
            if not exists("User Permission", {"user": email, "allow": "Cost Center", "for_value": val}):
                insert_doc({"doctype": "User Permission", "user": email,
                            "allow": "Cost Center", "for_value": val},
                           f"UserPermission {email} CC={val}")
    else:
        log("INFO", f"{email}: no CC restriction (cross-enterprise by design)")

# ------------------------------------------------------- bank for payment demo
bank = get_or_create("Bank", {"bank_name": "Commercial Bank of Ethiopia"},
                     {"doctype": "Bank", "bank_name": "Commercial Bank of Ethiopia"}, "Bank CBE")
if bank and not exists("Bank Account", {"bank": bank, "company": COMPANY, "account": acc_cbe}):
    insert_doc({"doctype": "Bank Account", "bank": bank, "company": COMPANY,
                "account": acc_cbe, "bank_account_no": "1000123456789",
                "account_name": "AIG Operating CBE",
                "bank_account_name": "Adama Investment Group - Operating"},
               "Bank Account CBE Operating")


def run():
    """Entry point for `bench execute`. Idempotent."""
    frappe.db.commit()
    print(f"\n=== STEP01 COMPLETE, {len(LOG)} actions ===")
    return len(LOG)
