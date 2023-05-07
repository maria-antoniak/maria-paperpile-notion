
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
        formatted_tags = [{"name": _tag} for _tag in keywords.split(';')]
        payload["properties"]["Tags"] = {"multi_select": formatted_tags}
    else:
        payload["properties"]["Tags"] = {"multi_select": []}
    
    if link:
        payload["properties"]["Link"] = {"url": link}

    if year:
        payload["properties"]['Year'] = {"rich_text": [{"type": "text",
                                                        "text": {"content": year}}]}

    return payload



def notion_add_entry(title='',
                     authors='',
                     year='0',
                     ref_id='',
                     link='',
                     abstract='',
                     keywords=''):
    
    url = "https://api.notion.com/v1/pages"
    payload = get_payload(title, authors, year, ref_id, link, abstract, keywords)
    # pprint.pprint(payload)

    response = requests.post(url, json=payload, headers=HEADERS)
    # pprint.pprint('inside notion_add_entry')
    # pprint.pprint(json.loads(response.text))


def notion_update_page(page_id,
                       title='',
                       authors='',
                       year='0',
                       ref_id='',
                       link='',
                       abstract='',
                       keywords=''):
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = get_payload(title, authors, year, ref_id, link, abstract, keywords)
    # pprint.pprint(payload)
    response = requests.patch(url, json=payload, headers=HEADERS)
    # pprint.pprint('inside notion_update_page')
    # pprint.pprint(json.loads(response.text))


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


def main():

    # Instantiate the parser
    parser = bibtexparser.bparser.BibTexParser()
    parser.ignore_nonstandard_types = True
    parser.homogenize_fields = False
    parser.interpolate_strings = False

    with open(BIB_PATH) as bib_file:
        bibliography = bibtexparser.load(bib_file, parser=parser)

    if os.path.exists(ARCHIVE_PATH):
        with open(ARCHIVE_PATH, 'rb') as archive_file:
            archive = json.load(archive_file)
    else:
        archive = []
    archive_ids = [e['ID'] for e in archive]

    # Add each entry to notion database
    update_archive = False
    entries_to_archive = []
    for entry in reversed(bibliography.entries):

        title = entry.get('title', '')
        title = clean_str(title)
        title = title

        authors = entry.get('author', '')
        authors = authors.replace(' and ', '; ')
        authors = authors.replace(' And ', '; ')
        authors = clean_str(authors)
        authors = format_authors(authors)

        year = entry.get('year', '')
        link = entry.get('url', '')
        ref_id = entry.get('ID')
        
        abstract = entry.get('abstract', '')
        
        keywords = entry.get('keywords', '')

        entries_to_archive.append({'title': title,
                                   'authors': authors,
                                   'year': year,
                                   'ref_id': ref_id',
                                   'link': link,
                                   'abstract': abstract,
                                   'keywords': keywords})

        # Create new page
        if ref_id not in archive_ids:
#             pprint.pprint('ref_id not in archive_ids')
#             pprint.pprint(ref_id)
#             pprint.pprint(archive_ids)
            notion_add_entry(title=title,
                             authors=authors,
                             year=year,
                             ref_id=ref_id,
                             link=link,
                             abstract=abstract,
                             keywords=keywords)
            update_archive = True

         # Update existing page
        elif entry not in archive:
            # pprint.pprint('entry not in archive')
            page_id = notion_fetch_page(ref_id)
            if page_id != -1:
                # pprint.pprint('page_id != -1')
                notion_update_page(page_id=page_id,
                                   title=title,
                                   authors=authors,
                                   year=year,
                                   ref_id=ref_id,
                                   link=link,
                                   abstract=abstract,
                                   keywords=keywords)
                update_archive = True

    # Only update the archive if necessary
    if update_archive and entries_to_archive:
        pprint.pprint('Updating archive with ' + str(len(entries_to_archive)) + ' bibliography entries')
        with open(ARCHIVE_PATH, 'w') as archive_file:
            archive = json.dump(entries_to_archive)


if __name__ == "__main__":
    main()
