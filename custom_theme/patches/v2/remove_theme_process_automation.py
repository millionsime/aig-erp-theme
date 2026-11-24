"""Take process automation out of the theme (Nov 2026).

The theme shipped AIG's approval workflows and Server/Client Scripts as
fixtures. Business processes now live in their own apps (aig_finance,
aig_stock, aig_assets, aig_hr, ...), so the theme keeps branding only.
Removing a record from a fixture file never deletes it from a site, so this
patch deletes exactly the records the theme shipped, by name. Records owned by
other apps (aig_hr's ORG-* scripts, for example) are not in these lists and
are not touched.

Documents already in a workflow keep their workflow_state value as plain text;
with the workflow gone they save and submit the normal ERPNext way.
"""

import frappe

SERVER_SCRIPTS = [
 "AIG - PO Cost Center Default",
 "AIG - Payment Three-Way Match",
 "AIG - PO Guard Raw Submit",
 "AIG - PE Guard Raw Submit",
 "AIG - Item Duplicate Name Warning",
 "AIG - MR Request Defaults",
 "AIG - MR Approval Guard",
 "AIG - SE Movement Defaults",
 "AIG - SE Receiving Inspection Gate",
 "AIG - SE Guard Raw Submit",
 "AIG - SE Issue Validation",
 "AIG - MR Item Cost Center Sync",
 "AIG - SE Item Cost Center Sync",
 "AIG - CC Guard Journal Entry",
 "AIG - CC Guard Payment Entry",
 "AIG - CC Guard Sales Invoice",
 "AIG - CC Guard Purchase Invoice",
 "AIG - Migration Batch Validation",
 "AIG - MR End User Type Guard",
 "AIG - MR End User Type Default",
 "AIG - MR Stock Item Guard",
 "AIG - SE CC Normalize",
 "AIG - MR CC Normalize",
 "AIG - Item Auto Code",
 "AIG - CS Guard",
 "AIG - PO Committee Majority",
 "AIG - Model 42 Guard",
 "AIG - Payment Withholding 7.5% + 3%",
 "AIG - PO Committee Reject Guard",
 "AIG - MR End User Purchase Scope"
]

CLIENT_SCRIPTS = [
 "AIG - Ethiopic Date (Purchase Order)",
 "AIG - Ethiopic Date (Journal Entry)",
 "AIG - Ethiopic Date (Payment Entry)",
 "AIG - Ethiopic Date (Attendance)",
 "AIG - Row CC Scrub (Stock Entry)",
 "AIG - Row CC Scrub (Material Request)",
 "AIG - Row CC Scrub (Purchase Order)",
 "AIG - MR Default Type (End User)",
 "AIG - SE CC Intercept",
 "AIG - MR CC Intercept",
 "AIG - Item Code Auto Hint"
]

WORKFLOWS = [
 "AIG Procurement Approval",
 "AIG Payment Approval",
 "AIG Stock Request Approval",
 "AIG Store Receiving",
 "AIG Leave Approval"
]


def _delete(doctype, names):
	for name in names:
		if frappe.db.exists(doctype, name):
			frappe.delete_doc(doctype, name, force=True, ignore_permissions=True, ignore_missing=True)


def execute():
	_delete("Workflow", WORKFLOWS)
	_delete("Server Script", SERVER_SCRIPTS)
	_delete("Client Script", CLIENT_SCRIPTS)
	frappe.clear_cache()
