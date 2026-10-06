# Extension system, schema version 1

An extension adds searchable copy snippets, HTTPS bookmarks and aliases to
already registered local actions. It cannot access arbitrary files, import
Python, load JavaScript or execute code during search. Install/remove through
Settings. Inspect the manifest before confirming installation.

```json
{
  "schema_version": 1,
  "id": "writing-tools",
  "name": "Writing tools",
  "entries": [
    {
      "id": "greeting",
      "title": "Friendly greeting",
      "keyword": "greet",
      "kind": "copy",
      "value": "Hello! Thanks for getting in touch."
    },
    {
      "id": "python-docs",
      "title": "Python documentation",
      "keyword": "pydocs",
      "kind": "url",
      "value": "https://docs.python.org/3/"
    }
  ]
}
```

## Contract

`id` is 3–41 lowercase identifier characters, beginning with a letter. `name`
is 1–100 characters. At most 30 entries are accepted. Each entry has a unique
1–40-character identifier and nonempty `title`, `keyword`, `kind`, `value`.
Strings are bounded to 2,000 characters. The supported kinds are:

| Kind | Value | Execution |
| --- | --- | --- |
| `copy` | Text | Copies after selecting the result |
| `url` | HTTPS URL without embedded credentials | Opens in the external browser |
| `action` | String containing the numeric ID of an existing action | Requires Run confirmation |

Register the action first, then read its ID from `/api/state` with the app's
session token (or the local SQLite actions table). Example entry:

```json
{"id":"project","title":"Open project","keyword":"project","kind":"action","value":"1"}
```

That example works only if action 1 exists. Removed actions are not silently
recreated by an extension. Reinstalling the same extension ID replaces its
manifest. Extensions appear in general search by title/keyword. Local actions
run with the user's permissions, with an argument array and `shell=False`.
PowerShell policy is respected; executable actions are not sandboxed.

Future executable plugins would need a separate permission, versioning and
process-isolation design. They are intentionally not represented as supported
by this schema.
