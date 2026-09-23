app_name = "custom_theme"
app_title = "AIG Custom Theme"
app_publisher = "aig-tech"
app_description = "AIG theme logo coor"
app_email = "simemillion@gmail.com"
app_license = "mit"

app_include_css = "/assets/custom_theme/css/custom_theme.css"
app_include_js = "/assets/custom_theme/js/aig_desk.js"

# Auth pages (login, forgot password, etc.)
# Bump ?v= when changing these assets so browsers drop their cached copy.
web_include_css = "/assets/custom_theme/css/aig_login.css?v=4"
web_include_js = "/assets/custom_theme/js/aig_login.js?v=4"

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

# before_install = "custom_theme.install.before_install"
# after_install = "custom_theme.install.after_install"

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

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

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

