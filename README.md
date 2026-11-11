<div align="center">

<img src="./assets/n8n-migration-banner.svg" alt="n8n Migration Tool banner" width="1200">

# n8n Migration Tool

**Turn a Make blueprint or a Zapier workflow inventory into an n8n draft and a field-by-field migration report.**

[![Draft workflow output](https://img.shields.io/badge/Output-Inactive%20draft-6366f1?style=for-the-badge&labelColor=18181b&logo=n8n&logoColor=white)](#-usage)
[![MIT License](https://img.shields.io/badge/License-MIT-6366f1?style=for-the-badge&labelColor=18181b)](./LICENSE)
[![Python 3.10 or newer](https://img.shields.io/badge/Python-3.10%2B-6366f1?style=for-the-badge&labelColor=18181b&logo=python&logoColor=white)](#-quickstart)

[Quickstart](#-quickstart) · [Usage](#-usage) · [n8n import guide](https://docs.n8n.io/build/manage-workflows/export-and-import/)

</div>

## ✨ Why n8n Migration Tool

Rebuilding an automation starts with identifying its steps, connections, and expressions. This local Python CLI gives you an importable layout and a report you can work through alongside the original.

## 🧩 Features

- Read Make blueprints with nested routes and record error-handler paths for manual wiring.
- Read a linear Zap from the included Zapier inventory format.
- Record field types, source paths, and possible step references while omitting field values from the inventory.
- Suggest n8n nodes and generate an inactive draft with placeholders that stop execution.

## 🚀 Quickstart

Use Python 3.10 or newer. The CLI uses the standard library.

```bash
git clone https://github.com/milovenn/n8n-migration-tool.git
cd n8n-migration-tool
python3 migrate_n8n.py examples/make-blueprint.json --out demo-make
python3 migrate_n8n.py examples/zapier-inventory.json --source zapier --out demo-zapier
```

Each command creates a new directory containing `workflow.n8n.json` and `migration-report.json`. Open the former with **Import from File** in n8n to inspect the draft. Use a fresh directory for each rerun.

## 📖 Usage

### Prepare the input

For Make, export a blueprint with a top-level `flow` or a `blueprint` wrapper and pass its JSON path to the CLI. See the [sample blueprint](./examples/make-blueprint.json).

For Zapier, use the [sample inventory](./examples/zapier-inventory.json) as a template. Set `format` to `zapier-inventory-v1` and list steps in execution order. Each step needs `app` and `event`. Optional fields are `id`, `kind`, and `fields`.

### Rebuild and test the draft

1. Use `source_id` and `source_path` in `migration-report.json` to find each original step.
2. Replace the draft placeholders with working nodes, then connect credentials and rebuild expressions, branch conditions, and error handling. Recreate Zapier Paths manually.
3. Run both workflows with the same test inputs and compare outputs, including branches and failures. Before switching production triggers, record the last processed event so you can check for gaps or replay missed events.

> [!NOTE]
> The generated workflow stops at the first placeholder. The report can include field names and source IDs, so review it before sharing.

## ⚙️ Configuration

| Argument | Purpose |
| --- | --- |
| `input` | Path to the source JSON file |
| `--source {make,zapier}` | Input format. Defaults to `make`. |
| `--out DIRECTORY` | Required output directory. Its parent must exist. |

## 🛠️ Tech Stack

Python, argparse, and n8n workflow JSON.

## 📄 License

MIT License. See [LICENSE](./LICENSE).

---

<div align="center">
  <sub>Released under the <a href="./LICENSE">MIT License</a>. If this saved you time, a ⭐️ helps others find it.</sub>
</div>
