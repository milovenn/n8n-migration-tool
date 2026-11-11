# Make und Zapier nach n8n migrieren

Wenn du einen Workflow in n8n nachbaust, musst du zuerst herausfinden, welche Schritte zusammenhängen und woher die Daten kommen. Dieses Python-Skript übernimmt die Bestandsaufnahme. Du bekommst einen Entwurf für den n8n-Editor und einen Bericht, mit dem du die Schritte im Original wiederfindest.

## In zwei Minuten ausprobieren

Du brauchst Python 3.10 oder neuer. Das Skript läuft lokal und benötigt keine zusätzlichen Pakete.

```bash
python3 migrate_n8n.py examples/make-blueprint.json --out demo-make
```

`--out` gibt den Namen eines neuen Ordners an. Darin findest du zwei Dateien.

- **`workflow.n8n.json`** öffnest du im n8n-Editor über **Import from File**. Der Workflow ist inaktiv und enthält einen manuellen Start und beschriftete Platzhalter. Ein Testlauf stoppt am ersten Platzhalter. [Workflows importieren](https://docs.n8n.io/build/manage-workflows/export-and-import/)
- **`migrationsbericht.json`** zeigt Quell-IDs, Feldpfade, Datentypen, mögliche Ausdrucksreferenzen und Prüfpunkte. Der Bericht enthält Feldnamen und IDs. Schau diese vor dem Teilen durch, wenn sie interne Informationen enthalten.

Das Make-Beispiel zeigt einen Webhook, einen Router mit zwei Pfaden und einen Fehlerpfad. Vergleiche den Entwurf mit dem Bericht, um zu sehen, wie die Schritte zusammenhängen.

## Ein Make-Szenario vorbereiten

Öffne das Szenario in Make und wähle im Drei-Punkte-Menü **Export blueprint**. [Make-Hilfe zum Blueprint-Export](https://help.make.com/blueprints)

```bash
python3 migrate_n8n.py mein-szenario.blueprint.json --out mein-szenario-n8n
```

Suche im Bericht unter `steps` nach dem gewünschten Schritt. Über `source_id` und `source_path` findest du ihn im Blueprint. Unter `fields` stehen Feldpfade und Datentypen. Die zugehörigen Werte bleiben im Original.

Das Skript liest Blueprints mit einer `flow`-Liste, auch wenn sie in `blueprint` eingebettet sind. Es erfasst `parameters`, `mapper` und `filter` sowie verschachtelte `routes[].flow` und `onerror`-Pfade. Router-Kanten zeigen den Aufbau. Die Bedingungen, Reihenfolge und Fallbacks legst du in n8n fest. Fehlerpfade stehen im Bericht, ihr Einstieg bleibt im n8n-Entwurf vom normalen Ablauf getrennt.

## Einen Zap vorbereiten

Nutze den Zap-Editor oder einen Zapier-Export als Vorlage für ein Inventar. Trage die Schritte eines **linearen** Zaps in der Reihenfolge ein, in der sie ausgeführt werden. Bei Zapier Paths dokumentierst du die Zweige samt Bedingungen separat für den manuellen Nachbau. [Zapier-Hilfe zum JSON-Workflow-Export](https://help.zapier.com/hc/en-us/articles/8496308481933-Import-and-export-Zaps-in-your-Team-or-Enterprise-account) · [Zapier-Hilfe zum Kontodatenexport](https://help.zapier.com/hc/en-us/articles/8496289406349-Export-or-delete-your-Zapier-account-data)

Kopiere [das Beispielinventar](examples/zapier-inventory.json) und passe es an. `format` bleibt `zapier-inventory-v1`. Jeder Eintrag in `steps` braucht `app` und `event`. `id`, `kind` und `fields` sind optional. Für `kind` stehen `trigger`, `action`, `filter`, `schedule`, `webhook`, `delay`, `formatter` und `loop` zur Auswahl. Standard ist `action`. Wenn du nur Feldnamen erfassen möchtest, kannst du als Feldwerte `null` eintragen.

```bash
python3 migrate_n8n.py examples/zapier-inventory.json --source zapier --out demo-zapier
```

## Den Entwurf in n8n fertigstellen

1. **In einer Testinstanz importieren.** Wenn du n8n selbst betreibst, prüfe für die Zielinstanz HTTPS, Webhook-Adresse, Zeitzone, persistente Daten, Verschlüsselungsschlüssel und Backup-Wiederherstellung. [n8n mit Docker Compose einrichten](https://docs.n8n.io/deploy/host-n8n/install-options/install-using-docker-compose/)
2. **Platzhalter ersetzen und Konten verbinden.** Richte Trigger und Aktionen anhand des Originals ein. Bei `{{1.email}}` in Make verweist die `1` auf den Quellschritt. Wenn die Adresse im aktuellen n8n-Item unter `email` steht, kannst du `{{ $json.email }}` verwenden. Prüfe die tatsächliche Node-Ausgabe. Der Bericht erkennt vor allem einfache Referenzen mit numerischen IDs. [Expressions in n8n](https://docs.n8n.io/code/expressions/)
3. **Mit denselben Eingaben testen.** Vergleiche die Ergebnisse in beiden Systemen. Teste auch leere Felder, mehrere Elemente, jeden Zweig, Fehler und doppelte Ereignisse. Lass während des Vergleichs höchstens einen Workflow in produktive Ziele schreiben.
4. **Trigger umschalten.** Pausiere den alten Trigger, merke dir das letzte verarbeitete Ereignis und aktiviere den neuen Trigger. Prüfe die ersten Läufe auf Lücken und Duplikate. Falls die Umstellung scheitert, pausiere den neuen Trigger, aktiviere den alten wieder und arbeite fehlende Ereignisse ab der gesicherten Marke nach.

## Lohnt sich die Migration?

Rechne das bisherige Abo gegen Hosting, Backups, Monitoring, Pflege und gegebenenfalls n8n-Lizenzkosten. Bei 450 € bisherigen und 150 € neuen laufenden Kosten bleiben monatlich 300 € übrig. Kostet die Umstellung einmalig 1.800 €, amortisiert sie sich nach sechs Monaten. Die Nettoersparnis im ersten Jahr beträgt in diesem Beispiel 1.800 €. [n8n-Lizenz nach Betriebsmodell](https://support.n8n.io/article/can-i-use-your-license-for-my-use-case)
