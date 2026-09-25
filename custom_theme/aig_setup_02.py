# AIG config - step 02: workflows, custom field, server scripts, doc perms.
# Run with: bench --site frontend execute custom_theme.aig_setup_02.run
# Everything here is data-level (Workflow/Custom Field/Custom DocPerm/Server Script) - no core edits.
# Frappe v16 schema: Workflow.states -> "Workflow Document State" rows (state links to
# Workflow State master, doc_status on the row); transitions -> "Workflow Transition" rows.
import frappe
import traceback

COMPANY = "Adama Investment Group"
LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


def insert_doc(values, label):
    doc = frappe.get_doc(values)
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


# ============================== 1. Custom field: PO cost center (mandatory) ==
get_or_create("Custom Field", {"dt": "Purchase Order", "fieldname": "aig_cost_center"}, {
    "doctype": "Custom Field", "dt": "Purchase Order", "fieldname": "aig_cost_center",
    "label": "AIG Cost Center", "fieldtype": "Link", "options": "Cost Center",
    "reqd": 1, "insert_after": "company", "in_list_view": 1, "in_standard_filter": 1,
}, "Custom Field PO aig_cost_center")

# =========================================== 2. Workflow State / Action masters ==
for state_name in ["Draft", "Pending Purchase Committee Approval", "Pending Enterprise Head Approval",
                   "Pending Corporate Approval", "Pending CEO Approval", "Pending Deputy Approval",
                   "Approved", "Rejected"]:
    get_or_create("Workflow State", {"workflow_state_name": state_name}, {
        "doctype": "Workflow State", "workflow_state_name": state_name,
    }, f"Workflow State {state_name}")

for action in ["Submit for Committee Review", "Submit for Direct Purchase", "Submit for Deputy Review",
               "Approve", "Reject"]:
    get_or_create("Workflow Action Master", {"workflow_action_name": action}, {
        "doctype": "Workflow Action Master", "workflow_action_name": action,
    }, f"Workflow Action Master {action}")

# ================================================== 3. Workflow #1: Purchase Order ==
# Pending states are docstatus 1 (PO submits when entering committee review):
# v16 forbids Draft(0) -> Rejected(2), so rejection happens from submitted states only.
# allow_edit is mandatory per state (v16): pending state = its acting role;
# terminal states = System Manager only, so no AIG role can edit approved/rejected docs.
PO_STATES = [
    {"state": "Draft", "doc_status": "0", "allow_edit": "AIG Procurement Officer"},
    {"state": "Pending Purchase Committee Approval", "doc_status": "1", "allow_edit": "AIG Purchase Committee"},
    {"state": "Pending Enterprise Head Approval", "doc_status": "1", "allow_edit": "AIG Enterprise Head"},
    {"state": "Pending Corporate Approval", "doc_status": "1", "allow_edit": "AIG Corporate"},
    {"state": "Pending CEO Approval", "doc_status": "1", "allow_edit": "AIG CEO"},
    {"state": "Approved", "doc_status": "1", "allow_edit": "System Manager"},
    {"state": "Rejected", "doc_status": "2", "allow_edit": "System Manager"},
]
PO_TRANSITIONS = [
    {"state": "Draft", "action": "Submit for Direct Purchase", "next_state": "Approved",
     "allowed": "AIG Procurement Officer", "condition": "doc.grand_total < 20000"},
    {"state": "Draft", "action": "Submit for Committee Review", "next_state": "Pending Purchase Committee Approval",
     "allowed": "AIG Procurement Officer", "condition": "doc.grand_total >= 20000"},
    {"state": "Pending Purchase Committee Approval", "action": "Approve", "next_state": "Pending Enterprise Head Approval",
     "allowed": "AIG Purchase Committee", "condition": "doc.grand_total <= 750000"},
    {"state": "Pending Purchase Committee Approval", "action": "Approve", "next_state": "Pending Corporate Approval",
     "allowed": "AIG Purchase Committee", "condition": "doc.grand_total > 750000"},
    {"state": "Pending Purchase Committee Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG Purchase Committee", "condition": None},
    {"state": "Pending Enterprise Head Approval", "action": "Approve", "next_state": "Approved",
     "allowed": "AIG Enterprise Head", "condition": None},
    {"state": "Pending Enterprise Head Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG Enterprise Head", "condition": None},
    {"state": "Pending Corporate Approval", "action": "Approve", "next_state": "Pending CEO Approval",
     "allowed": "AIG Corporate", "condition": None},
    {"state": "Pending Corporate Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG Corporate", "condition": None},
    {"state": "Pending CEO Approval", "action": "Approve", "next_state": "Approved",
     "allowed": "AIG CEO", "condition": None},
    {"state": "Pending CEO Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG Forbidden Attempt", "condition": None},
]
# fix the deliberate trap row (no such role exists; kept for explicitness)
PO_TRANSITIONS = [t for t in PO_TRANSITIONS if t["allowed"] != "AIG Forbidden Attempt"]
PO_TRANSITIONS.append({"state": "Pending CEO Approval", "action": "Reject", "next_state": "Rejected",
                       "allowed": "AIG CEO", "condition": None})


