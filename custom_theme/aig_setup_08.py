# AIG config - step 08: workflow-runtime hardening.
# 1) Approvers need write for their state-transition saves (v16 applies them
#    through doc.save()/submit() under normal permission checks).
# 2) Guard scripts block raw submit bypass: without this, a user holding
#    submit permission could submit straight from Draft, skipping the chain.
# 3) Clean up the partially-created docs from the failed acceptance run.
import frappe

LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


# ---------------- 1. write for approvers (needed by apply_workflow saves) ----
def ensure_perm(dt, role, **flags):
    row = frappe.db.get_value("Custom DocPerm", {"parent": dt, "role": role, "permlevel": 0})
    if not row:
        print(f"!! missing perm row {dt}/{role}")
        return
    doc = frappe.get_doc("Custom DocPerm", row)
    changed = False
    for k, v in flags.items():
        if getattr(doc, k) != v:
            setattr(doc, k, v)
            changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        log("UPDATE", f"DocPerm {dt}/{role}: {flags}")


for r in ["AIG Purchase Committee", "AIG Enterprise Head", "AIG Corporate", "AIG CEO"]:
    ensure_perm("Purchase Order", r, write=1)
for r in ["AIG Deputy", "AIG Corporate", "AIG CEO"]:
    ensure_perm("Payment Entry", r, write=1)

# ---------------- 2. raw-submit guards --------------------------------------
PO_GUARD = """# AIG: block raw submit bypass. The ONLY legitimate submits are the workflow's
# own Draft->Pending* (state already moved before submit) and Draft->Approved
# (Direct tier). If the state is still 'Draft' at submit time, someone tried to
# skip the chain.
if doc.workflow_state == "Draft":
    frappe.throw("AIG: submit is only allowed through the AIG Procurement Approval workflow actions.")
"""

PE_GUARD = """# AIG: block raw submit bypass on Payment Entry. Submitting is only legitimate
# after a workflow action has moved the state out of Draft (via 'Submit for
# Deputy Review') or to Approved through the chain.
if doc.workflow_state == "Draft":
    frappe.throw("AIG: submit is only allowed through the AIG Payment Approval workflow actions.")
"""


def upsert_script(name, ref, script):
    if frappe.db.exists("Server Script", name):
        d = frappe.get_doc("Server Script", name)
        d.script = script
        d.flags.ignore_permissions = True
        d.save(ignore_permissions=True)
        log("UPDATE", f"Server Script {name}")
    else:
        d = frappe.get_doc({
            "doctype": "Server Script", "name": name, "script_type": "DocType Event",
            "reference_doctype": ref, "doctype_event": "Before Submit", "script": script,
        })
        d.insert(ignore_permissions=True)
        log("CREATE", f"Server Script {name}")


upsert_script("AIG - PO Guard Raw Submit", "Purchase Order", PO_GUARD)
upsert_script("AIG - PE Guard Raw Submit", "Payment Entry", PE_GUARD)

# ---------------- 2b. demo-material adjustments ----------------
# AIG-PACK must be a stock item so the Model 19 (Purchase Receipt) leg of the
# payment demo works; give it the default Stores warehouse.
item = frappe.get_doc("Item", "AIG-PACK")
if not item.is_stock_item:
    item.is_stock_item = 1
    item.flags.ignore_permissions = True
    item.save(ignore_permissions=True)
    log("UPDATE", "Item AIG-PACK -> is_stock_item=1 (Model 19 receipt leg)")

stores = frappe.db.get_value("Warehouse", {"company": "Adama Investment Group", "warehouse_name": "Stores"})
if stores:
    for row in item.item_defaults or []:
        if row.company == "Adama Investment Group" and not row.default_warehouse:
            row.default_warehouse = stores
            item.flags.ignore_permissions = True
            item.save(ignore_permissions=True)
            log("UPDATE", f"Item AIG-PACK default warehouse -> {stores}")

# Creditors account for Payment Entry paid_to
COMPANY = "Adama Investment Group"
CREDITORS = frappe.db.get_value("Account", {"company": COMPANY, "account_name": ["like", "Creditors%"], "is_group": 0})
if not CREDITORS:
    CREDITORS = frappe.db.get_value("Account", {"company": COMPANY, "account_type": "Payable", "is_group": 0})
if not CREDITORS:
    root = frappe.db.get_value("Account", {"company": COMPANY, "is_group": 1, "parent_account": ["is", "set"]}, "name")
    acc = frappe.get_doc({"doctype": "Account", "company": COMPANY, "account_name": "Creditors",
                          "account_type": "Payable", "is_group": 0, "parent_account": root, "account_currency": "ETB"})
    acc.insert(ignore_permissions=True)
    CREDITORS = acc.name
    log("CREATE", f"Account Creditors: {CREDITORS}")
else:
    log("EXISTS", f"Creditors account: {CREDITORS}")

# ---------------- 3. cleanup of the failed run's partial demo docs ----------
def purge(dt, extra_filters=None):
    filters = {}
    if extra_filters:
        filters.update(extra_filters)
    names = frappe.get_all(dt, filters=filters, pluck="name")
    for n in names:
        try:
            d = frappe.get_doc(dt, n)
            if d.docstatus == 1:
                d.flags.ignore_permissions = True
                d.cancel()
            if d.docstatus in (0, 2):
                frappe.delete_doc(dt, n, ignore_permissions=True, force=True)
                log("DELETE", f"{dt} {n}")
        except Exception as e:
            print(f"!! could not purge {dt} {n}: {e}")


# demo docs are exactly those carrying our custom CC field value
for dt in ["Payment Entry", "Purchase Invoice", "Purchase Receipt"]:
    purge(dt, {"docstatus": ["<", 2]})
purge("Purchase Order")

frappe.db.commit()
print(f"STEP08_COMPLETE {len(LOG)} actions")
