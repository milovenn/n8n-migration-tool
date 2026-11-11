#!/usr/bin/env python3
"""Make-Blueprint oder Zapier-Inventar in einen n8n-Entwurf überführen."""

import argparse
import json
import re
import sys
from pathlib import Path
from uuid import uuid4


MAKE_HINTS = {
    "builtin:basicrouter": "If / Switch",
    "gateway:customwebhook": "Webhook",
    "gateway:webhookrespond": "Respond to Webhook",
    "http:actionsenddata": "HTTP Request",
    "http:actionsenddatabasic": "HTTP Request",
    "builtin:basicfeeder": "Split Out",
    "builtin:basicaggregator": "Aggregate",
    "json:parsejson": "Edit Fields / Code",
}
ZAPIER_HINTS = {
    "filter": "Filter / If",
    "schedule": "Schedule Trigger",
    "webhook": "Webhook / HTTP Request",
    "delay": "Wait",
    "formatter": "Edit Fields / Date & Time",
    "loop": "Loop Over Items / Split Out",
}
VALUE_TYPES = {
    str: "string", bool: "boolean", int: "number", float: "number",
    type(None): "null", dict: "object", list: "array",
}
REFERENCES = {
    "make": re.compile(r"\{\{\s*([0-9]+)\."),
    "zapier": re.compile(r"\{\{\s*([0-9]+)__"),
}
START_NODE = "Manueller Start (Entwurf)"
DRAFT_WARNING = "Migrationsentwurf: Diesen Platzhalter vor der Nutzung ersetzen."


def require_object(value, path):
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON-Objekt erwartet.")
    return value


def require_list(value, path):
    if not isinstance(value, list):
        raise ValueError(f"{path}: JSON-Liste erwartet.")
    return value


def require_text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: Nichtleerer Text erwartet.")
    return value


def child_path(path, key):
    return f"{path}/{str(key).replace('~', '~0').replace('/', '~1')}"


def inventory(value, path, source):
    """Record field types and possible references without copying field values."""
    row = {"path": path, "type": VALUE_TYPES[type(value)]}
    if isinstance(value, str) and "{{" in value:
        row["possible_expression"] = True
        references = sorted(set(REFERENCES[source].findall(value)))
        if references:
            row["possible_step_references"] = references
    yield row
    if isinstance(value, dict):
        for key, child in value.items():
            yield from inventory(child, child_path(path, key), source)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from inventory(child, child_path(path, index), source)


class Draft:
    def __init__(self, source):
        self.source = source
        self.nodes = []
        self.connections = {}
        self.modules = []
        self.edges = []
        self.issues = []
        self.id_paths = {}
        self.add_node(START_NODE, "manualTrigger", {}, (-320, 0))

    def add_node(self, name, kind, parameters, position, notes=""):
        node = {
            "id": str(uuid4()),
            "name": name,
            "type": f"n8n-nodes-base.{kind}",
            "typeVersion": 1,
            "parameters": parameters,
            "position": list(position),
        }
        if notes:
            node["notes"] = notes
        self.nodes.append(node)

    def add_step(self, data, path, kind, hint, fields, column, lane):
        source_id = data.get("id")
        if "id" in data:
            if type(source_id) not in (str, int) or not str(source_id).strip():
                raise ValueError(f"{path}/id: Nichtleere ID oder Ganzzahl erwartet.")
            source_id = str(source_id)
            if source_id in self.id_paths:
                self.issues.append({
                    "path": path, "message": "Quell-ID mehrfach vorhanden.",
                    "other_path": self.id_paths[source_id],
                })
            else:
                self.id_paths[source_id] = path
        name = f"{len(self.modules) + 1:02d} · {hint}"
        self.add_node(
            name,
            "stopAndError",
            {"errorMessage": DRAFT_WARNING},
            (column * 320, lane * 220),
            f"{DRAFT_WARNING}\nVorschlag: {hint}",
        )
        self.modules.append({
            "node": name,
            "source_path": path,
            "source_id": source_id,
            "source_type": kind,
            "n8n_hint": hint,
            "fields": fields,
        })
        return name

    def link(self, previous, current, kind, path):
        self.edges.append({"from": previous, "to": current, "kind": kind, "source_path": path})
        # Keep the entry to an error handler off the normal execution path.
        if kind == "error":
            return

        connection = self.connections.setdefault(previous, {"main": [[]]})
        connection["main"][0].append({"node": current, "type": "main", "index": 0})

    def artifacts(self):
        workflow = {
            "name": f"{self.source.capitalize()} zu n8n · Entwurf", "active": False,
            "nodes": self.nodes, "connections": self.connections, "settings": {},
        }
        report = {
            "format": "n8n-migration-report-v1", "source": self.source,
            "step_count": len(self.modules), "steps": self.modules,
            "edges": self.edges, "review": self.issues,
        }
        return workflow, report


