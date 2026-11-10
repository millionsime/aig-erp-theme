# Procurement: what already exists (read-only audit)

Generated from the live `test.local` database on 2026-11-10. No changes were
made to anything described here.

## 1. Workflows

- **AIG Stock Request Approval** on **Material Request** (active: 1, state field `workflow_state`)
- **AIG Procurement Approval** on **Purchase Order** (active: 1, state field `workflow_state`)

### Purchase Order transitions (`AIG Procurement Approval`)

| From | Action | To | Allowed role | Condition |
| --- | --- | --- | --- | --- |
| Draft | Submit for Direct Purchase | Pending Finance Signoff | AIG Procurement Officer | (doc.grand_total or 0) < 20000 |
| Draft | Submit for Committee Review | Pending Committee Signoff | AIG Procurement Officer | (doc.grand_total or 0) >= 20000 |
| Pending Committee Signoff | Finalize Committee Decision | Pending Enterprise Head Approval | AIG Purchase Committee | (doc.grand_total or 0) <= 750000 |
| Pending Committee Signoff | Forward to Tender Committee | Pending Corporate Approval | AIG Purchase Committee | (doc.grand_total or 0) > 750000 |
| Pending Committee Signoff | Reject | Rejected | AIG Purchase Committee | - |
| Pending Enterprise Head Approval | Approve | Approved | AIG Enterprise Head | - |
| Pending Enterprise Head Approval | Reject | Rejected | AIG Enterprise Head | - |
| Pending Corporate Approval | Approve | Pending CEO Approval | AIG Corporate | - |
| Pending Corporate Approval | Reject | Rejected | AIG Corporate | - |
| Pending CEO Approval | Approve | Approved | AIG CEO | - |
| Pending CEO Approval | Reject | Rejected | AIG CEO | - |
| Pending Finance Signoff | Finance Sign-off | Approved | AIG Finance | - |
| Pending Finance Signoff | Reject | Rejected | AIG Finance | - |

### Material Request transitions (`AIG Stock Request Approval`)

| From | Action | To | Allowed role |
| --- | --- | --- | --- |
| Draft | Submit Purchase Request | Pending Budget Approval | AIG End User |
| Pending Store Review | Approve & Assign | Approved | AIG Main Store Administrator |
| Draft | Submit Request | Pending Store Review | AIG End User |
| Pending Store Review | Approve | Pending Enterprise Approval | AIG Main Store Administrator |
| Pending Store Review | Reject | Rejected | AIG Main Store Administrator |
| Pending Enterprise Approval | Approve | Approved | AIG Enterprise Head |
| Pending Enterprise Approval | Reject | Rejected | AIG Enterprise Head |
| Draft | Submit Request | Approved | AIG Procurement Officer |
| Draft | Submit for Endorsement | Pending Enterprise Head Endorsement | AIG Procurement Officer |
| Pending Enterprise Head Endorsement | Endorse | Endorsed | AIG Enterprise Head |
| Pending Enterprise Head Endorsement | Reject | Rejected | AIG Enterprise Head |
| Pending Head Approval | Approve | Pending Print & Seal | AIG Enterprise Head |
| Pending Head Approval | Reject | Rejected | AIG Enterprise Head |
| Pending Budget Approval | Approve Budget | Pending Corporate Approval | AIG Plan and Budget |
| Pending Budget Approval | Reject | Rejected | AIG Plan and Budget |
| Pending CEO Approval | Approve | Pending Print & Seal | AIG CEO |
| Pending Corporate Approval | Approve | Pending Print & Seal | AIG Corporate |
| Pending Print & Seal | Confirm Printed & Sealed | Pending Store Review | AIG Record Office |
| Pending Print & Seal | Reject | Rejected | AIG Record Office |
| Pending Store Review | Approve & Assign | Approved | AIG Procurement Director |
| Draft | Submit Purchase Request | Pending Budget Approval | AIG End User |
| Pending Budget Approval | Approve Budget | Pending Head Approval | AIG Plan and Budget |
| Pending Budget Approval | Approve Budget | Pending CEO Approval | AIG Plan and Budget |
| Pending Budget Approval | Approve Budget | Pending Corporate Approval | AIG Plan and Budget |

## 2. Scripts touching procurement DocTypes

### Server scripts (14)