def build_po_workflow():
    name = "AIG Procurement Approval"
    if frappe.db.exists("Workflow", name):
        log("EXISTS", f"Workflow {name}")
        return
    insert_doc({
        "doctype": "Workflow",
        "workflow_name": name,
        "document_type": "Purchase Order",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "override_status": 1,
        "send_email_alert": 0,
        "states": [{"state": s["state"], "doc_status": s["doc_status"], "allow_edit": s["allow_edit"]}
                   for s in PO_STATES],
        "transitions": [{"state": t["state"], "action": t["action"], "next_state": t["next_state"],
                         "allowed": t["allowed"], "condition": t.get("condition") or None}
                        for t in PO_TRANSITIONS],
    }, f"Workflow {name}")


build_po_workflow()

# ============================================== 4. Workflow #2: Payment Entry ==
PE_STATES = [
    {"state": "Draft", "doc_status": "0", "allow_edit": "AIG Finance"},
    {"state": "Pending Deputy Approval", "doc_status": "1", "allow_edit": "AIG Deputy"},
    {"state": "Pending Corporate Approval", "doc_status": "1", "allow_edit": "AIG Corporate"},
    {"state": "Pending CEO Approval", "doc_status": "1", "allow_edit": "AIG CEO"},
    {"state": "Approved", "doc_status": "1", "allow_edit": "System Manager"},
    {"state": "Rejected", "doc_status": "2", "allow_edit": "System Manager"},
]
PE_TRANSITIONS = [
    {"state": "Draft", "action": "Submit for Deputy Review", "next_state": "Pending Deputy Approval",
     "allowed": "AIG Finance", "condition": None},
    {"state": "Pending Deputy Approval", "action": "Approve", "next_state": "Pending Corporate Approval",
     "allowed": "AIG Deputy", "condition": None},
    {"state": "Pending Deputy Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG Deputy", "condition": None},
    {"state": "Pending Corporate Approval", "action": "Approve", "next_state": "Pending CEO Approval",
     "allowed": "AIG Corporate", "condition": None},
    {"state": "Pending Corporate Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG Corporate", "condition": None},
    {"state": "Pending CEO Approval", "action": "Approve", "next_state": "Approved",
     "allowed": "AIG CEO", "condition": None},
    {"state": "Pending CEO Approval", "action": "Reject", "next_state": "Rejected",
     "allowed": "AIG CEO", "condition": None},
]


def build_pe_workflow():
    name = "AIG Payment Approval"
    if frappe.db.exists("Workflow", name):
        log("EXISTS", f"Workflow {name}")
        return
    insert_doc({
        "doctype": "Workflow",
        "workflow_name": name,
        "document_type": "Payment Entry",
        "workflow_state_field": "workflow_state",
        "is_active": 1,
        "override_status": 1,
        "send_email_alert": 0,
        "states": PE_STATES,
        "transitions": [{"state": t["state"], "action": t["action"], "next_state": t["next_state"],
                         "allowed": t["allowed"], "condition": t.get("condition") or None}
                        for t in PE_TRANSITIONS],
    }, f"Workflow {name}")


build_pe_workflow()

# ================================================ 5. Server scripts ==
THREE_WAY = """# AIG Three-Way Match (Payment Entry, Before Submit)
# Enforces: PO + Purchase Receipt (Model 19) + Purchase Invoice all referenced,
# and their allocated amounts reconcile within 0.5% (min 10 ETB tolerance).
if doc.payment_type != "Pay":
    frappe.throw("AIG Three-Way Match: only 'Pay' payments follow the AIG approval chain.")

po_total = pr_total = pi_total = 0.0
has_po = has_pr = has_pi = False
for r in (doc.references or []):
    if r.reference_doctype == "Purchase Order":
        has_po = True
        po_total += (r.allocated_amount or 0)
    elif r.reference_doctype == "Purchase Receipt":
        has_pr = True
        pr_total += (r.allocated_amount or 0)
    elif r.reference_doctype == "Purchase Invoice":
        has_pi = True
        pi_total += (r.allocated_amount or 0)

problems = []
if not has_pi:
    problems.append("no Purchase Invoice reference (supplier invoice)")
if not has_po:
    problems.append("no Purchase Order reference")
if not has_pr:
    problems.append("no Purchase Receipt reference (Model 19)")
if problems:
    frappe.throw("AIG Three-Way Match failed: " + "; ".join(problems))

def _tol(x):
    return max(10, 0.005 * abs(x))

if abs(po_total - pi_total) > _tol(po_total):
    frappe.throw("AIG Three-Way Match failed: PO {0} vs Invoice {1} mismatch.".format(po_total, pi_total))
if pr_total and abs(pr_total - pi_total) > _tol(pi_total):
    frappe.throw("AIG Three-Way Match failed: Receipt {0} vs Invoice {1} mismatch.".format(pr_total, pi_total))
"""

