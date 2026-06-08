import argparse
import csv as parser
import requests
import sys

from typing import Any, cast


class CLIException(Exception):
    pass


def csv_to_map(csv: str) -> list[dict[str, object]]:
    # Read CSV in.
    with open(csv, "r", encoding="utf-8") as fp:
        reader = parser.reader(fp)
        lines = [r for r in reader]

    if not lines or not lines[0]:
        raise CLIException("CSV does not have a header row!")

    # Determine headers based on top row.
    headers: dict[int, str] = {}
    for off, name in enumerate(lines[0]):
        if name:
            headers[off] = name

    # Associate data with headers.
    data: list[dict[str, object]] = []
    expected: set[str] = set(headers.values())
    lowered: set[str] = {h.lower() for h in expected}

    for lnum, row in enumerate(lines[1:]):
        entry: dict[str, object] = {}

        for i, col in enumerate(row):
            if i in headers:
                entry[headers[i]] = col

        if entry.keys() != expected:
            raise CLIException(f"Row {lnum + 2} does not have enough columns!")

        data.append(entry)

    # Determine duplicate entries.
    if "count" not in lowered and "quantity" not in lowered:
        dedup: dict[str, int] = {}

        for entry in data:
            key = str(entry)
            if key not in dedup:
                dedup[key] = 0

            dedup[key] += 1

        deduped: list[dict[str, object]] = []

        for entry in data:
            count = dedup.pop(str(entry), None)

            if count:
                deduped.append({
                    **entry,
                    "count": count,
                })

        data = deduped

    return data


def raise_on_error(resp: requests.Response) -> None:
    if resp.status_code < 200 or resp.status_code >= 300:
        raise Exception(f"Got status code {resp.status_code} from API, returning {resp.text}!")


def json_swap(method: str, loc: str, token: str = "", data: dict[str, Any] = {}) -> dict[str, Any]:
    if token:
        headers = {"Authorization": f"Bearer {token}"}
    else:
        headers = {}

    resp = requests.request(method, loc, headers=headers, json=data)
    raise_on_error(resp)
    if resp.status_code == 204:
        return {}
    return cast(dict[str, Any], resp.json())


def import_csv(location: str, username: str, password: str, csv: str, collection: str, *, empty_first: bool = False) -> None:
    # First get the data, including any counts.
    csv_rows = csv_to_map(csv)

    # Now, get an API token.
    while location[-1] == "/":
        location = location[:-1]

    resp = json_swap("POST", f"{location}/api/authentication_token", data={"username": username, "password": password})
    token = resp.get('token')
    if not token:
        raise CLIException("Couldn't get a token from the API!")

    # Find the collection we're adding to.
    resp = json_swap("GET", f"{location}/api/collections", token=token)
    collection_id: str = ""

    for entry in resp['member']:
        if entry['title'] == collection:
            collection_id = entry['id']
            break

    if not collection_id:
        raise CLIException(f"Couldn't find collection named {collection} to import to!")

    if empty_first:
        print("Emptying out existing collection...")

        keep_going = True
        while keep_going:
            resp = json_swap("GET", f"{location}/api/collections/{collection_id}/items", token=token)
            keep_going = False
            for entry in resp['member']:
                resp = json_swap("DELETE", f"{location}{entry['@id']}", token=token)
                keep_going = True

    # Find any tags, so we can tag things with any data we find.
    tags: dict[str, str] = {}
    resp = json_swap("GET", f"{location}/api/tags", token=token)
    for entry in resp['member']:
        tags[entry['label']] = entry['@id']

    print("Importing CSV into collection...")

    # Now, go about creating some entries based on our CSV.
    for row in csv_rows:
        lowered: dict[str, str] = {k.lower(): k for k in row.keys()}

        name = row.get(lowered.get('name', ''))
        count = row.get(lowered.get('count', '')) or row.get(lowered.get('quantity', ''))
        if not count:
            count = 1
        elif isinstance(count, str):
            count = int(count)
        if not name:
            raise CLIException("Couldn't determine name for an entry in the CSV! Make sure you have a 'name' column!")

        # Try to auto-deduce tags and field values.
        actual_tags: list[str] = []
        actual_fields: dict[str, str] = {}
        for key, val in row.items():
            if key.lower() in {"name", "count", "quantity"}:
                continue

            if val not in tags:
                continue

            actual_tags.append(tags[val])
            actual_fields[key] = val

        data = {
            "name": name,
            "quantity": count,
            "collection": f"/api/collections/{collection_id}",
            "tags": actual_tags,
            "visibility": "public"
        }
        resp = json_swap("POST", f"{location}/api/items", token=token, data=data)

        for field, value in actual_fields.items():
            data = {
                "item": resp['@id'],
                "type": "text",
                "label": field,
                "value": value,
                "visibility": "public"
            }
            json_swap("POST", f"{location}/api/data", token=token, data=data)

    print("Done!")


def main() -> int:
    parser = argparse.ArgumentParser(description="CSV Importer for Koillection")
    parser.add_argument("-l", "--location", metavar="URL", type=str, help="Location of Koillection instance to import into.")
    parser.add_argument("-u", "--username", metavar="USERNAME", type=str, help="Username of user to use when importing.")
    parser.add_argument("-p", "--password", metavar="PASSWORD", type=str, help="Password of user to use when importing.")
    parser.add_argument("-f", "--file", metavar="CSV", type=str, help="CSV file that should be imported.")
    parser.add_argument("-c", "--collection", metavar="NAME", type=str, help="Name of the collection you are importing to.")
    parser.add_argument("-e", "--empty-first", action="store_true", help="Empty the collection out before importing.")
    args = parser.parse_args()

    try:
        import_csv(args.location, args.username, args.password, args.file, args.collection, empty_first=args.empty_first)
    except CLIException as e:
        print(str(e), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
