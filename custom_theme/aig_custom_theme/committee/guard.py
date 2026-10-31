# Committee assignment guard (§2.8 — deliberately code, not workflow conditions:
# workflow conditions cannot reliably check "is the user in this document's list").
#
# Hook: Quality Inspection / Purchase Order / Request for Quotation validate.
#
# Rules:
#  - committee members are ordinary employees assigned per transaction on the
#    `aig_assigned_committee_members` child table (DocType: AIG Assigned
#    Committee Member). Assigning roles: Store Keeper/Expert on QI, Purchaser
#    on PO/RFQ;
#  - only a user whose Employee is on a row may record/update that row's
#    decision (or System Manager);
#  - the amount threshold lives on the AIG Minimum ERP Settings single.

import frappe
from frappe import _

CHILD_FIELD = "aig_assigned_committee_members"
ASSIGNING_ROLES = {
    "Quality Inspection": ["AIG Store Keeper", "AIG Store Expert", "AIG Store Manager"],
    "Purchase Order": ["AIG Procurement Officer", "AIG Procurement Director"],
    "Request for Quotation": ["AIG Procurement Officer", "AIG Procurement Director"],
}


def _session_employee():
    if frappe.session.user in ("Guest",):
        return None
    return frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name")


def _is_admin():
    return "System Manager" in frappe.get_roles()


def _settings():
    return frappe.get_single("AIG Minimum ERP Settings")


def _old_rows(doc):
    return {
        r.name: r
        for r in frappe.get_all(
            "AIG Assigned Committee Member",
            filters={"parent": doc.name, "parenttype": doc.doctype},
            fields=["name", "employee", "decision", "comment", "decided_on"],
        )
    }


def validate(doc, method=None):
    if not _settings().enable_committee:
        return

    rows = doc.get(CHILD_FIELD) or []
    if not rows:
        _threshold_hint(doc)
        return

    me = _session_employee()
    admin = _is_admin()
    assign_ok = admin or bool(set(ASSIGNING_ROLES.get(doc.doctype, [])) & set(frappe.get_roles()))

    old_rows = {} if doc.get("__islocal") else _old_rows(doc)

    for row in rows:
        old = old_rows.get(row.name)

        # 1) adding a member row on a SAVED document needs the assigning role
        if old is None and not doc.get("__islocal") and not assign_ok:
            # row is new but parent already saved: only assigning roles manage members
            frappe.throw(
                _("AIG: role {0} may not assign committee members on {1}.").format(
                    frappe.session.user, doc.name
                ),
                frappe.PermissionError,
            )

        # 2) recording a decision requires being that row's employee
        if row.decision and row.decision not in ("", "Pending") and not (admin or (me and me == row.employee)):
            frappe.throw(
                _("AIG: only assigned committee member '{0}' may record this decision.").format(row.employee),
                frappe.PermissionError,
            )

        # 3) editing an already recorded decision likewise
        if old is not None and old.employee and not (admin or (me and me == old.employee)):
            changed = (
                old.decision != row.decision
                or old.comment != row.comment
                or old.decided_on != row.get("decided_on")
            )
            if changed:
                frappe.throw(
                    _("AIG: only assigned committee member '{0}' may change decision row '{1}'.").format(
                        old.employee, row.name
                    ),
                    frappe.PermissionError,
                )

        # stamp decided_on on first decision
        if row.decision and row.decision not in ("", "Pending") and not row.decided_on:
            row.decided_on = frappe.utils.today()

    _threshold_hint(doc)


def _threshold_hint(doc):
    if doc.doctype not in ("Purchase Order", "Request for Quotation"):
        return
    s = _settings()
    threshold = s.purchase_order_threshold or 0
    if not threshold:
        return
    base = flt_base(doc)
    if base > threshold:
        frappe.msgprint(
            _("AIG: amount {0} exceeds the committee threshold ({1}) - assign committee members.").format(
                frappe.utils.fmt_money(base, currency=doc.get("currency") or "ETB"),
                frappe.utils.fmt_money(threshold),
            ),
            indicator="orange",
            alert=True,
        )


def flt_base(doc):
    try:
        return float(doc.get("base_grand_total") or doc.get("grand_total") or 0)
    except (TypeError, ValueError):
        return 0.0
