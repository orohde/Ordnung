# REST-API

[English](api.en.md)

Alles, was die Oberfläche kann, geht auch per REST-API unter `/api/`. Die Oberfläche selbst nutzt nichts anderes. Anfragen und Antworten sind JSON.

**Vollständige Beschreibung:** Ordnung! liefert unter **`/api/docs`** eine ausprobierbare Übersicht aller Endpunkte mit Parametern und Antworten, maschinenlesbar unter `/api/openapi.json`. Wer im Browser angemeldet ist, kann dort direkt Anfragen abschicken. Die Seite ist auch unter *Einstellungen → API* verlinkt.

## Anmelden mit API-Schlüssel

Unter **Einstellungen → API** (nur für Administratoren) erzeugst du einen Schlüssel und kopierst ihn. Programme schicken ihn bei jeder Anfrage als Bearer-Token mit:

```bash
curl -H "Authorization: Bearer DEIN_SCHLÜSSEL" https://ordnung.example.org/api/documents?q=versicherung
```

- Der Schlüssel handelt **wie ein Administrator** und sieht alle Bereiche. Er gehört nur in vertrauenswürdige Skripte.
- **Neu erzeugen** macht den alten sofort ungültig, **Löschen** schaltet den Zugang per Schlüssel ab.
- Ohne Schlüssel bleibt die API nur mit einer Anmeldung im Browser (Sitzungs-Cookie) nutzbar.
- Früher kam der Schlüssel aus der Umgebungsvariable `ORDNUNG_API_TOKEN`. Ist sie gesetzt, übernimmt Ordnung! sie beim ersten Start einmal in die Einstellungen. Danach gilt nur noch, was dort steht, und die Variable kann aus der Compose-Datei raus.

## Die wichtigsten Endpunkte

Dokumente haben eine `id` (die Kurz-ID aus dem Dateinamen). Bereiche heißen wie ihre Ordner (`oliver`, `gemeinsam` …), Ordner sind Pfade darunter (`Versicherungen/Cosmos/KFZ`).

| Methode | Pfad | Wofür |
|---|---|---|
| GET | `/api/version` | Version, ohne Anmeldung |
| GET | `/api/status` | Anzahl Dokumente, Stand der Texterkennung, letzter Scan |
| GET | `/api/areas` | Bereiche mit Anzeigenamen und Rechten |
| GET | `/api/tree?areas=oliver,gemeinsam` | Ordnerbaum mit Anzahl |
| GET | `/api/documents` | Liste und Suche, Parameter siehe unten |
| GET | `/api/documents/{id}` | Ein Dokument mit Titel, Datum, Ordner, Tags |
| GET | `/api/documents/{id}/file` | Die Datei selbst (PDF) |
| GET | `/api/documents/{id}/text` | Erkannter Text |
| PATCH | `/api/documents/{id}` | Titel und Datum ändern, `{"title": "…", "date": "2026-11-09"}`; benennt die Datei um |
| POST | `/api/documents/{id}/move` | Verschieben, `{"folder": "Versicherungen/HUK", "area": "gemeinsam"}` (`area` freiwillig) |
| POST | `/api/documents/{id}/trash` | In den Papierkorb |
| PUT | `/api/documents/{id}/tags` | Tags setzen, `{"tags": ["Steuer 2026"]}` |
| POST | `/api/tags/change` | Tags für viele, `{"ids": […], "add": […], "remove": […]}` |
| GET | `/api/tags` | Alle Tags mit Anzahl |
| GET | `/api/mappen` | Mappen; `/api/mappen/download?name=…&format=pdf` holt eine als PDF oder ZIP |
| POST | `/api/altablage` | In die Altablage oder zurück, `{"ids": […]}` bzw. `{"folder": "…"}`, `{"restore": true}` |
| GET | `/api/inbox` | Posteingang mit Vorschlägen |
| POST | `/api/inbox/upload` | Dateien in den Posteingang, `{"files": [{"name": "scan.pdf", "data": "<base64>"}], "combine": false}` |
| POST | `/api/inbox/{key}/file` | Ablegen, `{"area": "oliver", "folder": "…", "title": "…", "date": "2026-11-09", "tags": []}` |
| POST | `/api/rescan` | Ordner jetzt neu einlesen |

### Liste und Suche: `GET /api/documents`

| Parameter | Bedeutung |
|---|---|
| `q` | Suchbegriffe, alle müssen vorkommen; `#tag` filtert nach Tag |
| `folder`, `recursive` | Ordner und ob Unterordner dazugehören; eine Suche ohne `folder` geht immer über das ganze Archiv |
| `areas` | Bereiche, mit Komma getrennt; ohne: alle erlaubten |
| `tags` | Tags, mit Komma getrennt, alle müssen passen |
| `alt` | `true` sucht auch in der Altablage |
| `sort`, `desc` | `date` (Standard), `title`, `area` oder `relevance` (beste Treffer zuerst, nur bei einer Suche); `desc=false` dreht die Richtung |
| `limit`, `offset` | Seitenweise holen, Standard 500 |

Antwort: `{"total": 42, "items": [{"id": "a3f9c1", "title": "…", "date": "2026-10-01", "area": "oliver", "folder": "…", "tags": […], "snippet": "…"}]}`

## Beispiele

Neueste fünf Dokumente mit „Versicherung“:

```bash
curl -s -H "Authorization: Bearer $ORDNUNG_KEY" \
  "https://ordnung.example.org/api/documents?q=versicherung&limit=5" | jq '.items[] | {date, title, folder}'
```

PDF in den Posteingang legen:

```bash
curl -s -H "Authorization: Bearer $ORDNUNG_KEY" -H "Content-Type: application/json" \
  -d "{\"files\": [{\"name\": \"rechnung.pdf\", \"data\": \"$(base64 -i rechnung.pdf)\"}]}" \
  https://ordnung.example.org/api/inbox/upload
```

Dokument holen:

```bash
curl -s -H "Authorization: Bearer $ORDNUNG_KEY" -o dokument.pdf \
  https://ordnung.example.org/api/documents/a3f9c1/file
```

## Fehler

Fehler kommen als HTTP-Status mit `{"detail": "…"}`: `401` nicht angemeldet oder falscher Schlüssel, `403` keine Rechte im Bereich, `404` nicht gefunden, `409` Konflikt (z. B. Datei gibt es am Ziel schon), `422` ungültige Parameter.
