# How we work on AIG ERP

## The rule
Every configuration change lives in this app as a file. Only business data
(invoices, items, employees...) lives only in a site's database.

| What | Where |
|---|---|
| Custom fields, form changes, client/server scripts, workflows, roles, permissions, print formats, reports, notifications | this app, `custom_theme/fixtures/` |
| New DocTypes | this app, as JSON (create locally, developer mode on, "Custom?" unchecked, module = an AIG module) |
| Company, chart of accounts, cost centers | `aig-erp-config` scripts, run once per site |
| ERPNext / Frappe / HRMS code | never edited; versions pinned in the infra repo's `apps.json` |

## Branches
- `feature/inventory` is what the server runs. Nobody commits to it directly.
- Work on `feature/<topic>`, open a pull request, get one review, merge.
- Merging triggers the server build and deploy.

## Never
- Change configuration on the server. It is overwritten by the next deploy and nobody else gets it.
- Edit files under `apps/frappe`, `apps/erpnext` or `apps/hrms`.
- Commit database dumps, `.env` files or passwords.

## Daily loop
```bash
# get everyone's latest work
~/aig-erpnext-infra/scripts/sync-pull.sh

# after changing something in the UI
~/aig-erpnext-infra/scripts/sync-push.sh "what I changed"
# then open the pull request link it prints
```

## Removing something
Fixtures add and update, they never delete. To remove a field or script
everywhere, delete it locally, re-export, and add a patch in
`custom_theme/patches/` that deletes it on other sites.
