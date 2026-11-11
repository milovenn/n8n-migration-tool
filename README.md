# Make & Zapier → n8n Migration Tool

Turn a Make blueprint or a Zapier workflow inventory into an **n8n draft** and a **field-by-field migration report**. Use the draft to see how the steps fit together, then use the report to rebuild the logic in n8n.

**Requirements** · Python 3.10+ · Standard library only · Runs locally

## Quick start

From the repository root, run either example. Choose a new directory for `--out`.

```bash
python3 migrate_n8n.py examples/make-blueprint.json --out demo-make
python3 migrate_n8n.py examples/zapier-inventory.json --source zapier --out demo-zapier
```

| Output | What to do with it |
| --- | --- |
| `workflow.n8n.json` | In n8n, open a workflow and choose **Import from File**. The inactive draft shows step placeholders and workflow connections. A manual run stops at the first placeholder. |
| `migration-report.json` | Use the source IDs and JSON paths to find each step in the original. Review the field types, possible step references, and items that need manual work. |

[Import workflows in n8n](https://docs.n8n.io/build/manage-workflows/export-and-import/)

## Prepare your workflow

### Make blueprint

Open your scenario in Make and choose **Export blueprint** from the three-dot menu. Then run:

```bash
python3 migrate_n8n.py my-scenario.blueprint.json --out my-scenario-n8n
```

The script reads a top-level `flow` or one wrapped in `blueprint`. It inventories fields in `parameters`, `mapper`, and `filter` and follows nested routes and error paths. Use `source_id` and `source_path` in the report to find the original values. Route connections show the layout. Recreate filters, evaluation order, and fallbacks in n8n, and wire error paths to the appropriate error outputs.

[Export a Make blueprint](https://help.make.com/blueprints) · [View the example blueprint](examples/make-blueprint.json)

### Zapier inventory

Copy the [example inventory](examples/zapier-inventory.json) and use the Zap editor or export to fill it in. The CLI reads a **single linear Zap** in the inventory format below. For Zapier Paths, document the branches and their conditions for manual reconstruction.

| Field | What to enter |
| --- | --- |
| `format` | Use `zapier-inventory-v1`. |
| `steps` | List steps in execution order. |
| `app`, `event` | Required on each step. Use the app and event names from Zapier. |
| `id` | Optional. Use the source step ID if available. |
| `kind` | Optional. Choose `trigger`, `action`, `filter`, `schedule`, `webhook`, `delay`, `formatter`, or `loop`. Defaults to `action`. |
| `fields` | Optional. Use an object with the field names and sample values. Use `null` when you only need to record a field name. |

```bash
python3 migrate_n8n.py my-zap-inventory.json --source zapier --out my-zap-n8n
```

[Export Zap workflows](https://help.zapier.com/hc/en-us/articles/8496308481933-Import-and-export-Zaps-in-your-Team-or-Enterprise-account) · [Export Zapier account data](https://help.zapier.com/hc/en-us/articles/8496289406349-Export-or-delete-your-Zapier-account-data)

## From draft to production

1. **Import into a test instance.** For self-hosted n8n, verify HTTPS, the webhook URL, timezone, persistent storage, the encryption key, and backup recovery. [Set up n8n with Docker Compose](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose/)
2. **Replace the placeholders.** Configure the real trigger and actions, connect accounts in n8n, and rebuild the expressions against actual node output. For example, Make’s `{{1.email}}` points to source step 1. If the email is on the current n8n item, use `{{ $json.email }}`. The report flags likely references with numeric step IDs. It records field names and source IDs, so review those before sharing. [Expressions in n8n](https://docs.n8n.io/code/expressions/)
3. **Compare results with the same inputs.** Cover empty values, multiple items, each branch, errors, and duplicate events. During the comparison, let only one workflow write to production.
4. **Switch triggers.** Pause the old trigger, record the last processed event, and enable the new trigger. Check the first runs for gaps and duplicates. To roll back, pause the new trigger, reactivate the old one, and replay missing events from the recorded point.

## Estimate the payback period

Subtract monthly hosting, backups, monitoring, maintenance, and any applicable n8n license costs from the subscription savings. In this example, moving from €450 to €150 in monthly costs saves €300 per month. A €1,800 migration pays back in six months and saves €1,800 in the first year. [n8n licensing by use case](https://support.n8n.io/article/can-i-use-your-license-for-my-use-case)
