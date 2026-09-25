# AIG config - step 04 patch:
# 1) Rewrite the Payment Three-Way Match server script (PE references cannot
#    include Purchase Receipts, so Model 19 is verified by querying submitted
#    Purchase Receipt Items linked to the referenced POs).
# 2) Grant submit to Procurement Officer (PO) and Finance (PE): the workflow
#    Draft->pending transition performs the doc submission.
import frappe

LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


THREE_WAY_V2 = """# AIG Three-Way Match (Payment Entry, Before Submit) - v2
# Checks, in order:
# 1) payment_type must be Pay
# 2) at least one Purchase Order reference (allocated > 0)
# 3) at least one Purchase Invoice reference with non-zero allocation
# 4) paid_amount reconciles with the invoice allocation (tolerance: 0.5%, min 10 ETB)
# 5) EVERY referenced Purchase Order has at least one SUBMITTED Purchase Receipt
#    (Model 19, via Purchase Receipt Item.purchase_order) - amounts reconcile by
#    construction because the PO allocation is capped by the PO total.
if doc.payment_type != "Pay":
    frappe.throw("AIG Three-Way Match: only 'Pay' payments follow the AIG approval chain.")

po_names = []
pi_total = 0.0
has_pi = False
for r in (doc.references or []):
    if r.reference_doctype == "Purchase Order" and (r.allocated_amount or 0) > 0:
        if r.reference_name not in po_names:
            po_names.append(r.reference_name)
    elif r.reference_doctype == "Purchase Invoice":
        has_pi = True
        pi_total += (r.allocated_amount or 0)

paid = doc.paid_amount or 0
problems = []
if not po_names:
    problems.append("no Purchase Order reference")
if not has_pi:
    problems.append("no Purchase Invoice reference")
if not pi_total:
    problems.append("Purchase Invoice allocation is zero")
if problems:
    frappe.throw("AIG Three-Way Match failed: " + "; ".join(problems))

def _tol(x):
    return max(10, 0.005 * abs(x))

if abs(pi_total - paid) > _tol(pi_total):
    frappe.throw("AIG Three-Way Match failed: paid {0} vs invoice allocation {1} mismatch.".format(paid, pi_total))

for po in po_names:
    rows = frappe.db.get_all("Purchase Receipt Item",
                             filters={"purchase_order": po, "docstatus": 1},
                             fields=["parent"])
    if not rows:
        frappe.throw("AIG Three-Way Match failed: no submitted Purchase Receipt (Model 19) for Purchase Order {0}.".format(po))
"""

ss = frappe.get_doc("Server Script", "AIG - Payment Three-Way Match")
ss.script = THREE_WAY_V2
ss.flags.ignore_permissions = True
ss.save(ignore_permissions=True)
log("UPDATE", "Server Script AIG - Payment Three-Way Match -> v2 (Model 19 via PR Items)")


def ensure_perm(dt, role, **flags):
    row_name = frappe.db.get_value("Custom DocPerm", {"dt": dt, "role": role, "permlevel": 0})
    if not row_name:
        print(f"!! no base perm row for {dt}/{role}")
        return
    doc = frappe.get_doc("Custom DocPerm", row_name)
    changed = False
    for k, v in flags.items():
        if getattr(doc, k) != v:
            setattr(doc, k, v)
            changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save(ignore_permissions=True)
        log("UPDATE", f"DocPerm {dt}/{role}: {flags}")


ensure_perm("Purchase Order", "AIG Procurement Officer", submit=1)
ensure_perm("Payment Entry", "AIG Finance", submit=1)

frappe.db.commit()
print(f"STEP04_COMPLETE {len(LOG)} actions")
