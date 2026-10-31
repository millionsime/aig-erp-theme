# AIG Assigned Committee Member -- child table rows assigned per transaction.
# Decision-edit enforcement lives in aig_custom_theme/committee/guard.py
# (doc-level validate hook), not here: child rows have no meaningful
# per-row permission model of their own.

from frappe.model.document import Document


class AIGAssignedCommitteeMember(Document):
    pass
