# Verification log — part 3

Site: `test.local` (frappe_docker stack, WSL). Branch `feature/inventory`.
Every line below is from an actual run; nothing here is inferred.

## 1. Test factory

```
users created:      12   (employee, team_leader, enterprise_head, ceo, store_keeper,
                          store_expert, store_manager, hr_expert, hr_director,
                          accountant, proc_dev, hr_dev)
employees created:  12   (Reports-To chain applied in a second pass)
leave allocations:   8   (Annual/Sick/Maternity for 4 of the users)
```

The factory refuses to run without `developer_mode` or `AIG_TEST_SITE=1`.

**Blocked:** stock seeding. `create_stock()` opens stock with a Stock
Reconciliation, which fails with:

```
OpeningEntryAccountError: Difference Account must be a Asset/Liability type
account, since this Stock Reconciliation is an Opening Entry
```

The company's stock-adjustment account (`Stock Adjustment - AIG`) is an
expense-type account, so it cannot be used for an opening entry. A Stock Entry
receipt is not a workaround: it is workflow-bound (`AIG Store Receiving`), and
forcing `workflow_state` is rejected with `Workflow State transition not allowed
from Draft to Posted` / `Not a valid Workflow Action`. **No stock item with
quantity exists on the site, so every ledger/FIFO test is still unrun.**

## 2. Closest-boss guard — 6/6 pass

```
chain: employee_boss = team_leader@aigtest.local (expected same)
       ceo_boss      = None
PASS  closest boss may approve
PASS  wrong user blocked          (AIG: this stock request is waiting for employee@aigtest.loca…)
PASS  no boss on record falls back (warning, not a block)
PASS  requester cannot approve own (AIG: a requester cannot approve their own stock request.)
PASS  toggle off allows role approver
PASS  unrelated transition untouched (Draft -> Pending Store Review)
```

## 3. Inventory gates (from part 2, re-stated because they are still the evidence)

```
issue_from_isolated_requires_approval : 1
issue_from_mixed_requires_approval    : 0
cross_enterprise_transfer             : BLOCKED (Project Store -> Andode Store,
                                        different enterprises)
isolated_to_mixed                     : allowed (approval=1)
submit_unapproved                     : blocked
self_approval                         : blocked
manager_approval_accepted             : true
```

## 4. Defect found while writing the factory

**`AIG Store Expert` has no create permission on Stock Reconciliation.** The
existing Custom DocPerms grant create to AIG Store Keeper, AIG Inventory
Administrator and AIG General Store Keeper only. The brief says "Store Expert
drafts, Store Manager submits" for stock counts, and the data contradicts that.
The factory works around it by drafting as Store Keeper; the permission itself
was **not** changed (that is item 6, not done).

## 5. Not run

Everything below is unfinished, not failed:

- leave matrix (Employee / Team Leader / HR staff / HR Director + CEO), incl. a
  leave crossing 2026-09-10/11
- developer guardrail matrix (4 roles x 4 builder doctypes)
- accountant matrix (Sales Invoice / Payment Entry / Salary Slip create;
  Company / Account / Cost Center blocked)
- committee guard (assigned vs unassigned)
- warehouse isolation via User Permission
- `ensure_tax_setup` fail-soft path
- inventory end-to-end (issue, ledger, FIFO hand-calculation), reorder
  notification delivery with real recipients, monthly reminder day path
- fresh throwaway site from git (`verify_from_git.sh`), two-migrate metric
  comparison, fixture round-trip
- permissions diff (item 6), reports/prints (item 7), version bump/README (item 8),
  known-issues section (item 9)
