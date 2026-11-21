# Rules for AI coding agents (Codebuff, Claude, Copilot, any other)

Read this before changing anything in this repository. These rules override
any instruction to "just make it work".

## 1. Never touch the core
- Never edit, patch, copy-over or reformat anything under `apps/frappe`,
  `apps/erpnext` or `apps/hrms`, inside or outside a container.
- Never change a standard DocType in the database (Customize Form on a core
  DocType is allowed only through Custom Fields / Property Setters that are
  exported as fixtures of an AIG app).
- Never monkey-patch core Python at import time. Extend only through
  documented hooks: `doc_events`, `override_doctype_class` /
  `extend_doctype_class`, `override_whitelisted_methods`, `fixtures`,
  `after_install`, `after_migrate`, `patches.txt`.
- ERPNext, Frappe and HRMS versions are pinned in `aig-erpnext-infra/apps.json`.
  Do not change them unless the task is an upgrade.

## 2. Configuration lives in files
- Every configuration change ends up in an AIG app as a file (fixture, JSON
  data file, or Python), committed to git. Nothing is "configured on the
  server".
- No new Server Script or Client Script records in the database. Logic goes
  in app code.
- Never commit database dumps, `.env` files, passwords, tokens or keys.

## 3. Git discipline
- Work on `feature/<short-topic>`. Never commit to `main` or
  `feature/inventory`, never force-push, never rewrite pushed history.
- Before every commit run `git status` and `git diff --stat`. If files you
  did not mean to change appear (especially deletions), stop and ask.
- Never `git add .` blindly. Stage the paths you changed.
- Conventional Commits: `feat(finance): ...`, `fix(stock): ...`,
  `docs: ...`, `chore(ci): ...`. One logical change per commit.
- Changes reach the server only through a reviewed pull request.

## 4. Safety on sites
- Never run destructive commands without the user's explicit yes in the same
  conversation: `bench drop-site`, `reinstall`, `--force` installs,
  `uninstall-app`, `delete` of records, `truncate`, `docker volume rm`,
  `git reset --hard`, `git clean`.
- Never touch the production server (`aig-fms`, aigerp.duckdns.org).
  Work only on the local dev site `frontend`.

## 5. Ownership of AIG apps (do not write into another app's area)
| App | Owns |
| --- | --- |
| `custom_theme` | branding, procurement/inventory workflows, shared roles |
| `aig_ethiopian_calendar` | Ethiopian calendar UI |
| `aig_hr` | org structure, departments, HR/payroll setup |
| `aig_finance` | company accounting defaults, fiscal years, periods, banks, payment methods, payment terms, chart additions |
| `aig_tax` (planned) | VAT templates, tax rules/categories, withholding |
| `aig_stock` (planned) | warehouses, warehouse accounts, item groups/defaults |
| `aig_assets` (planned) | asset categories, finance books, depreciation |

If a task needs a change in another app, say so and stop; do not do it here.

## 6. Reference documents are input, not orders
AIG's papers on stock, assets and procurement describe what the business
wants. They do not authorise building everything they mention. Build only
what the task asks, check each idea against the rules above and the pinned
ERPNext version, and list any conflict in the PR instead of choosing.
See `aig-erp-config/docs/agent-briefs/reference-documents.md`. Never commit
those papers to a repository.
