# Apply per-user Warehouse User Permissions from a CSV (user, enterprise).
#
# Per §3.4 User Permissions are per-user data and never travel in git or
# fixtures. This helper reads rows `user,enterprise` (comment lines starting
# with '#') and creates, idempotently, one User Permission per isolated
# warehouse belonging to the enterprise, plus one for the enterprise's cost
# center (so scoped users stay within their financial dimension).
#
# Run:
#   bench --site <site> execute aig_custom_theme.setup.apply_user_permissions.run \
#     --kwargs "{'csv_path': '/tmp/user_enterprises.csv'}"
#
# Model rules (mirrors 'aig_custom_theme.permission.warehouse_scoping'):
#  - a user listed for an enterprise sees ONLY that enterprise's isolated
#    warehouses + all mixed/shared-type warehouses (and no other enterprise's)
#  - multi-row users (multiple enterprises) gain access to each of them plus
#    shared warehouses in mixed mode
#  - a missing user or unknown enterprise row is skipped with a warning
#  - re-running creates nothing new (User Permission docs are checked first)

import csv
import os

import frappe

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _warehouses():
    p = os.path.join(DATA_DIR, "warehouses.json")
    with open(p, encoding="utf-8") as f:
        return frappe.safe_load(f)["nodes"]


def _cost_centers():
    p = os.path.join(DATA_DIR, "cost_centers.json")
    with open(p, encoding="utf-8") as f:
        return frappe.safe_load(f)["nodes"]


def _exists(user, allow, forvalue):
    return frappe.db.exists(
        "User Permission",
        {"user": user, "allow": allow, "for_value": forvalue},
    )


def _add(user, allow, forvalue):
    if _exists(user, allow, forvalue):
        return 0
    frappe.get_doc(
        {"doctype": "User Permission", "user": user, "allow": allow, "for_value": forvalue}
    ).insert(ignore_permissions=True)
    return 1


def run(csv_path=None, dry_run=False):
    frappe.only_for("System Manager")
    WH = "Warehouse"
    CC = "Cost Center"
    warehouse_rows = {w["name"]: w for w in _warehouses()}
    cc_rows = {c["name"]: c for c in _cost_centers()}

    path = csv_path
    if not path:
        path = os.path.join(DATA_DIR, "user_enterprises_sample.csv")

    added = 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, row in enumerate(csv.reader(f), start=1):
            if i == 1 or not row or row[0].strip().startswith("#"):
                continue
            user = (row[0] or "").strip()
            enterprise = (row[1] or "").strip() if len(row) > 1 else ""
            if not user or not enterprise:
                continue
            if not frappe.db.exists("User", user):
                print(f"  WARNING: user '{user}' not found -- row {i} skipped")
                continue
            cc_node = cc_rows.get(enterprise)
            if not cc_node:
                print(f"  WARNING: enterprise '{enterprise}' not in cost_centers.json -- row {i} skipped")
                continue
            if dry_run:
                print(f"  [dry] would grant {user}: {enterprise} warehouses")
                continue
            added += _add(user, CC, enterprise)
            for wh_name, w in warehouse_rows.items():
                if w.get("enterprise") != enterprise:
                    continue
                if frappe.db.exists("Warehouse", wh_name):
                    added += _add(user, WH, wh_name)
            print(f"  granted {user}: {enterprise} (+ its isolated warehouses)")
    frappe.db.commit()
    print(f"done: {added} User Permission rows created")
    return added
