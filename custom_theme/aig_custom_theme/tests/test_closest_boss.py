# Closest-boss guard: unit tests against the guard directly.
#
# A stub document is used so the five cases exercise the guard logic without
# needing Frappe to accept a workflow transition; the end-to-end path is covered
# separately in test_inventory_flow.py.

import frappe

from custom_theme.aig_custom_theme.inventory import guards
from custom_theme.aig_custom_theme.tests import factory


class _Before:
	def __init__(self, state):
		self.workflow_state = state

	def get(self, key, default=None):
		return getattr(self, key, default)


class _Stub:
	def __init__(self, before_state, now_state, requester, name="AIGTEST-MR"):
		self._before = _Before(before_state) if before_state else None
		self.workflow_state = now_state
		self.aig_requested_by = requester
		self.owner = requester
		self.name = name

	def is_new(self):
		return self._before is None

	def get(self, key, default=None):
		return getattr(self, key, default)

	def get_doc_before_save(self):
		return self._before


def _case(label, user, before, now, requester, expect_block):
	previous = frappe.session.user
	try:
		frappe.set_user(user)
		doc = _Stub(before, now, requester)
		try:
			guards.enforce_closest_boss(doc)
			blocked, reason = False, ""
		except frappe.PermissionError as e:
			blocked, reason = True, str(e)[:80]
		return {
			"case": label,
			"result": "PASS" if blocked == expect_block else "FAIL",
			"blocked": blocked,
			"detail": reason,
		}
	finally:
		frappe.set_user(previous)


def run():
	frappe.flags.aig_test_site = True
	out = {"cases": []}
	emp = factory.email("employee")
	leader = factory.email("team_leader")
	head = factory.email("enterprise_head")
	ceo = factory.email("ceo")

	out["chain"] = {
		"employee_boss": guards.closest_boss_user(emp),
		"employee_boss_expected": leader,
		"ceo_boss": guards.closest_boss_user(ceo),
	}

	out["cases"].append(_case("closest boss may approve", leader,
							  "Pending Store Review", "Pending Enterprise Approval", emp, False))
	out["cases"].append(_case("wrong user blocked", head,
							  "Pending Store Review", "Pending Enterprise Approval", emp, True))
	out["cases"].append(_case("no boss on record falls back", head,
							  "Pending Enterprise Approval", "Approved", ceo, False))
	out["cases"].append(_case("requester cannot approve own", emp,
							  "Pending Store Review", "Pending Enterprise Approval", emp, True))

	frappe.db.set_single_value("AIG Minimum ERP Settings", "enable_closest_boss_guard", 0)
	out["cases"].append(_case("toggle off allows role approver", head,
							  "Pending Store Review", "Pending Enterprise Approval", emp, False))
	frappe.db.set_single_value("AIG Minimum ERP Settings", "enable_closest_boss_guard", 1)

	out["cases"].append(_case("unrelated transition untouched", head,
							  "Draft", "Pending Store Review", emp, False))

	out["passed"] = sum(1 for c in out["cases"] if c["result"] == "PASS")
	out["failed"] = sum(1 for c in out["cases"] if c["result"] == "FAIL")
	return out
