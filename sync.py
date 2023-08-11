
import bibtexparser
import json
import os
import pickle
import pprint
import requests

"""
TODO:
- Default icon for papers.
"""

ARCHIVE_PATH = 'archive.json'
BIB_PATH = 'references.bib'
NOTION_TOKEN = os.environ['NOTION_TOKEN']
DATABASE_IDENTIFIER = os.environ['DATABASE_IDENTIFIER']
HEADERS = {"Accept": "application/json",
           "Notion-Version": "2022-06-28",
           "Content-Type": "application/json",
           "Authorization": f"Bearer {NOTION_TOKEN}"}


def get_payload(title='',
                authors='',
                year='',
                ref_id='',
                link='',
                abstract='',
                keywords=''):    

    payload = {
        "parent": {
            'database_id': DATABASE_IDENTIFIER,
        },
        "properties": {
            'Title': {
                'title': [{
                    'text': {
                        'content': title,
                        }
                    }]
                },
            'Reference ID': {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": ref_id,
                    }
                }],
            }   
        }
    }

    if authors:
        payload["properties"]['Authors'] = {"rich_text": [{"type": "text",
                                                           "text": {"content": authors}}]}

    if abstract:
        payload["properties"]['Abstract'] = {"rich_text": [{"type": "text",
                                                            "text": {"content": abstract}}]}

    if keywords:
        formatted_tags = [{"name": _tag} for _tag in keywords]
        payload["properties"]["Tags"] = {"multi_select": formatted_tags}
    else:
        payload["properties"]["Tags"] = {"multi_select": []}
    
    if link:
        payload["properties"]["Link"] = {"url": link}

    if year:
        payload["properties"]['Year'] = {"rich_text": [{"type": "text",
                                                        "text": {"content": year}}]}

    return payload



def notion_add_entry(formatted_entry):
    url = "https://api.notion.com/v1/pages"
    payload = get_payload(formatted_entry['title'], 
                          formatted_entry['authors'],  
                          formatted_entry['year'], 
                          formatted_entry['ref_id'],  
                          formatted_entry['link'],  
                          formatted_entry['abstract'],  
                          formatted_entry['keywords'])
    
    response = requests.post(url, json=payload, headers=HEADERS)
    pprint.pprint(response)
    

def notion_update_page(page_id,
                       formatted_entry):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = get_payload(formatted_entry['title'], 
                          formatted_entry['authors'],  
                          formatted_entry['year'], 
                          formatted_entry['ref_id'],  
                          formatted_entry['link'],  
                          formatted_entry['abstract'],  
                          formatted_entry['keywords'])
    response = requests.patch(url, json=payload, headers=HEADERS)
    pprint.pprint(response)


def delete_page(page_id):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"archived": True}
    response = requests.patch(url, json=payload, headers=HEADERS)
    pprint.pprint(response)


def notion_fetch_page(ref_id):
    url = f"https://api.notion.com/v1/databases/{DATABASE_IDENTIFIER}/query"

    # List database pages
    payload = { "page_size": 1,
                "filter": {'property': 'Reference ID',
                           'rich_text': {"equals": ref_id}}}
    
    response = requests.post(url, json=payload, headers=HEADERS)
    
    response = json.loads(response.text)
    #  pprint.pprint(response)
    try:
        if len(response['results']) > 0:
            return response['results'][0]['id']
    except:
        return -1
    return -1


