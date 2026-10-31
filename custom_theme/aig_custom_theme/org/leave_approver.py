# Leave Approver automation (§2.7).
#
# Hook: Employee validate (registered in hooks.py doc_events).
#
# Rule: the closest boss approves - we derive Leave Approver strictly from the
# Employee's Reports To chain. Cost Center is an independent Employee field
# and must never be touched here (financial dimension ≠ reporting chain).
#
# If the reports-to employee has no linked user we warn clearly (not silently)
# and leave the existing leave_approver untouched.

import frappe
from frappe import _

COMPANY_USER_FIELD = "user_id"


def _closest_reports_to(employee_name):
    return frappe.db.get_value("Employee", employee_name, "reports_to")


def set_leave_approver(doc, method=None):
    """Auto-fill doc.leave_approver from doc.reports_to on Employee validate."""
    if not doc.reports_to:
        # No manager in the chain: do not invent one. Warn only when the field
        # would otherwise be empty on an active employee.
        if not doc.leave_approver and doc.status == "Active":
            frappe.msgprint(
                _(
                    "AIG: '{0}' has no Reports To, so a closest-boss Leave "
                    "Approver could not be derived. Set the Leave Approver "
                    "manually until the reporting chain exists."
                ).format(doc.name),
                indicator="orange",
                alert=True,
            )
        return

    if doc.reports_to == doc.name:
        frappe.throw(
            _("AIG: '{0}' cannot report to themselves.").format(doc.name)
        )

    approver_user = frappe.db.get_value("Employee", doc.reports_to, COMPANY_USER_FIELD)
    if approver_user:
        doc.leave_approver = approver_user
    else:
        frappe.msgprint(
            _(
                "AIG: reports-to employee '{0}' has no linked login user, so "
                "the Leave Approver could not be set automatically. Link a "
                "user to that employee or set the Leave Approver manually."
            ).format(doc.reports_to),
            indicator="orange",
            alert=True,
        )
