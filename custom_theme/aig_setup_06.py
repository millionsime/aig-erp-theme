# AIG config - step 06: role-scoped Workspaces + remaining read perms (Section 7/9).
import frappe

LOG = []


def log(what, detail):
    LOG.append(f"{what}: {detail}")
    print(f"### {what}: {detail}")


def perm(dt, role, permlevel=0):
    if frappe.db.exists("Custom DocPerm", {"parent": dt, "role": role, "permlevel": permlevel}):
        return
    doc = frappe.get_doc({"doctype": "Custom DocPerm", "parent": dt, "role": role,
                          "permlevel": permlevel, "read": 1})
    doc.insert(ignore_permissions=True)
    log("CREATE", f"DocPerm {dt} -> {role} (L{permlevel}, read)")


# Section 7: Corporate/CEO/Finance read across the procurement chain
for r in ["AIG Corporate", "AIG CEO", "AIG Finance"]:
    for dt in ["Material Request", "Request for Quotation", "Supplier Quotation", "Purchase Receipt"]:
        perm(dt, r)

# ------------------------------- Workspaces (Section 9: module scoping) ----
def ws(label, module, roles, for_user=None, is_hidden=0):
    filters = {"label": label}
    if frappe.db.exists("Workspace", filters):
        log("EXISTS", f"Workspace {label}")
        return
    doc = frappe.get_doc({
        "doctype": "Workspace", "label": label, "title": label, "module": module,
        "public": 0, "for_user": for_user or "", "is_hidden": is_hidden,
        "content": "[]", "parent_page": "",
        "roles": [{"role": r} for r in roles],
    })
    doc.insert(ignore_permissions=True)
    log("CREATE", f"Workspace {label} roles={roles} for_user={for_user or '-'}")


# Demo workspaces (private, role-gated)
ws("AIG Procurement", "Buying", ["AIG Procurement Officer"])
ws("AIG Approvals", "Buying", ["AIG Purchase Committee", "AIG Enterprise Head", "AIG Corporate", "AIG CEO"])
ws("AIG Finance", "Accounts", ["AIG Finance", "AIG Deputy"])

frappe.db.commit()
print(f"STEP06_COMPLETE {len(LOG)} actions")
