# AIG Admin Dashboard controller (www page /aig-admin).
# Custom admin view for Adama Investment Group - deliberately NOT the
# default Frappe desk home. Server-computed aggregates (no client API
# calls, no external chart libs): KPI cards, PO distribution, MR states,
# approval pipeline, needs-attention table, 12-week committed-spend trend,
# top suppliers.
import json

import frappe
from frappe.utils import cint, now_datetime

COMPANY = "Adama Investment Group"

PO_CHAIN = [
    "Draft", "Pending Committee Signoff", "Pending Finance Signoff",
    "Pending Enterprise Head Approval", "Pending Corporate Approval",
    "Pending CEO Approval", "Approved", "Rejected",
]
MR_HOT = ["Pending Store Review", "Pending Enterprise Head Endorsement"]
PO_HOT = ["Pending Committee Signoff", "Pending Finance Signoff",
          "Pending Enterprise Head Approval", "Pending Corporate Approval",
          "Pending CEO Approval"]

BADGES = {
    "Pending Committee Signoff": "b-committee",
    "Pending Finance Signoff": "b-finance",
    "Pending Enterprise Head Approval": "b-committee",
    "Pending Corporate Approval": "b-committee",
    "Pending CEO Approval": "b-committee",
    "Approved": "b-approved",
    "Draft": "b-draft",
    "Pending Store Review": "b-review",
    "Pending Enterprise Head Endorsement": "b-review",
    "Endorsed": "b-endorsed",
    "Rejected": "b-rejected",
}


def _fmt(v):
    return "{:,.0f}".format(cint(v))


def _count_by_state(doctype):
    c = {}
    for r in frappe.get_all(doctype, fields=["workflow_state"],
                            limit_page_length=0):
        s = r.workflow_state or "Draft"
        c[s] = c.get(s, 0) + 1
    return c


def get_context(context):
    user = frappe.session.user
    if user in ("Guest",):
        frappe.redirect("/login?redirect-to=/aig-admin")
    roles = set(frappe.get_roles())
    if not (roles & {"System Manager", "AIG Internal Auditor"}):
        frappe.redirect("/me")

    # ---- KPIs ----
    mr_states = _count_by_state("Material Request")
    po_states = _count_by_state("Purchase Order")
    po_rows = frappe.get_all("Purchase Order",
                             fields=["grand_total", "workflow_state",
                                     "transaction_date", "supplier"],
                             limit_page_length=0)
    po_value = sum((r.grand_total or 0) for r in po_rows)
    open_mr = sum(n for s, n in mr_states.items()
                  if s not in ("Approved", "Rejected"))
    chain = set(PO_CHAIN) - {"Draft", "Approved", "Rejected"}
    po_review = sum(n for s, n in po_states.items() if s in chain)

    kpi = {
        "mr_count": sum(mr_states.values()),
        "mr_open": open_mr,
        "po_count": sum(po_states.values()),
        "po_review": po_review,
        "po_value": round(po_value, 2),
        "po_value_fmt": _fmt(po_value),
        "pe_count": frappe.db.count("Payment Entry"),
        "supplier_count": frappe.db.count("Supplier"),
        "item_count": frappe.db.count("Item"),
        "user_count": frappe.db.count("User", {"enabled": 1}),
    }

    # ---- PO distribution (skip empty stages for the donut) ----
    po_by_state = [{"state": s, "count": po_states.get(s, 0)}
                   for s in PO_CHAIN]
    po_by_state = [p for p in po_by_state if p["count"]]

    # ---- MR bars (all states, ordered by count desc) ----
    mr_by_state = sorted(
        ({"state": s, "count": n, "count_fmt": str(n)}
         for s, n in mr_states.items()),
        key=lambda x: -x["count"])

    # ---- pipeline (full chain order, may include zeros) ----
    pipeline = [{"state": s, "count": po_states.get(s, 0)}
                for s in PO_CHAIN]

    # ---- needs attention ----
    pending = []
    for r in frappe.get_all("Purchase Order",
                            filters={"workflow_state": ["in", PO_HOT]},
                            fields=["name", "supplier", "grand_total",
                                    "workflow_state"],
                            order_by="modified desc", limit_page_length=8):
        pending.append({
            "doctype": "Purchase Order", "name": r.name,
            "supplier": r.supplier, "state": r.workflow_state,
            "value_fmt": _fmt(r.grand_total),
            "badge": BADGES.get(r.workflow_state, "b-generic"),
        })
    for r in frappe.get_all("Material Request",
                            filters={"workflow_state": ["in", MR_HOT]},
                            fields=["name", "aig_estimated_total",
                                    "workflow_state"],
                            order_by="modified desc", limit_page_length=8):
        if len(pending) >= 8:
            break
        pending.append({
            "doctype": "Material Request", "name": r.name,
            "supplier": "-", "state": r.workflow_state,
            "value_fmt": _fmt(r.aig_estimated_total or 0),
            "badge": BADGES.get(r.workflow_state, "b-generic"),
        })

    # ---- 12-week committed spend trend (ISO weeks) ----
    weeks = []
    today = now_datetime().date()
    year, wk, _ = today.isocalendar()
    base = (year, wk)
    buckets = {}
    for r in po_rows:
        d = r.transaction_date
        if not d:
            continue
        y, w, _ = d.isocalendar()
        buckets[(y, w)] = buckets.get((y, w), 0) + (r.grand_total or 0)
    trend = []
    for back in range(11, -1, -1):
        # step back `back` weeks from the current ISO week
        from datetime import timedelta
        d0 = today - timedelta(days=back * 7)
        y2, w2, _ = d0.isocalendar()
        val = buckets.get((y2, w2), 0.0)
        trend.append({"week": f"{y2}-W{w2}", "short": f"W{w2}",
                      "value": round(val, 2)})
    del base, year, wk

    # ---- top suppliers by committed PO value ----
    by_sup = {}
    for r in po_rows:
        if r.supplier:
            by_sup[r.supplier] = by_sup.get(r.supplier, 0) + (r.grand_total or 0)
    top_suppliers = sorted(
        ({"supplier": s, "value": round(v, 2), "value_fmt": _fmt(v)}
         for s, v in by_sup.items()),
        key=lambda x: -x["value"])[:5]

    data = {
        "kpi": kpi,
        "po_by_state": po_by_state,
        "mr_by_state": mr_by_state,
        "pipeline": pipeline,
        "pending": pending,
        "po_trend": trend,
        "top_suppliers": top_suppliers,
        "generated": now_datetime().strftime("%d %b %Y %H:%M"),
        "user": frappe.session.user_fullname or user,
    }
    context.data = data
    context.data_json = json.dumps(data, default=str)
    context.site_name = frappe.local.site
    context.no_cache = 1
    return context
