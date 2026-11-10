app_name = "custom_theme"
app_title = "AIG Custom Theme"
app_publisher = "aig-tech"
app_description = "AIG theme + foundation layer (seed, org hooks, guardrails)"
app_email = "simemillion@gmail.com"
app_license = "mit"

# ------------------------------------------------------------------ roles
# The AIG-prefixed role set (mapping in aig_custom_theme/setup/data/role_map.json).
# Used to filter Custom DocPerm fixtures so we ship only permissions we own.
AIG_ROLES = [
	"AIG Accountant",
	"AIG Asset Developer",
	"AIG Chief Accountant",
	"AIG CEO",
	"AIG Corporate",
	"AIG Deputy",
	"AIG End User",
	"AIG Enterprise Head",
	"AIG Evaluation Committee",
	"AIG Finance",
	"AIG Finance Head",
	"AIG General Store Keeper",
	"AIG HR Director",
	"AIG HR Expert",
	"AIG HR Manager",
	"AIG HR Developer",
	"AIG Inventory Administrator",
	"AIG Inventory Developer",
	"AIG Internal Auditor",
	"AIG Main Store Administrator",
	"AIG Plan and Budget",
	"AIG Procurement Director",
	"AIG Procurement Developer",
	"AIG Procurement Officer",
	"AIG Property Admin Expert",
	"AIG Purchase Committee",
	"AIG Record Office",
	"AIG Store Expert",
	"AIG Store Keeper",
	"AIG Store Manager",
	"AIG Team Leader",
]

app_include_css = "/assets/custom_theme/css/custom_theme.css?v=2"
app_include_js = "/assets/custom_theme/js/aig_desk.js?v=2"

# Auth pages (login, forgot password, etc.)
# Bump ?v= when changing these assets so browsers drop their cached copy.
web_include_css = "/assets/custom_theme/css/aig_login.css?v=4"
web_include_js = "/assets/custom_theme/js/aig_login.js?v=4"

# AIG configuration fixtures (2026-09-28): everything the site carried only in
# its DB is exported here via `bench --site frontend export-fixtures` and
# re-applied on every `bench migrate` on any deployment server. The phase-2/3
# build-out scripts in ~/aig-erp-config/scripts remain the source of truth
# for HOW these records were built; the fixtures capture the resulting state
# for reproducible installs.
fixtures = [
	# Custom DocPerm filtered to the AIG role set (2026-10-06): we only ship
	# permissions bound to roles we own; desktop/standard roles keep their own
	# erpnext/ hrms-defined rows.
	{"dt": "Custom DocPerm", "filters": [["role", "in", AIG_ROLES]]},
	{"dt": "Custom Field", "filters": [["fieldname", "like", "aig%"]]},
	{"dt": "Property Setter"},
	{"dt": "Server Script"},
	{"dt": "Client Script"},
	# Workflow moves below: it imports AFTER its Workflow State / Action rows.
	{"dt": "Role", "filters": [["name", "like", "AIG%"]]},
	# Leave Types we own (the 3 the foundation layer ships): Annual + Maternity
	# are foundation-owned; Sick keeps its AIG row so no MIS STAT uses it.
	{"dt": "Leave Type", "filters": [["name", "in", ["Annual", "Sick", "Maternity"]]]},
	# NOTE: User Permission is per-user data (docs section 3.4) and is
	# deliberately NOT a fixture anymore. Use the helper instead:
	#   bench --site <site> execute aig_custom_theme.setup.apply_user_permissions.run
	# CoA-2.0-linked records are NOT fixtures (2026-10-31): the AIG tax templates
	# and the two AIG Tax Withholding Categories hardwire CoA account names
	# (21402 VAT 15%, 21401 VAT-WH 7.5%, 21403 WHT 3%) that only exist AFTER the
	# AIG CoA importer chain runs (aig-erp-config scripts 80-86). Importing them
	# before that aborts every fresh install with a LinkValidationError. They are
	# rebuilt by:  bench --site <site> execute aig_custom_theme.setup.ensure_tax_setup.run
	{"dt": "Module Def", "filters": [["name", "like", "AIG%"]]},
	{"dt": "Print Format", "filters": [["name", "like", "AIG%"]]},
	{"dt": "Workspace", "filters": [["name", "like", "AIG%"]]},
	# Workflow fixture chain (2026-10-31): a Workflow validates its states and
	# actions via Link, so own rows MUST import before the Workflow docs. On a
	# fresh install this order is fatal, on frontend it silently skipped all
	# workflow fixtures for years. Workflow itself last.
	{"dt": "Workflow State"},
	{"dt": "Workflow Action Master"},
	{"dt": "Workflow"},
]
# NOTE: custom DocTypes (AIG Committee Signoff, AIG Stock Migration Batch/Row)
# cannot be exported as fixtures outside developer mode; they are created
# idempotently by the script chain in ~/aig-erp-config/scripts (132 et al.),
# which runs after migrate on a fresh install. The same chain also owns the
# one non-'aig'-prefixed field (Purchase Receipt.model_42_handover_document).
# The Custom Field 'aig%' filter also covers the AIG HR fields that carry the
# aig prefix; hrms/erpnext-created fields (Employee.*, workflow_state, ...)
# are re-created by their own apps on sync and are deliberately not captured.
# Property Setter / Custom DocPerm are exported UNFILTERED on purpose: rows
# created by hrms/erpnext syncs duplicate harmlessly on the target, while the
# AIG rows (Company/Cost Center/Warehouse/Account/MR/PO/PR/PI/PE...) are the
# ones that must travel.

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "custom_theme",
# 		"logo": "/assets/custom_theme/logo.png",
# 		"title": "AIG Custom Theme",
# 		"route": "/custom_theme",
# 		"has_permission": "custom_theme.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/custom_theme/css/custom_theme.css"
# app_include_js = "/assets/custom_theme/js/custom_theme.js"

