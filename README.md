<p align="center"><img src="docs/logo.svg" width="120" alt="Ordnung! logo"></p>

<h1 align="center">Ordnung!</h1>

<p align="center"><b>A document archive for families and small households – folders you already understand, a search that actually finds things.</b><br>
Self-hosted · open source (AGPL-3.0) · German, English, French, Italian</p>

<p align="center"><i>Deutsch: <a href="README.de.md">README.de.md</a></i></p>

![Archive with folder tree, list and preview](docs/screenshots/en/01-archiv.jpg)

## Why another document archive?

Most document managers are built around tags and filters. That is powerful – and most people never warm to it. **Ordnung!** turns it around: **the folders are the truth.** A document lives where you would look for it (`Insurance › Nordlicht › Buildings`), as a normal PDF on your disk. Ordnung! reads those folders, makes everything searchable and helps you file new post. Switch the app off and your archive is still perfectly readable via Finder, Explorer or SMB – in twenty years too.

## Features

- **One tree for the whole family.** Each person, the household or a house is an *area* (a top folder). Everyone sees all areas they may read in a single merged tree; rights are *read* or *read + write* per area. Areas do not need to belong to anyone – “House Linden Lane” simply has members.
- **Full-text search** over title, folder and the text of every page, scans included (Tesseract OCR, German and English). Partial words and small typos still match. `#tag` filters by tag.
- **Inbox with suggestions.** Scanner folders are watched; new documents wait in the inbox with a suggested folder, title and date. Suggestions come from rules, from the inbox subfolder, or – if you like – from an AI (Claude, Ollama or any OpenAI-compatible server). Nothing is filed without you.
- **Rules for humans.** Ordnung! recognises senders by the web or mail address in the letter and asks after filing: *“Post from Nordlicht Insurance → Insurance › Nordlicht › Buildings from now on?”* – with a traffic light that shows how reliable a rule is on your existing archive.
- **Upload from the phone.** Take photos with the iPhone camera; several pages become one PDF, HEIC is converted automatically. Works as a home-screen web app.
- **PDF editor.** Fill in forms, add text, ticks, the date and your stored signature. The result is saved as a new document next to the original, which stays untouched.
- **Collections.** Gather documents from many folders – *Tax return 2026* – without moving them. Download a collection as ZIP or as one merged PDF for your tax advisor.
- **Tags, trash, drag and drop.** Drag documents onto folders to move them, onto collections to link them. Deleted documents stay in the trash for 30 days (configurable).
- **REST API** for everything the UI does, documented at `/docs`.
- **Moving from Paperless-ngx** is supported with an import planner.

<table>
<tr><td><img src="docs/screenshots/en/04-posteingang.jpg" alt="Inbox with a suggested folder"></td><td><img src="docs/screenshots/en/06-editor.jpg" alt="PDF editor with signature"></td></tr>
<tr><td><img src="docs/screenshots/en/03-mappe.jpg" alt="Collection 'Tax return 2026'"></td><td><img src="docs/screenshots/en/02-suche.jpg" alt="Full-text search"></td></tr>
</table>

## Quick start with Docker

```yaml
services:
  ordnung:
    image: ghcr.io/orohde/ordnung:latest
    container_name: ordnung
    restart: unless-stopped
    ports:
      - "8440:8000"
    volumes:
      - ./archiv:/archiv        # your document folders – Ordnung! files new documents here
      - ./data:/data            # index, settings, accounts
      - ./eingang:/eingang      # optional: scanner / inbox folders
    environment:
      - ORDNUNG_ADMIN_USER=admin
      - ORDNUNG_ADMIN_PASSWORD=change-me
```

```bash
docker compose up -d
```

Open `http://localhost:8440`, sign in, and set up your archive and inbox folders under **Settings → Storage**. The first account comes from the environment once; afterwards accounts are managed in the app.

The image is built for `linux/amd64` and `linux/arm64` (Raspberry Pi, Apple silicon).

On **Unraid**, install it from the *Apps* tab (template repository [orohde/unraid-templates](https://github.com/orohde/unraid-templates)).

### Settings

| Variable | Default | Meaning |
|---|---|---|
| `ORDNUNG_ADMIN_USER` / `ORDNUNG_ADMIN_PASSWORD` | `admin` / – | first administrator (only used while no account exists) |
| `ORDNUNG_API_TOKEN` | – | optional token for scripts: `Authorization: Bearer …` |
| `ORDNUNG_OCR` | `1` | text recognition for scans |
| `ORDNUNG_OCR_LANG` | `deu+eng` | Tesseract languages |
| `ORDNUNG_RESCAN_MINUTES` | `10` | full rescan of the archive folders |
| `ORDNUNG_STARTER` | `1` | ship a household folder template and starter rules on first start |
| `PUID` / `PGID` / `UMASK` | `99` / `100` / `0002` | user, group and umask the app runs as when the container starts as root; fresh empty folders are handed over to that user (ignored with `--user`) |

## Try the demo

`tools/demo/make_demo.py` builds an installation with an invented family, invented companies and letters (the screenshots above come from it):

```bash
python tools/demo/make_demo.py /tmp/ordnung-demo --lang en
ORDNUNG_ARCHIVE=/tmp/ordnung-demo/archiv ORDNUNG_DATA=/tmp/ordnung-demo/data \
ORDNUNG_ADMIN_USER=demo ORDNUNG_ADMIN_PASSWORD=demo1234 python -m ordnung
python tools/demo/make_demo.py /tmp/ordnung-demo --lang en --setup http://localhost:8000
```

## How it stores things

```
archiv/
  max/Health/Doctors/2026-02-14_Private invoice_8f2c1a.pdf
  familie/Banking/Sample Savings Bank/Statements/2026-03-31_Account statement March 2026_3ebe93.pdf
  haus/Insurance/Nordlicht/Buildings/2026-01-12_Buildings insurance policy_a41b07.pdf
```

File names follow `date_title_id`; the id is the start of the file's SHA-256, so duplicates are recognised. SQLite is only an index and can be rebuilt from the folders at any time. Tags, collections, rules and accounts live as small JSON files in the data folder.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e '.[dev]'
.venv/bin/python -m pytest -q
ORDNUNG_ARCHIVE=./archiv ORDNUNG_DATA=./data ORDNUNG_ADMIN_PASSWORD=test1234 .venv/bin/python -m ordnung
```

Python · FastAPI · SQLite FTS5 · pypdfium2 · Tesseract · PDF.js · pdf-lib · SAP Fundamental Styles. No build step for the web UI.

## License

[GNU Affero General Public License v3.0](LICENSE). Free software, no paid edition. More at [worldgate.de](https://worldgate.de).
