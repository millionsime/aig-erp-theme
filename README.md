### AIG Custom Theme

AIG custom theme + AIG **foundation layer** (seeded master data, leave workflow,
committee guard, developer guardrails, permissions).

### What ships in this app

| Layer | Carrier |
|---|---|
| Configuration (custom fields, property setters, AIG roles, workflows incl. AIG Leave Approval, holiday lists, fix leave types, Custom DocPerms filtered to AIG roles) | `fixtures/` re-applied on every `bench migrate`; tax templates/withholding categories are runtime-built instead (see step 6) |
| New DocTypes (AIG Assigned Committee Member child, AIG Minimum ERP Settings single) | `aig_custom_theme/doctype/` (app JSONs) |
| Master data (Company, Fiscal Years EC, Cost Centers, Warehouses, Departments, Designations, Roles, Holiday Lists incl. 2019 EC with assigned company coverage, Settings defaults) | idempotent seed in `aig_custom_theme/setup/seed.py` reading `aig_custom_theme/setup/data/*.json` |
| Core logic (Leave Approver from Reports To, no-self-approval leave guard, committee `only assigned member may decide` guard, warehouse user permission helper, developer guardrails) | Python in `aig_custom_theme/` wired via `hooks.py` (`doc_events`, `permission_query_conditions`, `has_permission`) — deliberately NOT database Server Scripts |
| Per-user warehouse isolation | `bench --site <site> execute custom_theme.aig_custom_theme.setup.apply_user_permissions.run` reading a CSV `user,enterprise` (per-user data — never in git) |

Edit names (business units, isolated warehouses, enterprise-scoped stores, role map, module maps) by editing the JSON data files and re-running the seed; the seed is existence-checked and idempotent.

### Deploying to production

Order matters:

```bash
git pull                      # on the prod bench host
cd frappe-bench
bench get-app https://github.com/millionsime/aig-erp-theme custom_theme --branch main   # first time only
bench update --pull           # subsequent updates
bench --site <site> install-app custom_theme                # first time only
bench --site <site> migrate   # syncs doctypes, runs the seed patch, re-applies fixtures
bench build && bench --site <site> clear-website-cache
```

Then the manual steps (these live in site config / DB, never in git):

1. `bench set-config -g server_script_enabled 1` — the AIG business guard
   Server Scripts (CC guards, committee majority, three-way match...) do
   nothing without it.
2. `bench --site <site> set-config aig_ethiopian_calendar 1` — enables the
   Ethiopian calendar presentation layer (separate app).
3. `bench --site <site> execute custom_theme.aig_custom_theme.setup.apply_user_permissions.run --kwargs "{'csv_path': '/tmp/user_enterprises.csv'}"` —
   warehouse isolation per user (copy the CSV from your private template).
4. Developer mode OFF in System Settings (production shouldn't run in dev mode
   — DocTypes here are app JSON files and don't need it).
5. Chart of Accounts: a fresh site gets ERPNext's standard CoA. To adopt the
   AIG corrected v2 CoA use the documented importer chain in the
   `aig-erp-config` repo (scripts 80 purge → 81 preflight → 83 import → 84/86
   wiring → 85 health) BEFORE go-live postings.
6. Tax configuration: the AIG tax templates and withholding categories are
   deliberately NOT fixtures (they hardwire CoA-2.0 account names 21402/21401/
   21403 that only exist after step 5). After the CoA importer chain runs:

   ```bash
   bench --site <site> execute custom_theme.aig_custom_theme.setup.ensure_tax_setup.run
   ```

   Idempotent: on a site still on the standard CoA it is a safe no-op.

> Note: sites running the AIG standby theme on the *current* CoA keep their
> tax configuration as-is — `ensure_tax_setup` is only needed on sites that
> (re)build from scratch or (swap) to the AIG v2 CoA.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app custom_theme
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/custom_theme
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade
### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
