# AIG role inventory

31 `AIG *` roles exist on the site (all created by the foundation seed, all
included in the `Role` fixture filter `name like AIG%`). One line each, with
redundancy flags at the end.

## Executive and oversight

| Role | Purpose |
| --- | --- |
| AIG CEO | Final approver where policy requires company sign-off (HR Director appointment, large payments). |
| AIG Deputy | Acts for the CEO; same read reach as CEO, no independent approval rights. |
| AIG Corporate | Head-office coordination role; broad read on transactions, no operational write. |
| AIG Internal Auditor | Read-only across stock, finance and HR records for audit work. |
| AIG Record Office | Archives and retrieves approved documents (Model forms), read + cancel. |

## Finance

| Role | Purpose |
| --- | --- |
| AIG Finance | Day-to-day accounting entries and posting reads. |
| AIG Finance Head | Approves finance-side steps, sees finance reports. |
| AIG Chief Accountant | Owns the chart of accounts, item and cost-centre masters. |
| AIG Accountant | Creates Sales Invoice / Payment Entry / Salary Slip, cannot edit company masters. |
| AIG Plan and Budget | Budget check step on requests and purchases. |

## Procurement

| Role | Purpose |
| --- | --- |
| AIG Procurement Director | Approves procurement steps above threshold. |
| AIG Procurement Officer | Raises and runs RFQ / quotation / PO cycle. |
| AIG Purchase Committee | Committee member for purchase decisions (majority rule). |
| AIG Procurement Developer | Builds procurement-side scripts and fields only. |

## Stores and inventory

| Role | Purpose |
| --- | --- |
| AIG Store Keeper | Day-to-day receipts and issues at a store. |
| AIG General Store Keeper | Store keeper across the general (non-main) stores. |
| AIG Store Expert | Verifies store entries, checks availability, drafts reconciliations. |
| AIG Store Manager | Approves transfers, issues from isolated warehouses, reconciliations. |
| AIG Main Store Administrator | Runs the main store: final approval on main-store receipts. |
| AIG Inventory Administrator | Owns item, item group, warehouse and UOM masters. |
| AIG Inventory Developer | Builds inventory-side scripts and fields only. |
| AIG Property Admin Expert | Property/asset tagging and fixed-asset item data. |

## HR

| Role | Purpose |
| --- | --- |
| AIG HR Director | Leave-approval escalation point; approved by the CEO before acting as final approver. |
| AIG HR Expert | HR officer: processes leave, maintains employee records. |
| AIG HR Manager | HR line manager role (kept for structure; see flag below). |
| AIG HR Developer | Builds HR-side scripts and fields only. |

## Generic / cross-cutting

| Role | Purpose |
| --- | --- |
| AIG Team Leader | Approves their team's requests; the "closest boss" in the MR workflow. |
| AIG Enterprise Head | Enterprise-level approval and read of that enterprise's stock and requests. |
| AIG End User | Raises Material Requests; sees only their own. |
| AIG Evaluation Committee | Committee member for evaluation/sign-off records. |
| AIG Asset Developer | Builds asset-side scripts and fields only. |

## Redundancy flags

- **AIG Store Keeper vs AIG General Store Keeper** — overlapping permission sets
  in the Custom DocPerm fixtures (both get Stock Entry create/submit and Bin
  read). Suggest keeping `General Store Keeper` as the enterprise-wide variant
  and documenting the difference in scope, or merging them.
- **AIG HR Manager vs AIG HR Expert** — `HR Manager` is the ERPNext-standard name
  the brief explicitly says *not* to rely on; the leave workflow uses
  `AIG HR Director` / `AIG HR Expert`. `AIG HR Manager` currently looks vestigial.
- **AIG Inventory Administrator vs AIG Main Store Administrator** — both can
  submit Stock Entry and Stock Reconciliation; they differ only in main-store
  scope. Fine as long as the difference is enforced by User Permissions, not by
  hope.
- **AIG Corporate / AIG Deputy / AIG CEO** — read overlaps heavily; that is
  intentional (oversight), but none of the three should hold write on stock.
