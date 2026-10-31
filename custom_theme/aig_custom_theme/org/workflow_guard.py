# AIG Leave Approval workflow enforcement (§2.7).
#
# The Workflow fixture carries roles + conditions, but workflow transition
# conditions cannot be trusted alone for two rules, so this hook is the
# authoritative guard (registered as Leave Application validate):
#
#  1. nobody may approve their own application (leave_approver == owner
#     is rejected always, even in Draft);
#  2. stepping out of "Pending Closest Boss" requires the session user to BE
#     the application's leave_approver (closest-boss-only rule), unless the
#     CEO path applies (AIG Leave Approval workflow transitions the HR
#     Director's own leave to "Approved" and "CEO" may do that);
#  3. HR Director's leave jumps Pending Closest Boss -> Approved on CEO
#     approval - state handled purely by the Workflow fixture.

import frappe
from frappe import _

CLOSEST_BOSS_STATE = "Pending Closest Boss"
HR_NEXT_STATE = "Pending HR Expert"
APPROVED_STATE = "Approved"


def _owner_is_approver(doc):
    # owner of the Leave Application is the applying employee's user
    return doc.leave_approver == doc.owner


def validate(doc, method=None):
    user = frappe.session.user

    if _owner_is_approver(doc):
        frappe.throw(
            _("AIG: self-approval is not allowed - '{0}' is both applicant "
              "and Leave Approver.").format(user),
            frappe.PermissionError,
        )

    if doc.is_new():
        return

    # state-transition interception (workflow actions save through here)
    new_state = doc.get("workflow_state")
    if not new_state or new_state == "Draft":
        return

    old_state = frappe.db.get_value("Leave Application", doc.name, "workflow_state")
    if old_state == new_state:
        return  # ordinary field edit, transition engine handles approval rules

    if old_state == CLOSEST_BOSS_STATE and user != "Administrator":
        ceo_ok = _ceo_path(doc, user, new_state)
        boss_ok = user == doc.leave_approver
        if not (boss_ok or ceo_ok):
            frappe.throw(
                _("AIG: only the application's closest boss ({0}) may approve "
                  "at 'Pending Closest Boss'.").format(doc.leave_approver),
                frappe.PermissionError,
            )
        # closest boss cannot approve their own application (already guaranteed
        # above via owner check, kept explicit here for workflow-fixture drift)
        if boss_ok and _owner_is_approver(doc):
            frappe.throw(_("AIG: self-approval is not allowed."), frappe.PermissionError)


def _ceo_path(doc, user, new_state):
    """HR Director's own leave: the CEO is their closest boss and their
    approval goes straight to Approved."""
    if new_state != APPROVED_STATE:
        return False
    applicant = frappe.db.get_value("Employee", {"user_id": doc.owner}, "name")
    if not applicant:
        return False
    # the applicant (not the approver) must be an HR Director; the actor must be the CEO
    applicant_user = doc.owner
    return "AIG HR Director" in frappe.get_roles(applicant_user) and "AIG CEO" in frappe.get_roles(user)
