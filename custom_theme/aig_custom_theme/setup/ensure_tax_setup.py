# Rebuild the AIG tax configuration that was deliberately removed from the
# fixtures set (see hooks.py): the tax templates and withholding categories
# hardwire CoA-2.0 account names (21402 / 21401 / 21403) that only exist after
# the AIG CoA importer chain runs (aig-erp-config scripts 80-86). Importing
# them as fixtures before that aborts every fresh install.
#
# Run this ONCE after the CoA import on any site:
#   bench --site <site> execute aig_custom_theme.setup.ensure_tax_setup.run
#
# Idempotent: existing records keep their names, tax row sets are reset to the
# canonical single row, rate windows are extended only when they end before
# today. Safe also on a site still on the standard CoA: AIG account lookups
# fail and the whole run becomes a no-op with a clear message.

import copy

import frappe

COMPANY = "Adama Investment Group"
VAT15_KEY = "21402"
VATWH_KEY = "21401"
WHT3_KEY = "21403"
COST_CENTER = "Head Office - AIG"

# canonical rows, identical to the former fixture payload
SALES_TEMPLATE = {
    "title": "Ethiopia Tax",
    "taxes": [dict(
        charge_type="On Net Total", category="Total", add_deduct_tax="Add",
        rate=15, description="VAT 15%", is_tax_withholding_account=0,
        allocate_full_amount_to_stock_items=1,
    )],
}
PURCHASE_TEMPLATE = copy.deepcopy(SALES_TEMPLATE)

TWC_CATEGORIES = [
    dict(
        name="AIG 7.5% VAT Withholding",
        rate=7.5,
        account_key=VATWH_KEY,
        tax_deduction_basis="Gross Total",
    ),
    dict(
        name="AIG 3% Withholding Tax",
        rate=3,
        account_key=WHT3_KEY,
        tax_deduction_basis="Gross Total",
    ),
]

# rate windows are refreshed so a year-old import never needs re-running
RATE_WINDOW_DAYS = 365


def log(*a):
    print(*a, flush=True)


def _account(key):
    return frappe.db.get_value(
        "Account", {"company": COMPANY, "account_number": key}, "name"
    )


def ensure_tax_templates():
    vat15 = _account(VAT15_KEY)
    if not vat15:
        log("  AIG CoA not present yet - skipping tax templates")
        return False
    cc = frappe.db.get_value("Cost Center", {"company": COMPANY, "cost_center_name": COST_CENTER}, "name") \
        or (COST_CENTER if frappe.db.exists("Cost Center", f"{COST_CENTER} - AIG") else None)
    for dt, cfg in (
        ("Sales Taxes and Charges Template", SALES_TEMPLATE),
        ("Purchase Taxes and Charges Template", PURCHASE_TEMPLATE),
    ):
        tpl = frappe.db.exists(dt, {"name": "Ethiopia Tax - AIG", "company": COMPANY})
        if not tpl:
            doc = frappe.new_doc(dt)
            doc.name = "Ethiopia Tax - AIG"
            doc.company = COMPANY
            created = True
        else:
            doc = frappe.get_doc(dt, tpl)
            created = False
        doc.title = cfg["title"]
        doc.disabled = 0
        doc.set("taxes", [])
        for row in cfg["taxes"]:
            row = dict(row)
            row["account_head"] = vat15
            row["cost_center"] = cc
            doc.append("taxes", row)
        doc.flags.ignore_permissions = True
        doc.save()
        log(f"  {'created' if created else 'refreshed'} {dt}: 1 row -> {vat15}")
    return True


def ensure_twc_categories():
    import datetime

    if not all(_account(c["account_key"]) for c in TWC_CATEGORIES):
        missing = [c["name"] for c in TWC_CATEGORIES if not _account(c["account_key"])]
        log(f"  AIG CoA accounts missing for {', '.join(missing)} - skipping TWCs")
        return False

    today = frappe.utils.getdate(frappe.utils.today())
    new_to = today + datetime.timedelta(days=RATE_WINDOW_DAYS)
    new_from = new_to - datetime.timedelta(days=RATE_WINDOW_DAYS)

    for cat in TWC_CATEGORIES:
        acc = _account(cat["account_key"])
        doc = (
            frappe.get_doc("Tax Withholding Category", cat["name"])
            if frappe.db.exists("Tax Withholding Category", cat["name"])
            else frappe.new_doc("Tax Withholding Category")
        )
        doc.category_name = cat["name"]
        doc.tax_deduction_basis = cat["tax_deduction_basis"]
        doc.disable_transaction_threshold = 0
        doc.disable_cumulative_threshold = 0
        doc.round_off_tax_amount = 0
        doc.tax_on_excess_amount = 0
        doc.set("accounts", [])
        doc.append("accounts", {"company": COMPANY, "account": acc})
        if doc.get("rates"):
            r = doc.rates[-1]
            if not r.to_date or frappe.utils.getdate(r.to_date) < today:
                r.from_date = new_from
                r.to_date = new_to
        else:
            doc.append("rates", dict(
                tax_withholding_rate=cat["rate"],
                single_threshold=0,
                cumulative_threshold=0,
                from_date=new_from,
                to_date=new_to,
            ))
        doc.flags.ignore_permissions = True
        doc.save()
        log(f"  TWC {cat['name']}: -> {acc} (rate {cat['rate']}%)")
    return True


def run():
    log("=" * 60)
    log("AIG tax setup (post CoA-import wiring)")
    ok_templates = ensure_tax_templates()
    ok_twcs = ensure_twc_categories()
    log("=" * 60)
    if ok_templates and ok_twcs:
        log("DONE: tax templates + withholding categories are current")
    else:
        log("DONE with skips (see above): import the AIG CoA first (aig-erp-config scripts 80-86), then re-run this")
    return {"templates": ok_templates, "twcs": ok_twcs}