| Name | DocType | Event | Disabled |
| --- | --- | --- | --- |
| AIG - MR Approval Guard | Material Request | Before Save (Submitted Document) | 0 |
| AIG - MR CC Normalize | Material Request | Before Validate | 0 |
| AIG - MR End User Purchase Scope | Material Request | Before Validate | 0 |
| AIG - MR End User Type Default | Material Request | Before Insert | 1 |
| AIG - MR End User Type Guard | Material Request | Before Validate | 1 |
| AIG - MR Item Cost Center Sync | Material Request | Before Save | 0 |
| AIG - MR Request Defaults | Material Request | Before Insert | 0 |
| AIG - MR Stock Item Guard | Material Request | Before Validate | 0 |
| AIG - CC Guard Purchase Invoice | Purchase Invoice | Before Validate | 0 |
| AIG - PO Committee Majority | Purchase Order | Before Save (Submitted Document) | 0 |
| AIG - PO Committee Reject Guard | Purchase Order | Before Cancel | 0 |
| AIG - PO Cost Center Default | Purchase Order | Before Save | 0 |
| AIG - PO Guard Raw Submit | Purchase Order | Before Submit | 0 |
| AIG - Model 42 Guard | Purchase Receipt | Before Submit | 0 |

### Client scripts (5)

| Name | DocType | View | Enabled |
| --- | --- | --- | --- |
| AIG - MR CC Intercept | Material Request | Form | 1 |
| AIG - MR Default Type (End User) | Material Request | Form | 1 |
| AIG - Row CC Scrub (Material Request) | Material Request | Form | 1 |
| AIG - Ethiopic Date (Purchase Order) | Purchase Order | Form | 1 |
| AIG - Row CC Scrub (Purchase Order) | Purchase Order | Form | 1 |

## 3. Custom fields (22)

| DocType | Field | Type | Label |
| --- | --- | --- | --- |
| Material Request | `aig_assigned_procurement_officer` | Link | Assigned Procurement Officer |
| Material Request | `aig_budget_checked` | Check | Budget Checked |
| Material Request | `aig_budget_note` | Small Text | Budget Check Note |
| Material Request | `aig_cost_center` | Link | AIG Enterprise (Cost Center) |
| Material Request | `aig_destination_warehouse` | Link | Destination Store |
| Material Request | `aig_estimated_total` | Currency | Estimated Total (ETB) |
| Material Request | `aig_forwarded_to_procurement` | Check | Forwarded to Procurement |
| Material Request | `aig_issue_reference` | Link | Issue Reference (Stock Entry) |
| Material Request | `aig_procurement_reference` | Data | Procurement Reference |
| Material Request | `aig_purpose_note` | Small Text | Purpose |
| Material Request | `aig_receipt_confirmed` | Check | Receipt Confirmed |
| Material Request | `aig_receipt_note` | Small Text | Receipt Confirmation Note |
| Material Request | `aig_received_by` | Link | Received By (End User) |
| Material Request | `aig_received_on` | Datetime | Received On |
| Material Request | `aig_rejected_reason` | Small Text | Rejection Reason |
| Material Request | `aig_requested_by` | Link | Requested By |
| Material Request | `workflow_state` | Link | Workflow State |
| Purchase Order | `aig_assigned_committee_members` | Table | AIG Assigned Committee Members |
| Purchase Order | `aig_cost_center` | Link | AIG Cost Center |
| Purchase Order | `aig_eth_date_display` | HTML | Ethiopian Date (EC) |
| Purchase Order | `workflow_state` | Link | Workflow State |
| Request for Quotation | `aig_assigned_committee_members` | Table | AIG Assigned Committee Members |

## 4. AIG permissions on procurement DocTypes (48 rows)

