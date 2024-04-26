import re
import csv
import string
import argparse
import itertools
import requests
from collections import defaultdict
from thefuzz import fuzz


def read_csv_names(file_path):
    names = []
    with open(file_path, 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            names.append(row[0])
    return names


def catch_requests_exceptions(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.RequestException:
            return None
    return wrapper


def normalize_text(text):
    text = re.sub('-', ' ', text)
    return ''.join(ch for ch in re.sub(r'[^\w\s-]', '', text.lower()) if ch not in set(string.punctuation))


def generate_substring_permutations(org_name, limit=6):
    org_name_substrings = org_name.split(' ')
    if len(org_name_substrings) <= limit:
        return [' '.join(permutation) for permutation in itertools.permutations(org_name_substrings)]
    else:
        return [org_name]


@catch_requests_exceptions
def search_openalex(org_name):
    normalized_name = normalize_text(org_name)
    base_url = 'https://api.openalex.org/works'
    params = {
        'filter': 'raw_affiliation_strings.search:"{}"'.format(normalized_name),
        'per-page': '100',
        'cursor': '*'
    }
    match_list = []
    seen_pairs = set()
    substring_permutations = generate_substring_permutations(org_name)
    while True:
        r = requests.get(base_url, params=params)
        api_response = r.json()
        results = api_response.get('results')
        if not results:
            break
        for work in results:
            authorships = work.get('authorships', [])
            for author in authorships:
                raw_affiliations = author.get('raw_affiliation_strings')
                if not raw_affiliations:
                    continue
                for raw_affiliation in raw_affiliations:
                    normalized_affiliation = normalize_text(raw_affiliation)
                    partial_ratio = fuzz.partial_ratio(
                        normalized_name, normalized_affiliation)
                    token_set_ratio = fuzz.token_set_ratio(
                        normalized_name, normalized_affiliation)
                    max_ratio = max(partial_ratio, token_set_ratio)
                    for substring in substring_permutations:
                        if substring in normalized_affiliation:
                            doi = work.get("doi") or work.get('id')
                            pair = (doi, raw_affiliation)
                            if pair not in seen_pairs:
                                seen_pairs.add(pair)
                                match_list.append(pair)
                            break
                    if fuzz.ratio(normalized_name, normalized_affiliation) >= 90:
                        doi = work.get("doi") or work.get('id')
                        pair = (doi, raw_affiliation)
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            match_list.append(pair)
                    elif max_ratio >= 90:
                        doi = work.get("doi") or work.get('id')
                        pair = (doi, raw_affiliation)
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            match_list.append(pair)
        next_cursor = api_response['meta'].get('next_cursor')
        if not next_cursor:
            break
        params['cursor'] = next_cursor
    return match_list if match_list else None


def process_search_results(results, search_string):
    processed_results = []
    for doi, raw_affiliation in results:
        normalized_affiliation = normalize_text(raw_affiliation)
        normalized_search_string = normalize_text(search_string)
        string_in_affiliation = 'TRUE' if normalized_search_string in normalized_affiliation else 'FALSE'
        processed_results.append({
            'doi': doi,
            'raw_affiliation': raw_affiliation,
            'string_in_affiliation': string_in_affiliation
        })
    return processed_results


def write_results_to_csv(results, output_file):
    fieldnames = ['doi', 'raw_affiliation', 'string_in_affiliation']
    with open(output_file, 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Search for names using the OpenAlex API')
    parser.add_argument('-i', '--input_file',
                        help='Path to the CSV file containing the unit names')
    parser.add_argument('-s', '--search_string',
                        help='String to search for in affiliations')
    parser.add_argument('-o', '--output_file', default='string_in_affiliations.csv',
                        help='Path to the CSV file containing the unit names')
    return parser.parse_args()


def main():
    args = parse_arguments()
    names = read_csv_names(args.input_file)
    all_results = []
    for name in names:
        search_results = search_openalex(name)
        if search_results:
            processed_results = process_search_results(
                search_results, args.search_string)
            all_results.extend(processed_results)
    write_results_to_csv(all_results, args.output_file)


if __name__ == '__main__':
    main()
