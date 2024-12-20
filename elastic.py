import json
import os
import time

from elasticsearch import Elasticsearch
from bs4 import BeautifulSoup


class Elastic:
    def __init__(self, host, port, api_key, index_name='index'):
        self.client = Elasticsearch([{'scheme': 'http', 'host': host, 'port': port}], api_key=api_key)
        self.index_name = index_name
        if self.create_index():
            self.indexing()

    def _get_index_settings(self):
        return {
            "settings": {
                "index.requests.cache.enable": True,
            },
            "mappings": {
                "properties": {
                    "url": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "title": {
                        "type": "text",
                        "analyzer": "standard"
                    },
                    "headers": {
                        "type": "text",
                        "analyzer": "standard"

                    }
                    ,
                    "body": {
                        "type": "text",
                        "analyzer": "standard"
                    }
                }
            }
        }

    def search(self, query: str, offset=0, limit=20):
        query = query.strip()
        self.client.indices.refresh(index=self.index_name)
        words = query.split()  # جدا کردن کلمات
        query_body = {
            "_source": ["title", "headers", "url"],
            "from": offset,
            "size": limit,
            "query": {
                "bool": {
                    "should": []  # استفاده از should برای اعمال وزن‌دهی
                }
            },
            "suggest": {
                "text": query,
                "subjectSuggester": {
                    "term": {
                        "field": "title",
                        "min_word_length": 2,
                        "string_distance": "ngram"
                    }
                }
            }
        }
        for word in words:
            if '*' in word or '?' in word:
                query_body["query"]["bool"]["should"].append({
                    "wildcard": {
                        "title": {
                            "value": word,
                            "case_insensitive": True,
                            "boost": 3.0  # وزن بیشتر برای title
                        }
                    }
                })
                query_body["query"]["bool"]["should"].append({
                    "wildcard": {
                        "headers": {
                            "value": word,
                            "case_insensitive": True,
                            "boost": 2.0  # وزن متوسط برای headers
                        }
                    }
                })
                query_body["query"]["bool"]["should"].append({
                    "wildcard": {
                        "body": {
                            "value": word,
                            "case_insensitive": True,
                            "boost": 1.0  # وزن کمتر برای body
                        }
                    }
                })
            else:
                query_body["query"]["bool"]["should"].append({
                    "multi_match": {
                        "query": query,
                        "fields": ["title^3", "headers^2", "body^1"],
                        "type": "phrase_prefix"
                    }
                })
                # query_body["query"]["bool"]["should"].append({
                #     "multi_match": {
                #         "query": query,
                #         "fields": ["title^3", "headers^2", "body^1"],
                #         "type": "phrase_prefix"
                #     }
                # })
                # query_body["query"]["bool"]["should"].append({
                #     "match_phrase": {
                #         "body": {
                #             "query": word,
                #             "boost": 1.0  # وزن کمتر برای body
                #         }
                #     }
                # })

        # query_body["query"]["bool"]["minimum_should_match"] = 1  # حداقل یکی از شرایط باید برقرار باشد

        response = self.client.search(index=self.index_name, body=query_body)
        print(response)
        hits = response["hits"]["hits"]
        result = []
        for hit in hits:
            hit["_source"]['summary'] = hit["_source"].pop("headers")
            result.append(hit["_source"])
        suggest_str = ''
        flag = False
        for suggest in response['suggest']['subjectSuggester']:
            if not suggest.get('options', []):
                suggest_str += suggest['text']
            else:
                suggest_str += suggest['options'][0]['text']
                flag = True
            suggest_str += ' '
        if not flag:
            suggest_str = ''

        return response['took'], response['hits']['total']['value'], [hit["_source"] for hit in
                                                                      hits], suggest_str.strip()

    def suggest(self, query: str, limit=10):
        tokens = query.split(" ")
        clauses = [

            {
                "span_multi": {
                    "match": {
                        "fuzzy":
                            {
                                "title":
                                    {
                                        "value": token,
                                        "fuzziness": "AUTO",
                                    },
                            }
                    }
                }
            }

            for token in tokens
        ]

        # Build the final payload
        payload = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "span_near": {
                                "clauses": clauses,
                                "slop": 0,
                            }
                        }
                    ]
                }
            },
            "size":1000
        }

        # Execute the search query
        response = self.client.search(index=self.index_name, body=payload)
        # print(response)
        hits = response.get("hits", {}).get("hits", [])
        results = []
        query_words = query.split()  # Split the query into words

        for hit in hits:
            title = hit["_source"]['title'].strip()

            # Split the title into sections based on "-"
            parts = title.split("-")

            for part in parts:
                words = part.split()  # Split each part into words
                # Find positions of query words in the part
                positions = [i for i, word in enumerate(words) if any(q in word for q in query_words)]
                if positions:  # If at least one query word exists in the part
                    # Determine the range of words to include
                    start_index = max(0, min(positions) - 3)  # Add context of 3 words before
                    end_index = min(len(words), max(positions) + 4)  # Add context of 3 words after

                    # Extract the snippet
                    snippet = " ".join(words[start_index:end_index])
                    if snippet not in results:
                        results.append(snippet)

        return response['took'], results[:limit]

    def create_index(self):
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name, body=self._get_index_settings())
            return True
        return False

    def reindex(self):
        if self.client.indices.exists(index=self.index_name):
            self.client.indices.delete(index=self.index_name)

        self.client.indices.create(index=self.index_name, body=self._get_index_settings())

    def indexing(self):
        documents = []
        with open('documents.json') as f:
            informations = json.load(f)
        start = time.time()
        for information in informations:
            # # documents.append({"index": {"_index": self.index_name}})
            # url = information.get('url', '')
            # doc = self._parse_html(os.path.join(self.repository_path, information['path']))
            # doc['url'] = url
            # documents.append(doc)
            self.client.index(index=self.index_name, document=information)
        end = time.time()
        print(end - start)

    # def _parse_html(self, file_path):
    #     with open(file_path, 'r', encoding='utf-8') as f:
    #         soup = BeautifulSoup(f, 'lxml')
    #     title = soup.title.string if soup.title else ''
    #     headers = ' '.join([h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])])
    #     body = soup.body.get_text() if soup.body else ''
    #     return {'title': title, 'headers': headers, 'body': body}

# e = Elastic('localhost', 9200, 'MnphNDBKTUJxUkwtcFp2dW4wQ3I6R3BxcjJhNHRSRG1QSXoyYzZGYmw5dw==', '/home/sina/uni/WebSearch/project1/','soft98')
# # e.reindex()
# # e.indexing()
# print(e.search('soft98'))
