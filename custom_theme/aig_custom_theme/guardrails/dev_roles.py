# Developer guardrails (§2.10).
#
# AIG Procurement / HR / Inventory / Asset Developer roles may create and edit
# builder records (Client Script, Server Script, Workflow, Custom Field,
# Property Setter) only when the record's TARGET doctype belongs to the
# developer role's own module. The module -> doctype map lives in
# aig_custom_theme/data/module_doctype_map.json.
#
# Registered in hooks.py: permission_query_conditions (list filtering) and
# has_permission (doc-level check) for the five guarded doctypes.
# Core doctypes (Company, Account, Cost Center, User, Role, DocPerm, Fiscal
# Year...) stay unreachable because these roles hold no Standard permissions
# on them; only System Manager keeps the core.

import json
import os

import frappe
from frappe import _

MAP_FILE = os.path.join(
    os.path.dirname(__file__), "..", "setup", "data", "module_doctype_map.json"
)


def _map():
    with open(MAP_FILE, encoding="utf-8") as f:
        return json.load(f)


def _developer_roles(user=None):
    roles = set(frappe.get_roles(user) if user else frappe.get_roles())
    if "System Manager" in roles:
        return None  # admin bypasses guardrails entirely
    return roles & set(_map()["developers"].keys())


def _allowed_doctypes_for(user):
    devs = _developer_roles(user)
    if not devs:
        return None  # not a developer subject to guardrails
    m = _map()["developers"]
    allowed = set()
    for role in devs:
        allowed |= set(m[role]["doctypes"])
    return allowed


def _target(doc, settings_field):
    if not doc:
        return None
    return doc.get(settings_field)


def permission_query_conditions(user, doctype=None, parenttype=None, **kwargs):
    """SQL fragment restricting developers to builder rows aimed at their own
    module's doctypes. Returns None for admins / non-developers (no extra
    restriction on top of their role permissions)."""
    devs = _developer_roles(user)
    if not devs:
        return None
    m = _map()
    ref_field = m["reference_field"].get(doctype) or m["reference_field"].get(parenttype or "")
    if not ref_field:
        return None
    allowed = _allowed_doctypes_for(user)
    quoted = ", ".join(frappe.db.escape(d) for d in sorted(allowed or {"__none__"}))
    return f"(`tab{doctype}`.`{ref_field}` in ({quoted}) or `tab{doctype}`.`{ref_field}` is null or `tab{doctype}`.`{ref_field}` = '')"


def has_permission(doc, user=None, doctype=None, parenttype=None, ptype=None, **kwargs):
    devs = _developer_roles(user)
    if not devs:
        return None  # not our business; standard permission engine decides
    ref_field = _map()["reference_field"].get(doctype or (doc and doc.doctype))
    if not ref_field or doc is None:
        return True  # untargeted rows (should not exist) or unknown shape
    target = _target(doc, ref_field)
    if not target or target == "":
        return True  # pristine builder row without a target yet
    if target == doctype:  # builder row pointing at itself is allowed only for admins
        return bool(_is_admin()) if user is None or "System Manager" in frappe.get_roles(user) else False
    allowed = _allowed_doctypes_for(user)
    return bool(allowed and target in allowed)
