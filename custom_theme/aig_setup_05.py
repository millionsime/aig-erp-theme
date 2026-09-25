# AIG config - step 05: repair Custom DocPerm rows.
# v16 renamed Custom DocPerm.dt -> parent ("Reference Document Type").
# Step-02 rows were created with dt=..., leaving parent NULL => engine-invisible.
# This script deletes only those orphaned rows (created by this same build, never
# effective) and recreates the full permission matrix with parent set correctly.
import frappe

LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


# 1) drop orphans (rows with no parent doctype - artifacts of step 02)
orphans = frappe.get_all("Custom DocPerm",
                         filters=[["parent", "is", "not set"]],
                         pluck="name")
orphans += frappe.get_all("Custom DocPerm", filters={"parent": ""}, pluck="name")
for name in set(orphans):
    frappe.delete_doc("Custom DocPerm", name, ignore_permissions=True)
log("DELETE", f"{len(set(orphans))} orphaned Custom DocPerm rows (parent NULL, created by step 02)")


def perm(dt, role, read=0, write=0, create=0, submit=0, cancel=0, amend=0, permlevel=0):
    filters = {"parent": dt, "role": role, "permlevel": permlevel}
    if frappe.db.exists("Custom DocPerm", filters):
        log("EXISTS", f"DocPerm {dt}/{role}/L{permlevel}")
        return
    doc = frappe.get_doc({
        "doctype": "Custom DocPerm", "parent": dt, "role": role, "permlevel": permlevel,
        "read": 1 if read else 0, "write": 1 if write else 0, "create": 1 if create else 0,
        "submit": 1 if submit else 0, "cancel": 1 if cancel else 0, "amend": 1 if amend else 0,
    })
    doc.insert(ignore_permissions=True)
    log("CREATE", f"DocPerm {dt} -> {role} (L{permlevel})")


ALL_AIG = ["AIG Procurement Officer", "AIG Evaluation Committee", "AIG Purchase Committee",
           "AIG Enterprise Head", "AIG Corporate", "AIG CEO", "AIG Finance", "AIG Deputy"]
APPROVERS = ["AIG Purchase Committee", "AIG Enterprise Head", "AIG Corporate", "AIG CEO"]

# Purchase Order
perm("Purchase Order", "AIG Procurement Officer", read=1, write=1, create=1, submit=1, amend=1)
for r in APPROVERS:
    perm("Purchase Order", r, read=1, submit=1, cancel=1)
perm("Purchase Order", "AIG Finance", read=1)

# Payment Entry
perm("Payment Entry", "AIG Finance", read=1, write=1, create=1, submit=1, cancel=1, amend=1)
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

frappe.db.commit()
print(f"STEP05_COMPLETE {len(LOG)} actions")
