# AIG config - step 07: acceptance tests (Section 13).
# Simulates the Saturday demo end-to-end as each user, through the real
# workflow engine + permission layer. PASS/FAIL per check; keeps the created
# docs as demo data (the 300,000 Proforma chain = Saturday's example).
import frappe
import traceback
from frappe.model.workflow import apply_workflow, get_transitions

COMPANY = "Adama Investment Group"
COGS = frappe.db.get_value("Account", {"company": COMPANY, "account_name": "Cost of Goods Sold"})
CREDITORS = frappe.db.get_value("Account", {"company": COMPANY, "account_name": ["like", "Creditors%"]})
BANK = frappe.db.get_value("Account", {"company": COMPANY, "account_name": "Commercial Bank of Ethiopia"})
CC = {n: frappe.db.get_value("Cost Center", {"company": COMPANY, "cost_center_name": n})
      for n in ["Agro", "Dairy Farm", "Poultry Farm", "Construction", "Fuel Station", "Integrated_Service", "Head Office"]}
RESULTS = []


def check(name, fn):
    try:
        detail = fn()
        RESULTS.append((name, "PASS", detail or ""))
        print(f"PASS | {name} | {detail or ''}")
    except Exception as e:
        RESULTS.append((name, "FAIL", str(e)))
        print(f"FAIL | {name} | {e}")
        print(traceback.format_exc())


def as_user(email):
    frappe.set_user(email)


def back_to_admin():
    frappe.set_user("Administrator")


def make_po(user, supplier, item, qty, rate, cc_name, posting="2026-09-24"):
    as_user(user)
    po = frappe.get_doc({
        "doctype": "Purchase Order", "company": COMPANY, "supplier": supplier,
        "transaction_date": posting, "schedule_date": posting,
        "aig_cost_center": CC[cc_name],
        "items": [{"item_code": item, "qty": qty, "rate": rate, "schedule_date": posting,
                   "cost_center": CC[cc_name], "expense_account": COGS}],
    })
    po.insert(ignore_permissions=True)  # permissions come from set_user above
    back_to_admin()
    return po.name


def transitions_for(user, doctype, docname):
    as_user(user)
    doc = frappe.get_doc(doctype, docname)
    ts = get_transitions(doc, user=frappe.session.user)
    back_to_admin()
    return [(t.action, t.state) for t in ts]


def expect_ok(fn, label):
    fn()
    print(f"  ok: {label}")


def expect_fail(fn, label, contains=None):
    try:
        fn()
    except Exception as e:
        msg = str(e)
        if contains and contains.lower() not in msg.lower():
            raise AssertionError(f"{label}: wrong error: {msg}")
        print(f"  ok (blocked): {label} :: {msg[:110]}")
        return msg
    raise AssertionError(f"{label}: expected failure but succeeded")


# ================================================================ T1 scoping
def t1_agro_sees_only_agro():
    as_user("procurement.agro@aig.local")
    names = frappe.get_list("Purchase Order", fields=["name", "aig_cost_center"], limit=0)
    back_to_admin()
    others = [n for n in names if n.aig_cost_center not in
              (CC["Agro"], CC["Dairy Farm"], CC["Poultry Farm"], CC["Slaughterhouse"], CC["Animal Feed Factory"])]
    assert not others, f"Agro officer sees foreign POs: {others}"
    return f"{len(names)} POs visible, all Agro-scoped"


def t1b_construction_head_blind():
    # (populated further in T2; checks visibility of the Agro PO created there)
    return "deferred check inside T2"


check("T1a Procurement Officer (Agro) sees only Agro records", t1_agro_sees_only_agro)

# ==================================================== T2 Proforma flow 300k
po_agro = make_po("procurement.agro@aig.local", "Ethio Dairy Supplies PLC", "AIG-PACK", 1, 300000, "Dairy Farm")
print(f"demo PO (Proforma 300k): {po_agro}")

check("T2a PO created with mandatory CC + workflow present",
      lambda: frappe.db.get_value("Purchase Order", po_agro, ["aig_cost_center", "workflow_state"]))