def get_notion_ref_ids():
    url = f"https://api.notion.com/v1/databases/{DATABASE_IDENTIFIER}/query"

    page_size = 100

    payload = {"page_size": page_size}
    response = requests.post(url, json=payload, headers=HEADERS)

    data = response.json()

    results = data["results"]

    i = 0
    while data["has_more"]:
        pprint.pprint(i)
        i += 1
        payload = {"page_size": page_size, "start_cursor": data["next_cursor"]}
        response = requests.post(url, json=payload, headers=HEADERS)
        data = response.json()
        results.extend(data["results"])

    ref_ids_in_notion = []
    archive = []
    ref_archive_dict = {}
    for _result in results:
        
        ref_id = _result['properties']['Reference ID']['rich_text'][0]['plain_text']
        title = ''
        authors = ''
        year = ''
        link = _result['properties']['Link']['url']
        abstract = ''
        keywords = []

        if _result['properties']['Title']['title']:
            title = _result['properties']['Title']['title'][0]['plain_text']
        if _result['properties']['Authors']['rich_text']:
            authors = _result['properties']['Authors']['rich_text'][0]['plain_text']
        if _result['properties']['Year']['rich_text']:
            year = _result['properties']['Year']['rich_text'][0]['plain_text']
        if _result['properties']['Abstract']['rich_text']:
            abstract = _result['properties']['Abstract']['rich_text'][0]['plain_text']
        if _result['properties']['Tags']['multi_select']:
            for _keyword in _result['properties']['Tags']['multi_select']:
                keywords.append(_keyword['name'].lower().strip())
            keywords = sorted(keywords)

        new_entry = {'title': title,
                     'authors': authors,
                     'year': year,
                     'ref_id': ref_id,
                     'link': link,
                     'abstract': abstract,
                     'keywords': keywords}
                   
        archive.append(new_entry)

        ref_archive_dict[ref_id] = new_entry
               
        ref_ids_in_notion.append(ref_id)
               
    return ref_ids_in_notion, archive, ref_archive_dict


def clean_str(string):
    string = string.strip()
    string = string.replace('\n', ' ')
    string = string.replace(r'\"a', 'ä')
    string = string.replace(r'\"e', 'ë')
    string = string.replace(r'\"i', 'ï')
    string = string.replace(r'\"o', 'ö')
    string = string.replace(r'\"u', 'ü')
    string = string.replace(r'\'a', 'á')
    string = string.replace(r'\'e', 'é')
    string = string.replace(r'\'i', 'í')
    string = string.replace(r'\'o', 'ó')
    string = string.replace(r'\'u', 'ú')
    string = string.replace(r'\^a', 'â')
    string = string.replace(r'\^e', 'ê')
    string = string.replace(r'\^i', 'î')
    string = string.replace(r'\^o', 'ô')
    string = string.replace(r'\^u', 'û')
    string = string.replace(r'\`a', 'à')
    string = string.replace(r'\`e', 'è')
    string = string.replace(r'\`i', 'ì')
    string = string.replace(r'\`o', 'ò')
    string = string.replace(r'\`u', 'ù')
    string = ' '.join([w.title() if w.islower() else w for w in string.split()])
    string = string.replace('{', '')
    string = string.replace('}', '')
    return string


def format_authors(test_string):
    authors = [a.split(',') for a in test_string.split(';')]
    formatted_authors = [] 
    for a in authors:
        if len(a) == 1:
            formatted_authors.append(a[0].strip())
        elif len(a) == 2:
            formatted_authors.append(a[1].strip() + ' ' + a[0].strip())
        else:
            formatted_authors.append(' '.join(a).strip())
    return ', '.join(formatted_authors)


def get_bib_entry(entry):
    ref_id = ''
    title = ''
    authors = ''
    year = ''
    link = None
    abstract = ''
    keywords = []

    if entry.get('title', ''):
               title = entry.get('title', '')
               title = clean_str(title)
               title = title

    if entry.get('author', ''):
        authors = entry.get('author', '')
        authors = authors.replace(' and ', '; ')
        authors = authors.replace(' And ', '; ')
        authors = clean_str(authors)
        authors = format_authors(authors)

    if entry.get('year', ''):
        year = entry.get('year', '')

    if entry.get('url', ''):
        link = entry.get('url', '')

    if entry.get('ID'):
        ref_id = entry.get('ID')

    if entry.get('abstract', ''):
        abstract = entry.get('abstract', '')

    if entry.get('keywords', ''):
        keywords = sorted(list(set([k.strip() for k in entry.get('keywords', '').lower().split(';')])))

    formatted_entry = {'title': title,
                       'authors': authors,
                       'year': year,
                       'ref_id': ref_id,
                       'link': link,
                       'abstract': abstract,
                       'keywords': keywords}
           
    return ref_id, formatted_entry


