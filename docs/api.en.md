# REST API

[Deutsch](api.md)

Everything the interface does is also available through the REST API under `/api/`. The interface itself uses nothing else. Requests and responses are JSON.

**Full reference:** Ordnung! serves an interactive overview of every endpoint with parameters and responses at **`/api/docs`**, machine-readable at `/api/openapi.json`. When you are signed in in the browser, you can send requests right there. The page is also linked under *Settings → Connections*.

## Signing in with an API key

Under **Settings → Connections** (administrators only) you create named keys – best one per program – and copy it. Programs send it with every request as a bearer token:

```bash
curl -H "Authorization: Bearer YOUR_KEY" https://ordnung.example.org/api/documents?q=insurance
```

- Every key has a **right**: *Read and write* acts **like an administrator**, *Read only* sees every area but changes nothing (anything but GET is refused with 403, admin areas such as the inbox or users stay shut).
- Only a hash is stored; the key is shown exactly once. **Renew** disables the old secret at once, **Delete** locks the program out. The list shows when a key was last used.
- Without a key the API can only be used with a browser sign-in (session cookie).
- The single key of earlier versions becomes the named key "API" with the write right on update and keeps working unchanged. `ORDNUNG_API_TOKEN`, too, is taken over like this once on first start; after that the variable can go from the compose file.

## For AI assistants (MCP)

MCP access is off in a fresh installation; an administrator switches it on under *Settings → Connections*. The endpoint `/api/mcp` speaks the Model Context Protocol (streamable HTTP) and takes the same key as `Authorization: Bearer <key>`.

Tools: list areas, folders, tags, Mappen and the trash, search (by area, folder, tags, date range), read a document with its recognised text, set or change tags, change title and date, move, create a Mappe, put into the trash and restore. With an administrator key also: view the inbox, file or set aside items, list senders. A read-only key is offered no writing tool. Nothing is deleted for good through MCP, and settings (users, security, storage, rules) are left to the interface.

## Main endpoints

Documents have an `id` (the short ID from the file name). Areas are named like their folders (`oliver`, `gemeinsam` …), folders are paths below them (`Insurance/Car`).

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/version` | Version, no sign-in needed |
| GET | `/api/status` | Number of documents, text recognition progress, last scan |
| GET | `/api/areas` | Areas with display names and rights |
| GET | `/api/tree?areas=oliver,gemeinsam` | Folder tree with counts |
| GET | `/api/documents` | List and search, parameters below |
| GET | `/api/documents/{id}` | One document with title, date, folder, tags |
| GET | `/api/documents/{id}/file` | The file itself (PDF) |
| GET | `/api/documents/{id}/text` | Recognised text |
| PATCH | `/api/documents/{id}` | Change title and date, `{"title": "…", "date": "2026-11-09"}`; renames the file |
| POST | `/api/documents/{id}/move` | Move, `{"folder": "Insurance/Home", "area": "gemeinsam"}` (`area` optional) |
| POST | `/api/documents/{id}/trash` | Into the trash |
| PUT | `/api/documents/{id}/tags` | Set tags, `{"tags": ["Tax 2026"]}` |
| POST | `/api/tags/change` | Tags for many, `{"ids": […], "add": […], "remove": […]}` |
| GET | `/api/tags` | All tags with counts |
| GET | `/api/mappen` | Binders; `/api/mappen/download?name=…&format=pdf` fetches one as PDF or ZIP |
| POST | `/api/altablage` | Into the old files or back, `{"ids": […]}` or `{"folder": "…"}`, `{"restore": true}` |
| GET | `/api/inbox` | Inbox with suggestions |
| POST | `/api/inbox/upload` | Files into the inbox, `{"files": [{"name": "scan.pdf", "data": "<base64>"}], "combine": false}` |
| POST | `/api/inbox/{key}/file` | File it, `{"area": "oliver", "folder": "…", "title": "…", "date": "2026-11-09", "tags": []}` |
| POST | `/api/rescan` | Read the folders again now |

### List and search: `GET /api/documents`

| Parameter | Meaning |
|---|---|
| `q` | Search words, all must occur; `#tag` filters by tag |
| `folder`, `recursive` | Folder and whether subfolders count; a search without `folder` always covers the whole archive |
| `areas` | Areas, comma-separated; without: all allowed ones |
| `tags` | Tags, comma-separated, all must match |
| `date_from`, `date_to` | Date range by document date, both days included; `2026`, `2026-03` or `2026-03-15` |
| `alt` | `true` searches the old files, too |
| `sort`, `desc` | `date` (default), `title`, `area` or `relevance` (best hits first, searches only); `desc=false` reverses |
| `limit`, `offset` | Paging, default 500 |

Response: `{"total": 42, "items": [{"id": "a3f9c1", "title": "…", "date": "2026-10-01", "area": "oliver", "folder": "…", "tags": […], "snippet": "…"}]}`

## Examples

Newest five documents mentioning "insurance":

```bash
curl -s -H "Authorization: Bearer $ORDNUNG_KEY" \
  "https://ordnung.example.org/api/documents?q=insurance&limit=5" | jq '.items[] | {date, title, folder}'
```

Put a PDF into the inbox:

```bash
curl -s -H "Authorization: Bearer $ORDNUNG_KEY" -H "Content-Type: application/json" \
  -d "{\"files\": [{\"name\": \"invoice.pdf\", \"data\": \"$(base64 -i invoice.pdf)\"}]}" \
  https://ordnung.example.org/api/inbox/upload
```

Fetch a document:

```bash
curl -s -H "Authorization: Bearer $ORDNUNG_KEY" -o document.pdf \
  https://ordnung.example.org/api/documents/a3f9c1/file
```

## Errors

Errors come as an HTTP status with `{"detail": "…"}`: `401` not signed in or wrong key, `403` no rights in the area, `404` not found, `409` conflict (e.g. the file already exists at the target), `422` invalid parameters.
