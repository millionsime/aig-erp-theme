# Inventory layer — decisions and assumptions

Branch `feature/inventory`, cut from `feature/foundation`. Everything below was
decided by the agent where the brief left it open; each item says how to change
it without touching code.

## Packaging

| Decision | Why | How to change |
| --- | --- | --- |
| Stock Settings are applied by a **seed function**, not a fixture | A fixture would carry site-specific noise (modified_by, timestamps) and could not stay idempotent | `setup/data/inventory_settings.json` |
| Masters (UOM, Item Group, Stock Entry Type, Price List, Warehouse Type) are seeded from `setup/data/inventory_*.json` | Names are placeholders in this deployment; operators edit data, not Python | edit the JSON, re-run the seed |
| Custom Fields are created **in code** (`INVENTORY_CUSTOM_FIELDS`) instead of only being shipped as a fixture | On a fresh install the fields must exist *before* the first Item Group insert; a fixture imports after model sync | `setup/inventory_seed.py` |
| The seed runs on `bench migrate` through patch `custom_theme.patches.aig_0002_inventory_seed` | Production picks the layer up with no manual step | `custom_theme/patches.txt` |

## Stock behaviour

| Setting | Value | Rationale |
| --- | --- | --- |
| `valuation_method` | **FIFO** | Brief. Also what the existing site already had, so no re-valuation risk on upgrade. |
| `allow_negative_stock` | **0** | Brief. A hard block for every warehouse; per-item overrides are not seeded. |
| `auto_indent` (auto Material Request on reorder) | **0** | Brief: alert instead. `reorder_email_notify` also stays 0 so ERPNext's own mailer does not double up with the AIG alert job. |
| `item_naming_by` | `Item Code` | The AIG server script `AIG - Item Auto Code` owns the code; naming stays manual/scripted. |
| `auto_insert_price_list_rate_if_missing` | **1** | Items must carry a rate for FIFO valuation on receipt; without it every receipt is zero-valued. |
| `stock_frozen_upto_days` | **0** | Back-dated entries stay allowed. Raise it in the data file when the stock freeze policy is agreed. |
| `use_serial_batch_fields` | 1 | Batch/serial tracking is off per group; when turned on, the simple fields (not the bundle) are used, matching the AIG store-workflow scripts. |
| Stock adjustment account | **adopted** from the CoA (`account_type = Stock Adjustment`), never created | The CoA is owned by `aig-erp-config`; this app must not invent accounts. On this site it resolved to `Stock Adjustment - AIG`. |

## Item groups

Default tree is flat under `All Item Groups`: Consumables, Office Supplies,
Spare Parts, Fixed Asset Items, Agro Inputs, Construction Materials, Services,
plus `Fuel` under Consumables as a worked example of a child group.

Inheritance is carried by five `aig_*` flags on **Item Group**, copied onto new
Items by a default-fill hook:

- `aig_is_stock_item` (default 1) → `Item.is_stock_item`
- `aig_is_fixed_asset` → `Item.is_fixed_asset` + `auto_create_assets`
- `aig_has_batch_no` → `Item.has_batch_no`
- `aig_has_serial_no` → `Item.has_serial_no`
- `aig_has_expiry_date` → `Item.has_expiry_date` (+ `shelf_life_in_days` untouched)

`Services` is the only group seeded as non-stock. Batch/serial/expiry are **off
everywhere** in the seed, as the brief requires; flipping a flag in the JSON and
re-running the seed turns them on for that group only.

Assumption: "Fixed Asset Items must be flagged" is read as *the group tells the
Item to be a fixed asset*, not as *the group itself is an asset*. Asset logic
(Asset Category, depreciation, capitalisation) is out of scope here.

## UOMs

`Nos, Kg, Quintal, Ton, Litre, Meter, Box, Pack, Set, Roll`, in four UOM
Categories (Quantity, Mass, Volume, Length). Conversions seeded: `1 Quintal = 100
Kg`, `1 Ton = 1000 Kg`. `Ton` is deliberately **not** given a direct Ton→Quintal
row: ERPNext resolves it through Kg, and a second path invites rounding drift.

`Set` and `Roll` are extras beyond the brief's list — both are used in AIG store
paperwork. Remove them from the JSON if unwanted.

## Warehouses

The foundation seed keeps placeholder store names (X/Y/Z equivalents). This layer
adds only what is safe to add without renaming stores:

