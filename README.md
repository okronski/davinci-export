# Davinci Resolve Export Python Script

## Voraussetzung
- Das Projekt benutzt [uv](https://docs.astral.sh/uv/) um die Python-Umgebung zu managen.
- Davinci Resolve Studio

## Setup
1. Libraries installieren
```
uv sync
```
2. Medien vorbereiten

`.mov` Dateien, die konvertiert werden sollen, in den `input_data` Ordner verschieben

3. Script ausführen
```
# Mit UI
uv run main.py

# Ohne UI
uv run main.py --headless
```

4. Output

Die fertig gerenderten Videos sind im `out` Ordner gespeichert