| DocType | Role | R | W | C | Submit | Cancel | Amend | Report |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Material Request | AIG CEO | 1 | 1 | 1 | 1 | 1 | 0 | 1 |
| Material Request | AIG Corporate | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
| Material Request | AIG End User | 1 | 1 | 1 | 1 | 1 | 0 | 1 |
| Material Request | AIG Enterprise Head | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
| Material Request | AIG Finance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Material Request | AIG General Store Keeper | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Material Request | AIG Internal Auditor | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Material Request | AIG Inventory Administrator | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| Material Request | AIG Main Store Administrator | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
| Material Request | AIG Plan and Budget | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
| Material Request | AIG Procurement Director | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
| Material Request | AIG Procurement Officer | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| Material Request | AIG Property Admin Expert | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Material Request | AIG Record Office | 1 | 1 | 0 | 0 | 1 | 0 | 1 |
| Material Request | AIG Store Keeper | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| Purchase Invoice | AIG CEO | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Invoice | AIG Corporate | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Invoice | AIG Deputy | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Invoice | AIG Enterprise Head | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Invoice | AIG Finance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Invoice | AIG Purchase Committee | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Order | AIG CEO | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| Purchase Order | AIG Corporate | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| Purchase Order | AIG Enterprise Head | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| Purchase Order | AIG Finance | 1 | 1 | 0 | 1 | 0 | 0 | 0 |
| Purchase Order | AIG Procurement Officer | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| Purchase Order | AIG Purchase Committee | 1 | 1 | 0 | 1 | 1 | 0 | 0 |
| Purchase Receipt | AIG CEO | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Corporate | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Deputy | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Enterprise Head | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Finance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG General Store Keeper | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Internal Auditor | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Main Store Administrator | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Procurement Officer | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| Purchase Receipt | AIG Purchase Committee | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Purchase Receipt | AIG Store Keeper | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| Request for Quotation | AIG CEO | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Request for Quotation | AIG Corporate | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Request for Quotation | AIG Enterprise Head | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Request for Quotation | AIG Finance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Request for Quotation | AIG Procurement Officer | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| Supplier Quotation | AIG CEO | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Supplier Quotation | AIG Corporate | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Supplier Quotation | AIG Enterprise Head | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Supplier Quotation | AIG Finance | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Supplier Quotation | AIG Procurement Officer | 1 | 1 | 1 | 1 | 0 | 1 | 0 |

## 5. Committees

`AIG Assigned Committee Member` exists as a child DocType, and a Table field of
that type is declared on **no** DocType (`0` matches). There are **0** committee rows in the database,
so in practice no committee membership is recorded anywhere yet.

The committee rule lives in code instead:

- `enable_committee` = **1** and `purchase_order_threshold` = **5000000.0** in `AIG Minimum ERP Settings`.
- Server scripts `AIG - PO Committee Majority` and `AIG - PO Committee Reject Guard` enforce
  majority/reject logic on Purchase Order; `AIG - CS Guard` guards the Committee Signoff DocType;
  `Quality Inspection` and `Request for Quotation` carry committee validation via a `validate` hook.

## 6. Thresholds

Two different threshold mechanisms exist and they do not agree:

1. **Live, in the workflow conditions** on `AIG Procurement Approval`:
   - `< 20000` ETB -> direct purchase, finance signoff
   - `>= 20000` ETB -> committee review
   - `<= 750000` ETB -> enterprise head approval after committee
   - `> 750000` ETB -> forwarded to the tender committee / corporate approval
2. **Declarative only**: `purchase_order_threshold` = 5,000,000 ETB in
   `AIG Minimum ERP Settings`. No script or transition references it
   (0 scripts mention a threshold setting), so `AIG Minimum ERP Settings` and
   the workflow disagree by a factor of ~6.7 at the committee boundary
   (20,000 live vs 5,000,000 configured).

Any procurement build must decide which one is authoritative. Do not wire a new
rule to `purchase_order_threshold` without resolving that.

## 7. Overlaps and conflicts with the foundation work

1. **Two workflows share the procurement surface.** `AIG Procurement Approval` (PO) and
   `AIG Stock Request Approval` (MR) both gate purchasing: an MR can end at `Approved` and a
   PO then runs its own approval chain. Nothing links them — no field carries an MR approval
   reference onto the PO, so a PO raised from a request does not prove the request was approved.
2. **`Draft -> Submit Request -> Approved` for AIG Procurement Officer** in the MR workflow
   bypasses store and enterprise approval entirely.
3. **Role overlap:** `AIG Procurement Director` and `AIG Procurement Officer` both hold write on
   Material Request; `AIG Purchase Committee` holds read-only there but is the role the committee
   scripts look for on PO. Three procurement roles, overlapping scopes.
4. **`AIG - PO Guard Raw Submit`** blocks posting outside the workflow, mirroring the Stock Entry
   rule — any future procurement build must go through the workflow, not raw submit.
5. **No committee data exists** (0 rows, no DocType carries the child table), so the committee
   scripts are currently untestable with real membership; they can only reject or no-op.