PO_CC_DEFAULT = """# AIG: default the mandatory AIG Cost Center on Purchase Order.
# Order: first item cost_center -> creating user's User Permission -> company default.
if not doc.get("aig_cost_center"):
    cc = None
    for item in (doc.items or []):
        if item.get("cost_center"):
            cc = item.get("cost_center")
            break
    if not cc:
        cc = frappe.db.get_value("User Permission",
                                 {"user": frappe.session.user, "allow": "Cost Center"},
                                 "for_value")
    if not cc:
        cc = frappe.db.get_value("Company", doc.company, "cost_center")
    if cc:
        doc.set("aig_cost_center", cc)
for item in (doc.items or []):
    if not item.get("cost_center") and doc.get("aig_cost_center"):
        item.cost_center = doc.get("aig_cost_center")
"""

get_or_create("Server Script", {"name": "AIG - PO Cost Center Default"}, {
    "doctype": "Server Script", "name": "AIG - PO Cost Center Default",
    "script_type": "DocType Event", "reference_doctype": "Purchase Order",
    "doctype_event": "Before Save", "script": PO_CC_DEFAULT,
}, "Server Script AIG - PO Cost Center Default")

get_or_create("Server Script", "AIG - Payment Three-Way Match", {
    "doctype": "Server Script", "name": "AIG - Payment Three-Way Match",
    "script_type": "DocType Event", "reference_doctype": "Payment Entry",
    "doctype_event": "Before Submit", "script": THREE_WAY,
}, "Server Script AIG - Payment Three-Way Match")

# ================================================ 6. Custom DocPerms ==
def perm(dt, role, read=0, write=0, create=0, submit=0, cancel=0, amend=0, permlevel=0):
    filters = {"dt": dt, "role": role, "permlevel": permlevel}
    if frappe.db.exists("Custom DocPerm", filters):
        log("EXISTS", f"DocPerm {dt}/{role}/L{permlevel}")
        return
    insert_doc({"doctype": "Custom DocPerm", "dt": dt, "role": role, "permlevel": permlevel,
                "read": read, "write": 1 if write else 0, "create": 1 if create else 0,
                "submit": 1 if submit else 0, "cancel": 1 if cancel else 0,
                "amend": 1 if amend else 0},
               f"DocPerm {dt} -> {role} (L{permlevel})")


ALL_AIG = ["AIG Procurement Officer", "AIG Evaluation Committee", "AIG Purchase Committee",
           "AIG Enterprise Head", "AIG Corporate", "AIG CEO", "AIG Finance", "AIG Deputy"]
APPROVERS = ["AIG Purchase Committee", "AIG Enterprise Head", "AIG Corporate", "AIG CEO"]

# Purchase Order
perm("Purchase Order", "AIG Procurement Officer", read=1, write=1, create=1, amend=1)
for r in APPROVERS:
    perm("Purchase Order", r, read=1, submit=1, cancel=1)
perm("Purchase Order", "AIG Finance", read=1)

# Payment Entry
perm("Payment Entry", "AIG Finance", read=1, write=1, create=1, cancel=1, amend=1)
for r in ["AIG Deputy", "AIG Corporate", "AIG CEO"]:
    perm("Payment Entry", r, read=1, submit=1, cancel=1)

# Procurement chain
for dt in ["Material Request", "Request for Quotation", "Supplier Quotation"]:
    perm(dt, "AIG Procurement Officer", read=1, write=1, create=1, submit=1, amend=1)
    perm(dt, "AIG Enterprise Head", read=1)
perm("Purchase Receipt", "AIG Procurement Officer", read=1, write=1, create=1, submit=1, amend=1)
for dt in ["Purchase Receipt", "Purchase Invoice"]:
    for r in ["AIG Enterprise Head", "AIG Corporate", "AIG CEO", "AIG Finance", "AIG Deputy", "AIG Purchase Committee"]:
        perm(dt, r, read=1)
perm("Purchase Invoice", "AIG Finance", read=1, write=1, create=1, submit=1, cancel=1, amend=1)

# Masters
for dt in ["Item", "Supplier", "Cost Center"]:
    for r in ALL_AIG:
        perm(dt, r, read=1)
for r in ["AIG Finance", "AIG Procurement Officer", "AIG Corporate"]:
    perm("Account", r, read=1)

# Budget
perm("Budget", "AIG Enterprise Head", read=1)
perm("Budget", "AIG Procurement Officer", read=1)
perm("Budget", "AIG Finance", read=1, write=1, create=1)
perm("Budget", "AIG Corporate", read=1, write=1)

# Supplier banking (permlevel 1)
for r in ["AIG Finance", "AIG Corporate", "AIG CEO", "AIG Deputy"]:
    perm("Supplier", r, read=1, write=1, permlevel=1)

# ================================================ 7. Supplier banking field ==
get_or_create("Custom Field", {"dt": "Supplier", "fieldname": "aig_bank_details"}, {
    "doctype": "Custom Field", "dt": "Supplier", "fieldname": "aig_bank_details",
    "label": "AIG Banking Details (restricted)", "fieldtype": "Small Text",
    "permlevel": 1, "insert_after": "tax_id",
}, "Custom Field Supplier aig_bank_details (permlevel 1)")

frappe.db.commit()
print(f"STEP02_COMPLETE {len(LOG)} actions")