# include js, css files in header of web template
# web_include_css = "/assets/custom_theme/css/custom_theme.css"
# web_include_js = "/assets/custom_theme/js/custom_theme.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "custom_theme/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "custom_theme/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "custom_theme.utils.jinja_methods",
# 	"filters": "custom_theme.utils.jinja_filters"
# }

# Installation
# ------------

# after_install seed: on a FRESH site install-app, this seeds company, fiscal
# years, cost centers, warehouses, departments, designations, roles and the
# settings single from aig_custom_theme/setup/data/*.json. Safe to re-run.
after_install = "custom_theme.aig_custom_theme.setup.seed.run_all"

# Uninstallation
# ------------

# before_uninstall = "custom_theme.uninstall.before_uninstall"
# after_uninstall = "custom_theme.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "custom_theme.utils.before_app_install"
# after_app_install = "custom_theme.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "custom_theme.utils.before_app_uninstall"
# after_app_uninstall = "custom_theme.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "custom_theme.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "custom_theme.notifications.get_notification_config"

# Awesome Bar
# -----------
# Extra search results: list of dicts with label, description, route, index.
# route: ["List", "ToDo"], "/desk/docs/some/page", or "https://example.com"
# awesomebar_search = ["custom_theme.search.awesomebar_results"]

# Permissions
# -----------
# Permissions evaluated in scripted ways

# Developer guardrails (section 2.10 of the foundation design): each AIG *
# Developer role sees only builder records targeting its own module's
# doctypes. Core doctypes (Company, Account, Cost Center, User, Role,
# DocPerm, Fiscal Year...) have no permissions for these roles at all.
w = "custom_theme.aig_custom_theme.guardrails.dev_roles"
permission_query_conditions = {
	"Client Script": f"{w}.permission_query_conditions",
	"Server Script": f"{w}.permission_query_conditions",
	"Workflow": f"{w}.permission_query_conditions",
	"Custom Field": f"{w}.permission_query_conditions",
	"Property Setter": f"{w}.permission_query_conditions",
}
has_permission = {
	"Client Script": f"{w}.has_permission",
	"Server Script": f"{w}.has_permission",
	"Workflow": f"{w}.has_permission",
	"Custom Field": f"{w}.has_permission",
	"Property Setter": f"{w}.has_permission",
}

# Document Events
# ---------------
# Hook on document methods and events

# AIG foundation hooks (app code, never DB Server Scripts -- see docs): 
#  - Employee validate: derive Leave Approver from Reports To (closest boss)
#  - Leave Application validate: no self-approval + closest-boss-only guard
#  - Quality Inspection / Purchase Order / RFQ validate: committee guard
doc_events = {
	"Employee": {
		"validate": "custom_theme.aig_custom_theme.org.leave_approver.set_leave_approver",
	},
	"Leave Application": {
		"validate": "custom_theme.aig_custom_theme.org.workflow_guard.validate",
	},
	"Quality Inspection": {
		"validate": "custom_theme.aig_custom_theme.committee.guard.validate",
},
	"Purchase Order": {
		"validate": "custom_theme.aig_custom_theme.committee.guard.validate",
},
	"Request for Quotation": {
		"validate": "custom_theme.aig_custom_theme.committee.guard.validate",
},
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"custom_theme.tasks.all"
# 	],
# 	"daily": [
# 		"custom_theme.tasks.daily"
# 	],
# 	"hourly": [
# 		"custom_theme.tasks.hourly"
# 	],
# 	"weekly": [
# 		"custom_theme.tasks.weekly"
# 	],
# 	"monthly": [
# 		"custom_theme.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "custom_theme.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "custom_theme.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "custom_theme.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "custom_theme.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["custom_theme.utils.before_request"]
# after_request = ["custom_theme.utils.after_request"]

# Job Events
# ----------
# before_job = ["custom_theme.utils.before_job"]
# after_job = ["custom_theme.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"custom_theme.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

# ------------------------------------------------------------------ inventory
# Added by the inventory layer (2026-11-10). Written as an update() so the
# foundation's doc_events block above stays untouched and readable.
_INV = "custom_theme.aig_custom_theme.inventory.guards"
doc_events.update(
	{
		"Item": {"validate": f"{_INV}.apply_item_group_defaults"},
		"Material Request": {"validate": f"{_INV}.enforce_closest_boss"},
		"Stock Entry": {
			"before_validate": f"{_INV}.classify_stock_entry",
			"before_submit": f"{_INV}.validate_store_manager_approval",
		},
		"Stock Reconciliation": {
			"before_submit": f"{_INV}.require_store_manager_for_reconciliation",
		},
	}
)

# Reorder alerts (daily) and the monthly stock-count reminder. Both no-op when
# their switch in AIG Minimum ERP Settings is off.
scheduler_events = {
	"daily": [f"{_INV}.daily_reorder_alerts"],
	"monthly": [f"{_INV}.monthly_stock_count_reminder"],
}
