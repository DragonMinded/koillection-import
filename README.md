Simple script that allows you to take a CSV and upload it to a collection you
have on a Koillection instance that you host.

Uses the `just` command runner to make things easier. If you're on a debian-based
operating system, run the following to get started:

```
# Install dependencies.
sudo apt install just python3

# Clone this repo.
git clone https://github.com/DragonMinded/koillection-import.git
cd koillection-import

# Set up the repo to run.
just setup

# Run with help.
just run --help
```

You'll need a CSV file where the first row is headers for the data you'll want
to import. Automatically finds a "name" column and uses that for item names.
Automatically finds a "count" or "quantity" column and uses that for item counts.
If there isn't a column for item count, determines that automatically by finding
duplicate rows and combining them to one item with the right count. Takes any other
columns and adds them as fields on the imported items. So, be sure to spell the
headers correctly and capitalize them as you want. Any column with an empty header
will be skipped and not imported. Additionally, if any cell matches a tag that
you have created in your Koillection instance, tags the item with that tag.

You'll need to specify the base URL to your Koillection instance, your username,
your password, the CSV file you want to import, and the name of the collection you
want to import into. Optionally you can specify `--empty-first` to delete everything
in the collection before importing.
