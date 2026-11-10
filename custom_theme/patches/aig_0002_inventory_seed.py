# Patch: seed the inventory layer on `bench migrate` for every site.
#
# Runs after model sync (see patches.txt) so the Custom Fields and DocTypes the
# seed touches already exist. Idempotent: a second run creates nothing.

import frappe


def execute():
	frappe.flags.in_patch = True
	from custom_theme.aig_custom_theme.setup import inventory_seed

	inventory_seed.run_all()