- Warehouse Types: `Store`, `Scrap`, `Receiving` (plus the existing `Transit`,
  `Manufacturing`, `Receivable`).
- `Cost Center.aig_default_warehouse` — the per-enterprise default store, used to
  default `Material Request.aig_destination_warehouse` and usable as an
  Employee/User default.
- The enterprise (Cost Center) remains the isolation key: `Warehouse.aig_cost_center`
  already exists from the foundation layer and is what the isolation check reads.

Renaming the placeholder stores is left to the operator: they are data, and the
brief says they are still placeholders.

## Deviations from the brief, and why

1. **`enable_stock_maintenance` does not exist in ERPNext v16.** It was in the
   brief's Stock Settings list; the field was removed upstream. Nothing to set.
2. **`stock_frozen_days` is `stock_frozen_upto_days` in v16.** Same intent.
3. **UOM Category is mandatory** on a UOM Conversion Factor in v16 (discovered
   when the first seed run failed with `MandatoryError: category`). Categories
   are therefore derived from the UOM data file rather than hardcoded.
4. **Stock Entry Type has no autoname** on this build, so the seed sets `name`
   explicitly.

## Not built in this pass

These are in the brief but deliberately not faked; see the final report's gap
table for status:

- Material Request workflow reshaping (the `AIG Stock Request Approval` workflow
  already exists from the foundation/procurement work and was **not** modified).
- Inter-warehouse transfer approval, Stock Reconciliation approval,
  store-manager gate on isolated-warehouse issues.
- Reorder alert and monthly stock-count reminder scheduler jobs.
- Reports (Stock Balance by Enterprise, Material Request pending status, Low
  Stock) and the Model 19/22 print-format changes (four AIG print formats already
  exist).
- `TODO(procurement)` extension point is documented on the
  `aig_forwarded_to_procurement` field itself.


## Pass 2 additions (2026-11-10)

| Decision | Why | Change it in |
| --- | --- | --- |
| Gate defaults are written into `tabSingles` by the seed, not just declared as DocType defaults | An unset Check reads back as `0`, which silently disabled every new gate on a site whose Single had never been saved | `SETTING_DEFAULTS` in `setup/inventory_seed.py` |
| Warehouse `mixed`/`isolated` + owning enterprise stay in `setup/data/warehouses.json`; a warehouse not in the file falls back to `Warehouse.aig_cost_center` | The data file is the declared source of truth, and the fallback keeps stores created later from becoming silently "mixed" | `data/warehouses.json` |
| Every Material Transfer needs Store Manager approval; isolated issues need it too. Both switches default on | Brief. Switching either off leaves the cross-enterprise block independent | `AIG Minimum ERP Settings` |
| Cross-enterprise block applies only isolated -> isolated; isolated -> mixed is allowed | Brief ("target is a mixed warehouse") | `block_cross_enterprise_transfer` |
| `enable_closest_boss_guard` defaults **on** | Brief default. It is enforced by `guards.py` as an extra check on the existing `Pending Enterprise Approval` transition — never by replacing the existing approver role | `AIG Minimum ERP Settings` |
| No Material Request workflow state was added, renamed or removed | Existing behaviour is the source of truth for this pass | — |
| Reorder alerts and the count reminder are Notification Log rows, one per user+subject+day | Dedupe without a new table, visible in the desk bell | `guards.py` `_notify()` |
| `is_default` on Holiday List is advisory | ERPNext v16 Holiday List has no such field; the seed sets it only if the field exists | `data/holiday_lists.json` |
| The 2018-EC tail list carries the weekly off only, with no public holidays | No fixed Ethiopian public holiday falls between 2026-07-08 and 2026-09-10; both 2026 Eid dates fall before it. Flagged in the data file rather than guessed | `data/holiday_lists.json` |

### Environment defects found and fixed outside git

`sites/apps.txt` in the bench container listed only `erpnext`, `frappe`, `hrms`.
Frappe builds its module->app map from that file, so **every module of
`custom_theme` was invisible**: model sync never created `AIG Minimum ERP
Settings`, and any code path that loaded one of the app's doctype controllers
raised `Module AIG Custom Theme not found`. Appending `custom_theme` to
`sites/apps.txt` and clearing the cache fixed both. This is a bench-level file,
not repository content — a fresh container from the same image will need the
same line, and the Dockerfile/compose for that image should add it.