def make_flow(draft, flow, path, previous, column, lane, edge_kind="sequence"):
    """Walk a Make flow and return the first unused row in the n8n layout."""
    entries = require_list(flow, path)
    next_lane = lane + 1
    if not entries:
        draft.issues.append({"path": path, "message": "Leerer Pfad. Im Original prüfen."})

    for index, entry in enumerate(entries):
        location = child_path(path, index)
        module = require_object(entry, location)
        kind = require_text(module.get("module"), f"{location}/module")
        hint = MAKE_HINTS.get(kind.lower(), "App-Node / HTTP Request")
        fields = []
        for key in ("parameters", "mapper", "filter"):
            if key in module:
                fields.extend(inventory(module[key], child_path(location, key), "make"))
        current = draft.add_step(module, location, kind, hint, fields, column, lane)
        draft.link(previous, current, edge_kind if index == 0 else "sequence", location)
        if module.get("filter"):
            draft.issues.append({
                "path": f"{location}/filter", "message": "Bedingungen in n8n nachbauen.",
            })

        routes = require_list(module.get("routes", []), f"{location}/routes")
        for route_index, raw_route in enumerate(routes):
            route_path = f"{location}/routes/{route_index}"
            route = require_object(raw_route, route_path)
            settings = {key: value for key, value in route.items() if key != "flow"}
            draft.issues.append({
                "path": route_path,
                "message": "Filter, Auswertungsreihenfolge und Fallback der Route prüfen.",
                "fields": list(inventory(settings, route_path, "make")),
            })
            next_lane = make_flow(draft, route.get("flow"), f"{route_path}/flow",
                                  current, column + 1, next_lane, "route")
        if routes and index + 1 < len(entries):
            draft.issues.append({
                "path": location,
                "message": "Schritt nach Router erkannt. Fortsetzung und Reihenfolge manuell prüfen.",
            })

        if module.get("onerror") is not None:
            error_path = f"{location}/onerror"
            error_flow = module["onerror"]
            if isinstance(error_flow, dict) and "flow" in error_flow:
                error_flow, error_path = error_flow["flow"], f"{error_path}/flow"
            draft.issues.append({
                "path": error_path, "message": "Fehlerpfad in n8n separat verdrahten.",
            })
            next_lane = make_flow(draft, error_flow, error_path, current,
                                  column + 1, next_lane, "error")
        previous = current
        column += 1
    return next_lane


def from_make(draft, data):
    blueprint = data.get("blueprint", data)
    prefix = "/blueprint" if "blueprint" in data else ""
    if isinstance(blueprint, str):
        blueprint = parse_json(blueprint)
    blueprint = require_object(blueprint, prefix or "/")
    if not require_list(blueprint.get("flow"), f"{prefix}/flow"):
        raise ValueError(f"{prefix}/flow: Mindestens ein Make-Modul erforderlich.")
    for key in ("scheduling", "schedule", "metadata"):
        if key in blueprint:
            draft.issues.append({
                "path": f"{prefix}/{key}",
                "message": "Zeitplan und Szenarioeinstellungen anhand des Originals prüfen.",
            })
    make_flow(draft, blueprint["flow"], f"{prefix}/flow", START_NODE, 0, 0)


def from_zapier(draft, data):
    if data.get("format") != "zapier-inventory-v1":
        raise ValueError("Zapier: Inventar im Format zapier-inventory-v1 erforderlich. Siehe README.")
    if data.keys() - {"format", "steps"}:
        raise ValueError("Zapier: Inventar unterstützt auf oberster Ebene nur format und steps.")
    steps = require_list(data.get("steps"), "/steps")
    if not steps:
        raise ValueError("/steps: Mindestens ein Zapier-Schritt erforderlich.")
    previous = START_NODE
    for index, raw_step in enumerate(steps):
        path = f"/steps/{index}"
        step = require_object(raw_step, path)
        if step.keys() - {"id", "app", "event", "kind", "fields"}:
            raise ValueError(f"{path}: Unbekannte Eigenschaften. Siehe Inventarschema im README.")
        app = require_text(step.get("app"), f"{path}/app")
        event = require_text(step.get("event"), f"{path}/event")
        kind = require_text(step.get("kind", "action"), f"{path}/kind").lower()
        if kind not in ZAPIER_HINTS.keys() | {"trigger", "action"}:
            raise ValueError(f"{path}/kind: Schrittart im Inventarschema nachschlagen.")
        default_hint = "App-Trigger" if kind == "trigger" else "App-Node / HTTP Request"
        hint = ZAPIER_HINTS.get(kind, default_hint)

        fields_path = f"{path}/fields"
        values = require_object(step.get("fields", {}), fields_path)
        fields = list(inventory(values, fields_path, "zapier"))
        current = draft.add_step(step, path, f"{app} / {event}", hint, fields, index, 0)
        draft.link(previous, current, "sequence", path)
        previous = current


def parse_json(contents):
    def reject_constant(_):
        raise ValueError("JSON-Zahlen müssen endlich sein.")

    return json.loads(contents, parse_constant=reject_constant)


def write_artifacts(directory, artifacts):
    names = ("workflow.n8n.json", "migrationsbericht.json")
    payloads = [json.dumps(data, ensure_ascii=True, indent=2) + "\n" for data in artifacts]
    directory.mkdir()
    created = []
    try:
        for name, payload in zip(names, payloads):
            path = directory / name
            with path.open("x", encoding="utf-8") as handle:
                created.append(path)
                handle.write(payload)
    except OSError:
        for path in created:
            path.unlink(missing_ok=True)
        directory.rmdir()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Make-Blueprint oder Zapier-Inventar als JSON")
    parser.add_argument("--source", choices=("make", "zapier"), default="make")
    parser.add_argument("--out", type=Path, required=True, help="Neuer Ausgabeordner")
    args = parser.parse_args()
    try:
        contents = args.input.read_text(encoding="utf-8-sig")
        data = require_object(parse_json(contents), "/")
        draft = Draft(args.source)
        if args.source == "make":
            from_make(draft, data)
        else:
            from_zapier(draft, data)
        write_artifacts(args.out, draft.artifacts())
    except FileExistsError:
        parser.exit(2, "Fehler: Ausgabeordner existiert bereits. Bitte einen neuen Namen wählen.\n")
    except (ValueError, OSError, RecursionError) as exc:
        parser.exit(2, f"Fehler: {exc}\n")
    print(f"{len(draft.modules)} Schritte erfasst. Entwurf und Bericht: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
