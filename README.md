# String in Affiliation for Unit

Searches for a given search string in the raw affiliations of works associated with a list of organization names using the OpenAlex API.

## Installation
   ```
   pip install -r requirements.txt
   ```

## Usage

```
python string_in_affiliation_for_unit.py -i input_file.csv -s "search string" [-o output_file.csv]
```

- `-i`, `--input_file`: Path to the CSV file containing the unit names (required)
- `-s`, `--search_string`: String to search for in affiliations (required)
- `-o`, `--output_file`: Path to the output CSV file (optional, default: `string_in_affiliations.csv`)

## Output

The script saves the search results to the specified CSV file, with each row containing:
- `doi`: The DOI or ID of the work
- `raw_affiliation`: The raw affiliation string
- `string_in_affiliation`: 'TRUE' if the search string is found in the normalized affiliation, 'FALSE' otherwise