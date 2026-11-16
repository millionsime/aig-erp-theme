# Material Request / Stock Entry — brief versus site, reconciled

Governing rule for this pass: **existing behaviour wins.** Nothing below renames
a state, removes a transition, or edits an existing server script. Where the
brief asked for something the site does differently, the item is recorded as a
gap and closed with an *additive* guard, or left alone with the reason.

Evidence: `bench --site test.local` workflow transitions, the 30 server scripts,
and the guard tests in the final report.

## 1. The Material Request workflow that exists

`AIG Stock Request Approval` (active, `workflow_state_field = workflow_state`):

| From | Action | To | Role |
| --- | --- | --- | --- |
| Draft | Submit Request | Pending Store Review | AIG End User |
| Pending Store Review | Approve | Pending Enterprise Approval | AIG Main Store Administrator |
| Pending Store Review | Approve & Assign | Approved | AIG Main Store Administrator |
| Pending Store Review | Reject | Rejected | AIG Main Store Administrator |
| Pending Enterprise Approval | Approve | Approved | AIG Enterprise Head |
| Pending Enterprise Approval | Reject | Rejected | AIG Enterprise Head |
| Draft | Submit Purchase Request | Pending Budget Approval | AIG End User |
| Draft | Submit Request | Approved | AIG Procurement Officer |

Guards already in force (server scripts, untouched):

- `AIG - MR Approval Guard` — blocks self-approval in `Pending Enterprise
  Approval` / `Approved`, and demands a real budget check (`aig_budget_checked`
  or a note) before leaving `Pending Enterprise Approval`.
- `AIG - MR End User Purchase Scope` — End Users may only raise `Purchase` or
  `Material Issue`.
- `AIG - MR Request Defaults`, `AIG - MR CC Normalize`, `AIG - MR Item Cost
  Center Sync`, `AIG - MR Stock Item Guard`, `AIG - MR End User Type Default`,
  `AIG - MR End User Type Guard`.

## 2. Comparison with the brief

| Brief item | Site today | Status | Resolution |
| --- | --- | --- | --- |
| Employee submits → "Pending Closest Boss" | Employee submits → "Pending Store Review", then "Pending Enterprise Approval" for AIG Enterprise Head | **Gap (different shape)** | Not renamed. The brief's closest-boss *intent* is met only if the enterprise approver is the requester's boss; that is not enforced anywhere today. |
| Closest boss approves | `Pending Enterprise Approval` is role-only (any AIG Enterprise Head) | **Gap** | Closed additively by `guards.enforce_closest_boss` — switch `enable_closest_boss_guard` (default **on**). Implemented and tested this pass (6 cases). |
| Store Expert checks availability | "Pending Store Review" is held by **AIG Main Store Administrator**, not AIG Store Expert | **Redundant role overlap** | Left as-is. Changing who holds the state is a policy change, not a fix; flagged for your decision. |
| Issue from stock → "Approved for Issue" | No such state; approved requests are `Approved` and the issue is a Stock Entry linked to the request | **Gap (naming)** | No new state added. `AIG - SE Issue Validation` already requires the linked request to be `Approved`, which delivers the control without a new state. |
| Not in stock → "Forwarded to Procurement" | No state, no flag | **Gap** | Additive flag `aig_forwarded_to_procurement` + `aig_procurement_reference` (from pass 1). No workflow state. `TODO(procurement)` recorded on the field description. |
| Rejection sets a mandatory reason | `Rejected` exists; no reason field | **Gap** | Additive field `aig_rejected_reason` (from pass 1). Not made mandatory by a property setter, so the existing Reject transitions keep working. |
| Nobody approves their own request | Already enforced by `AIG - MR Approval Guard` | **Already covered** | Untouched. |
| Requester's cost center defaults from Employee | `aig_cost_center` exists; defaulting is done by the MR defaults script | **Already covered** | Untouched. |
| Isolated-warehouse issue needs Store Manager | Not enforced | **Gap** | Closed in app code on Stock Entry (below). |
| Transfer needs Store Manager + cross-enterprise block | Not enforced | **Gap** | Closed in app code on Stock Entry (below). |

## 3. What was added, and where

`custom_theme/aig_custom_theme/inventory/guards.py`, registered in `hooks.py`
(additive `doc_events.update(...)`, foundation block untouched):

| Hook | Doctype / event | Behaviour |
| --- | --- | --- |
| `classify_stock_entry` | Stock Entry `before_validate` | Sets `aig_requires_store_manager_approval` when a Material Issue (or transfer for manufacture) leaves an isolated warehouse, or for every Material Transfer. Blocks a transfer between two enterprises' isolated stores; allows isolated → mixed. |
| `validate_store_manager_approval` | Stock Entry `before_submit` | Refuses to post without approval, and refuses when the approver is the document owner or the current user. |
| `approve_store_manager_gate` | whitelisted API | Store Manager (or System Manager) records the approval with user + timestamp. |
| `require_store_manager_for_reconciliation` | Stock Reconciliation `before_submit` | Only Store Manager / System Manager may submit a count. |
| `apply_item_group_defaults` | Item `validate` | New Items inherit the group's batch / serial / expiry / fixed-asset flags. |
| `enforce_closest_boss` | Material Request `validate` | On exit from `Pending Store Review` / `Pending Enterprise Approval` the acting user must be the requester's closest boss (walked up `Employee.reports_to`). No boss on record → warning, not a block. Administrator / System Manager act on behalf. Never replaces the workflow's role rules. |

Warehouse ownership is read from `setup/data/warehouses.json`
(`type: mixed|isolated`, `enterprise`), never from store-name string matching —
a store added later falls back to `Warehouse.aig_cost_center`.

The existing `AIG - SE Guard Raw Submit` (posting only via `Posted`) and
`AIG - SE Issue Validation` (approved Model 19 + quantity ceiling) still run
first; the new guard sits in front of them and cannot bypass them.

## 4. Known overlaps left in place (need your call, not a code fix)

1. **"Pending Store Review" is held by AIG Main Store Administrator**, while the
   brief expects AIG Store Expert to check availability. Both roles exist and
   both hold Stock Entry submit; the workflow grants the state to Main Store
   Administrator only.
2. **`Draft → Submit Request → Approved` for AIG Procurement Officer** — a single
   click reaches `Approved` for procurement staff, bypassing store and
   enterprise approval. Almost certainly intentional (procurement raises its own
   requests) but it means the approvals are not universal.
3. **`Draft → Submit Purchase Request → Pending Budget Approval`** — this state
   has no outgoing transition in the workflow definition, so a request that
   enters it cannot proceed. It may be driven by a script, but nothing in the
   workflow moves it onward.