def main():

    # Instantiate the parser
    # parser = bibtexparser.bparser.BibTexParser()
    # parser = bibtexparser.BibTexParser()
    # parser.ignore_nonstandard_types = True
    # parser.homogenize_fields = False
    # parser.interpolate_strings = False

    # Load the bib file from Paperpile
    # with open(BIB_PATH) as bib_file:
        # bibliography = bibtexparser.load(bib_file, parser=parser)
    bibliography = bibtexparser.parse_file(BIB_PATH)

    ref_ids_in_bib = []
    for entry in reversed(bibliography.entries):
        pprint.pprint(entry)
        pprint.pprint(dir(entry))
        pprint.pprint(entry.fields)
        pprint.pprint(entry.fields_dict)
        ref_ids_in_bib.append(entry.key)
    pprint.pprint(len(ref_ids_in_bib))
           
    ref_ids_in_notion, notion_entries, ref_id_notion_entry_dict = get_notion_ref_ids()
    pprint.pprint(len(ref_ids_in_notion))

    ref_ids_to_add = [ref_id for ref_id in ref_ids_in_bib if ref_id not in ref_ids_in_notion]
    ref_ids_to_delete = [ref_id for ref_id in ref_ids_in_notion if ref_id not in ref_ids_in_bib]

    if len(ref_ids_to_add) > 0:
        pprint.pprint('NUMBER OF PAPERS TO ADD: ' + str(len(ref_ids_to_add)))
        pprint.pprint(ref_ids_to_add)
    if len(ref_ids_to_delete) > 0:
        pprint.pprint('NUMBER OF PAPERS TO DELETE: ' + str(len(ref_ids_to_delete)))
        pprint.pprint(ref_ids_to_delete)

    pprint.pprint('==================================================')
    pprint.pprint('ALL REF IDS')
    pprint.pprint(ref_ids_in_bib)

    # # Iterate over the bib entries and either add a new database row or update the row in Notion
    # for entry in reversed(bibliography.entries):

    #     ref_id, formatted_entry = get_bib_entry(entry)

    #     # Create new page if it doesn't already exist in Notion
    #     if ref_id not in ref_ids_in_notion:
    #         pprint.pprint('==================================================')
    #         pprint.pprint('Adding entry: ' + ref_id)
    #         pprint.pprint('==================================================')
    #         pprint.pprint(formatted_entry)
    #         notion_add_entry(formatted_entry)

    #     # Update existing page
    #     elif formatted_entry not in notion_entries:
    #         pprint.pprint('==================================================')
    #         pprint.pprint('Updating entry: ' + ref_id)
    #         pprint.pprint('==================================================')
    #         pprint.pprint('FORMATTED ENTRY FROM BIB')
    #         pprint.pprint(formatted_entry)
    #         pprint.pprint('CLOSEST ENTRY IN NOTION')
    #         if ref_id in ref_id_notion_entry_dict:
    #             pprint.pprint(ref_id_notion_entry_dict[ref_id])
    #         else:
    #             pprint.pprint('ref_ID not found in Notion')
    #         page_id = notion_fetch_page(ref_id)
    #         if page_id != -1:
    #             notion_update_page(page_id,
    #                                formatted_entry)
    #         else:
    #             pprint.pprint('--> Error: page_id == -1; Trying to add entry: ' + ref_id)
    #             notion_add_entry(formatted_entry)

    # Look for papers in Notion that no longer exist in the bib file and delete them
    # for ref_id in ref_ids_in_notion:
    #     if ref_id not in ref_ids_in_bib:
    #         pprint.pprint(ref_ids_in_bib)
    #         pprint.pprint('==================================================')
    #         pprint.pprint('Deleting entry: ' + ref_id)
    #         pprint.pprint('==================================================')
    #         page_id = notion_fetch_page(ref_id)
    #         delete_page(page_id)


if __name__ == "__main__":
    main()
