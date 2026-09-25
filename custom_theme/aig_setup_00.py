# AIG config - step 0: read-only inspection of the instance.
# Prints everything the build needs to know before creating anything.
print("=== COMPANY ===")
for c in frappe.get_all("Company", fields=["name", "company_name", "default_currency", "abbr", "enable_perpetual_inventory"]):
    print(c)

print("\n=== FISCAL YEARS ===")
for fy in frappe.get_all("Fiscal Year", fields=["name", "year_start_date", "year_end_date", "disabled"]):
    print(fy)

print("\n=== COST CENTERS (active) ===")
for cc in frappe.get_all("Cost Center",
                         filters={"disabled": 0},
                         fields=["name", "cost_center_name", "parent_cost_center", "company", "is_group"],
                         order_by="lft"):
    print(f"{'[G]' if cc.is_group else '   '} {cc.name}  parent={cc.parent_cost_center}")

print("\n=== EXISTING WORKFLOWS ===")
for w in frappe.get_all("Workflow", fields=["name", "document_type", "workflow_state_field", "is_active"]):
    print(w)

print("\n=== AIG ROLES (existing?) ===")
roles = frappe.get_all("Role", filters={"name": ["like", "AIG%"]}, pluck="name")
print(roles or "none")

print("\n=== AIG USERS (existing?) ===")
users = frappe.get_all("User", filters=[["email", "like", "%@aig.local"]], fields=["name", "full_name", "enabled"])
print(users or "none")

print("\n=== KEY ACCOUNTS ===")
for pattern in ["Cost of Goods Sold", "Stock Received But Not Billed", "Temporary", "Round Off"]:
    accs = frappe.get_all("Account",
                          filters=[["account_name", "like", f"%{pattern}%"], ["is_group", "=", 0]],
                          fields=["name", "company"], limit=6)
    print(f"{pattern}: {[a.name for a in accs]}")

print("\n=== TAX TEMPLATES (existing?) ===")
print("Withholding categories:", frappe.get_all("Tax Withholding Category", pluck="name"))
print("Purchase taxes templates:", [t.name for t in frappe.get_all("Purchase Taxes and Charges Template", fields=["name", "company"], limit=10)])

print("\n=== SITE BASICS ===")
print("currency (sys defaults):", frappe.db.get_single_value("Global Defaults", "default_currency"))
print("installed apps:", frappe.get_installed_apps())
print("erpnext version:", frappe.get_attr("erpnext.__version__")() if hasattr(frappe.get_attr("erpnext", "__version__"), "__call__") else getattr(__import__("erpnext"), "__version__", "unknown"))

print("\n=== SERVER SCRIPT ENABLED? ===")
print("server_script_enabled:", frappe.conf.get("server_script_enabled"))
print("server scripts existing:", frappe.get_all("Server Script", pluck="name"))

print("\n=== CUSTOM FIELDS ON PO (cost_center?) ===")
print(frappe.get_all("Custom Field", filters={"dt": "Purchase Order"}, fields=["fieldname", "label", "fieldtype"]))

print("\n=== SAMPLE ITEMS / SUPPLIERS (for demo docs) ===")
print("items:", frappe.get_all("Item", limit=5, pluck="name"))
print("suppliers:", frappe.get_all("Supplier", limit=5, pluck="name"))
print("UOMs:", frappe.get_all("UOM", limit=5, pluck="name"))

print("\n=== WAREHOUSES ===")
print(frappe.get_all("Warehouse", fields=["name", "is_group", "company"], limit=12))

print("\n=== PROPERTY SETTERS on Supplier banking-ish fields ===")
for ps in frappe.get_all("Property Setter", filters={"doc_type": "Supplier"}, fields=["name", "field_name", "property"], limit=20):
    print(ps)

print("\n=== BANK ACCOUNTS (for payment demo) ===")
print(frappe.get_all("Account", filters=[["account_type", "=", "Bank"], ["is_group", "=", 0]], fields=["name", "company"], limit=8))

print("\nDONE")