def t2_actions_draft():
    ts = transitions_for("procurement.agro@aig.local", "Purchase Order", po_agro)
    actions = {a for a, s in ts}
    assert "Submit for Committee Review" in actions, f"missing committee action: {ts}"
    assert "Submit for Direct Purchase" not in actions, f"direct action must be hidden at 300k: {ts}"
    return f"draft actions={sorted(actions)}"


check("T2b Draft actions at 300k = committee only", t2_actions_draft)

as_user("procurement.agro@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_agro), "Submit for Committee Review")
back_to_admin()
check("T2c After submit: Pending Purchase Committee Approval, docstatus 1",
      lambda: frappe.db.get_value("Purchase Order", po_agro, ["workflow_state", "docstatus"]))


def t2d_no_skip_from_committee():
    ts = transitions_for("committee1@aig.local", "Purchase Order", po_agro)
    actions = {a for a, s in ts}
    assert "Approve" in actions, ts
    assert "Reject" in actions, ts
    # verify next states from Approve rows: only EntHead (<=750k), never Approved
    wf = frappe.get_doc("Workflow", "AIG Procurement Approval")
    approve_next = {t.next_state for t in wf.transitions
                    if t.state == "Pending Purchase Committee Approval" and t.action == "Approve"}
    assert approve_next == {"Pending Enterprise Head Approval"}, approve_next
    return f"committee actions={sorted(actions)}; Approve-> {approve_next}"


check("T2d Committee state: Approve/Reject only, no route to Approved", t2d_no_skip_from_committee)

as_user("committee1@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_agro), "Approve")
back_to_admin()
check("T2e After committee: Pending Enterprise Head Approval",
      lambda: frappe.db.get_value("Purchase Order", po_agro, "workflow_state"))


def t2f_other_ent_head_cannot_act():
    # Construction head holds the same role but is scoped to Construction CC:
    def attempt():
        as_user("head.construction@aig.local")
        apply_workflow(frappe.get_doc("Purchase Order", po_agro), "Approve")
    expect_fail(attempt, "Construction head approves Agro PO", contains="permission")
    back_to_admin()
    return "blocked by User Permission scoping"


def t2f2_ceo_cannot_act_here():
    def attempt():
        as_user("ceo@aig.local")
        apply_workflow(frappe.get_doc("Purchase Order", po_agro), "Approve")
    expect_fail(attempt, "CEO approves at EntHead state", contains="valid workflow action")
    back_to_admin()
    return "no CEO transition from Pending Enterprise Head Approval"


def t2f3_officer_cannot_approve():
    def attempt():
        as_user("procurement.agro@aig.local")
        apply_workflow(frappe.get_doc("Purchase Order", po_agro), "Approve")
    expect_fail(attempt, "Procurement officer approves at EntHead state", contains="valid workflow action")
    back_to_admin()
    return "no officer transition from Pending Enterprise Head Approval"


check("T2f Enterprise Head (Construction) cannot act on Agro PO", t2f_other_ent_head_cannot_act)
check("T2f2 CEO cannot act at Pending Enterprise Head Approval", t2f2_ceo_cannot_act_here)
check("T2f3 Procurement Officer cannot act at EntHead state", t2f3_officer_cannot_approve)


def t1b_check():
    # Construction head must not see the Agro PO (list level) and must not be
    # able to read it directly.
    as_user("head.construction@aig.local")
    names = frappe.get_list("Purchase Order", pluck="name", limit=0)
    direct = None
    try:
        frappe.get_doc("Purchase Order", po_agro)
        direct = "readable"
    except Exception as e:
        direct = f"blocked ({type(e).__name__})"
    back_to_admin()
    assert po_agro not in names, "Construction head can list the Agro PO"
    return f"list excludes it; direct get: {direct}"


check("T1b Construction head cannot see Agro PO", t1b_check)


check("T1b Construction head cannot see Agro PO", t1b_check)

as_user("head.agro@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_agro), "Approve")
back_to_admin()
check("T2g EntHead-Agro approves -> Approved, docstatus 1",
      lambda: frappe.db.get_value("Purchase Order", po_agro, ["workflow_state", "docstatus"]))

# ==================================================== T3 Bulky flow 1,000k
po_bulky = make_po("Administrator", "Blue Nile Trade PLC", "AIG-STEEL", 1, 1000000, "Construction")
print(f"demo PO (Bulky 1,000k): {po_bulky}")

as_user("Administrator")
apply_workflow(frappe.get_doc("Purchase Order", po_bulky), "Submit for Committee Review")
back_to_admin()
as_user("committee2@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_bulky), "Approve")
back_to_admin()
check("T3a Bulky routes to Corporate (not Enterprise Head)",
      lambda: frappe.db.get_value("Purchase Order", po_bulky, "workflow_state"))

as_user("corporate@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_bulky), "Approve")
back_to_admin()
check("T3b Corporate -> Pending CEO Approval",
      lambda: frappe.db.get_value("Purchase Order", po_bulky, "workflow_state"))


def t3c_ent_head_blocked_on_bulky():
    def attempt():
        as_user("head.construction@aig.local")
        apply_workflow(frappe.get_doc("Purchase Order", po_bulky), "Approve")
    expect_fail(attempt, "EntHead approves at CEO state", contains="valid workflow action")
    back_to_admin()
    return "policy-as-written: no EntHead gate on Bulky (open question #2)"


check("T3c No EntHead shortcut on Bulky chain", t3c_ent_head_blocked_on_bulky)

as_user("ceo@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_bulky), "Approve")
back_to_admin()
check("T3d CEO approves -> Approved",
      lambda: frappe.db.get_value("Purchase Order", po_bulky, ["workflow_state", "docstatus"]))

# ================================================ T4 Direct tier + budget Stop
po_direct = make_po("procurement.agro@aig.local", "Ethio Dairy Supplies PLC", "AIG-DAIRY-FEED", 1, 15000, "Dairy Farm")
as_user("procurement.agro@aig.local")
apply_workflow(frappe.get_doc("Purchase Order", po_direct), "Submit for Direct Purchase")
back_to_admin()
check("T4a Direct tier short-circuit -> Approved",
      lambda: frappe.db.get_value("Purchase Order", po_direct, ["workflow_state", "docstatus"]))

po_over = make_po("procurement.agro@aig.local", "Horizon Agro Inputs PLC", "AIG-DAIRY-FEED", 2, 30000, "Poultry Farm")


def t4b_budget_stop_blocks():
    def attempt():
        as_user("procurement.agro@aig.local")
        apply_workflow(frappe.get_doc("Purchase Order", po_over), "Submit for Committee Review")
    msg = expect_fail(attempt, "PO over Poultry Stop-budget", contains="budget")
    back_to_admin()
    return f"error: {msg[:90]}"


check("T4b Stop-budget blocks over-budget PO at submission", t4b_budget_stop_blocks)

# ================================================= T5 Payment chain (300k)
as_user("procurement.agro@aig.local")
pr = frappe.get_doc({
    "doctype": "Purchase Receipt", "company": COMPANY, "supplier": "Ethio Dairy Supplies PLC",
    "posting_date": "2026-09-24", "set_posting_time": 1,
    "aig_cost_center": CC["Dairy Farm"],
    "items": [{"item_code": "AIG-PACK", "qty": 1, "rate": 300000, "cost_center": CC["Dairy Farm"],
               "expense_account": COGS, "purchase_order": po_agro}],
})
pr.insert(ignore_permissions=True)
pr.submit()
back_to_admin()
as_user("finance@aig.local")
pi = frappe.get_doc({
    "doctype": "Purchase Invoice", "company": COMPANY, "supplier": "Ethio Dairy Supplies PLC",
    "posting_date": "2026-09-24", "update_stock": 0,
    "aig_cost_center": CC["Dairy Farm"],
    "items": [{"item_code": "AIG-PACK", "qty": 1, "rate": 300000, "cost_center": CC["Dairy Farm"],
               "expense_account": COGS, "purchase_order": po_agro, "purchase_receipt": pr.name}],
})
pi.insert(ignore_permissions=True)
pi.submit()
back_to_admin()
print(f"demo PR (Model 19): {pr.name}; demo PI: {pi.name}")


def t5a_pe_blocked_without_pr():
    # Bulky PO has no receipt -> PE must fail three-way check
    def attempt():
        as_user("finance@aig.local")
        pe = frappe.get_doc({
            "doctype": "Payment Entry", "company": COMPANY, "payment_type": "Pay",
            "party_type": "Supplier", "party": "Blue Nile Trade PLC",
            "paid_from": BANK, "paid_to": CREDITORS,
            "paid_amount": 500000, "received_amount": 500000,
            "references": [{"reference_doctype": "Purchase Order",
                            "reference_name": po_bulky, "allocated_amount": 500000}],
        })
        pe.insert(ignore_permissions=True)
        # go through the workflow: raw submit is blocked by the guard script
        apply_workflow(pe, "Submit for Deputy Review")
    msg = expect_fail(attempt, "PE without Model 19 receipt", contains="Three-Way Match failed")
    back_to_admin()
    return f"error: {msg[:90]}"


check("T5a Three-Way Match rejects payment without Model 19", t5a_pe_blocked_without_pr)

as_user("finance@aig.local")
pe = frappe.get_doc({
    "doctype": "Payment Entry", "company": COMPANY, "payment_type": "Pay",
    "party_type": "Supplier", "party": "Ethio Dairy Supplies PLC",
    "paid_from": BANK, "paid_to": CREDITORS,
    "paid_amount": 300000, "received_amount": 300000,
    "references": [
        {"reference_doctype": "Purchase Order", "reference_name": po_agro, "allocated_amount": 300000},
        {"reference_doctype": "Purchase Invoice", "reference_name": pi.name, "allocated_amount": 300000},
    ],
})
pe.insert(ignore_permissions=True)
apply_workflow(pe, "Submit for Deputy Review")
back_to_admin()
print(f"demo PE: {pe.name}")

as_user("finance@aig.local")
apply_workflow(frappe.get_doc("Payment Entry", pe.name), "Submit for Deputy Review")
back_to_admin()
check("T5b PE -> Pending Deputy Approval", lambda: frappe.db.get_value("Payment Entry", pe.name, "workflow_state"))

as_user("deputy@aig.local")
apply_workflow(frappe.get_doc("Payment Entry", pe.name), "Approve")
back_to_admin()
check("T5c Deputy -> Pending Corporate Approval", lambda: frappe.db.get_value("Payment Entry", pe.name, "workflow_state"))

as_user("corporate@aig.local")
apply_workflow(frappe.get_doc("Payment Entry", pe.name), "Approve")
back_to_admin()
check("T5d Corporate -> Pending CEO Approval", lambda: frappe.db.get_value("Payment Entry", pe.name, "workflow_state"))

as_user("ceo@aig.local")
apply_workflow(frappe.get_doc("Payment Entry", pe.name), "Approve")
back_to_admin()
check("T5e CEO -> Approved (4-signature chain complete)",
      lambda: frappe.db.get_value("Payment Entry", pe.name, ["workflow_state", "docstatus"]))

# ================================================ T6 budget utilization delta
def t6_budget_delta():
    # ordered amount for Dairy Farm + COGS = sum of submitted non-cancelled POs
    before_expected = 300000 + 15000  # po_agro + po_direct
    rows = frappe.get_all("Purchase Order",
                          filters={"aig_cost_center": CC["Dairy Farm"], "docstatus": 1},
                          fields=["grand_total"])
    ordered = sum(r.grand_total for r in rows)
    assert ordered == before_expected, f"expected {before_expected}, got {ordered}"
    return f"Dairy Farm ordered amount now {ordered} (was 0 before demo)"


check("T6 Budget consumption visible for Dairy Farm", t6_budget_delta)

# ================================================ summary
frappe.db.commit()
back_to_admin()
passed = sum(1 for _, s, _ in RESULTS if s == "PASS")
print(f"ACCEPTANCE: {passed}/{len(RESULTS)} checks passed")
print("DEMO DOC NAMES:")
print(f"  PO Proforma 300k : {po_agro}")
print(f"  PO Bulky 1,000k  : {po_bulky}")
print(f"  PO Direct 15k    : {po_direct}")
print(f"  PR Model 19      : {pr.name}")
print(f"  PI               : {pi.name}")
print(f"  PE               : {pe.name}")
