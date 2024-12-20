import json
import os

from bs4 import BeautifulSoup


def indexing():
    documents = []
    with open(os.path.join('/home/sina/uni/WebSearch/project1/data4/information.json')) as f:
        informations = json.load(f)
    for information in informations:
        # documents.append({"index": {"_index": self.index_name}})
        url = information.get('url', '')
        doc = _parse_html(os.path.join('/home/sina/uni/WebSearch/project1/',information['path']))
        doc['url'] = url
        documents.append(doc)
    with open('documents.json', 'w+') as f:
        json.dump(documents, f)


def _parse_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')
    title = soup.title.string if soup.title else ''
    headers = ' '.join([h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])])
    body = soup.body.get_text() if soup.body else ''
    return {'title': title, 'headers': headers, 'body': body}


indexing()