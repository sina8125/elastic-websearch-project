from elasticsearch import Elasticsearch

api_key = "MnphNDBKTUJxUkwtcFp2dW4wQ3I6R3BxcjJhNHRSRG1QSXoyYzZGYmw5dw=="
client = Elasticsearch("http://localhost:9200", api_key=api_key)
index_name = "html_pages"

index_settings = {
    "settings": {
        "analysis": {
            "analyzer": {
                "standard_analyzer": {  # تحلیل‌گر استاندارد
                    "type": "standard"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text",  # فیلد body به صورت متنی
                "analyzer": "standard_analyzer"
            }
        }
    }
}
# ایجاد ایندکس
if client.indices.exists(index=index_name):
    print(f"Index '{index_name}' already exists. Deleting it...")
    client.indices.delete(index=index_name)

client.indices.create(index=index_name)

# داده‌ها
documents = [
    {"index": {"_index": index_name}},
    {
        "title": "sample Title Sample",
        "headers": "Header1 Header2",
        "body": "This is the main content of the HTML."
    },
    {"index": {"_index": index_name}},
    {
        "title": "Sample Title",
        "headers": "Header1 Header2",
        "body": "This is the main content of the HTML."
    },
]

# ایندکس کردن داده‌ها
print(client.bulk(body=documents))
print("Data indexed successfully.")

client.indices.refresh(index=index_name)


def autocomplete_query(prefix):
    body = {
        "query": {
            "multi_match": {
                "query": prefix,
                "fields": ["title", "headers", "body"],  # جستجو در فیلدهای موردنظر
                "type": "phrase_prefix"  # تطبیق بر اساس prefix
            }
        }
    }
    response = client.search(index=index_name, body=body)
    hits = response["hits"]["hits"]
    return [hit["_source"] for hit in hits]


# user_input = "co"
# results = autocomplete_query(user_input)
# print(f"Results for '{user_input}':")
# for result in results:
#     print(result)

resp = client.search(
    index=index_name,
    body={
        "suggest": {
            "text": "samp",  # کوئری جستجو که وارد می‌شود
            "sample-suggestion": {
                "term": {
                    "field": "title",  # فیلدی که پیشنهاد از آن گرفته می‌شود
                    "suggest_mode": "missing",  # پیشنهادها حتی در صورت نبود کلمه
                    "max_edits": 2,  # حداکثر تغییرات برای پیشنهاد
                    "prefix_length": 1,  # طول پیشوند ثابت
                    "min_word_length": 2,  # حداقل طول کلمات برای پیشنهاد
                    "size": 5  # تعداد پیشنهادات
                }
            }
        }
    }
)
print(resp)
exit()

print(client.search(
    index=index_name,
    body={
        "query": {
            "bool": {
                "should": [{
                    "match_phrase_prefix": {
                        "title": {
                            "query": "sample",  # کلمه جستجو
                            "boost": 3
                        }
                    }
                },
                    {
                        "match_phrase_prefix": {
                            "body": {
                                "query": "sample",  # کلمه جستجو
                                "boost": 1
                            }
                        }
                    }

                ]
            },
        },
        "highlight": {
            "fields": {
                "title": {},  # فعال کردن highlight برای هر فیلد
                "headers": {},
                "body": {}
            }
        }
    }
)
)

resp = client.search(
    index=index_name,
    suggest={
        "my-suggest-1": {
            "text": "Thiss is th mai",  # متن ورودی
            "term": {
                "field": "title",  # فیلدی که پیشنهاد از آن گرفته می‌شود
                "suggest_mode": "missing",  # پیشنهادها حتی در صورت نبود کلمه
                "max_edits": 2,  # حداکثر تغییرات برای پیشنهاد
                "prefix_length": 1,  # طول پیشوند ثابت
                "min_word_length": 2  # حداقل طول کلمات برای پیشنهاد
            }
        }, "my-suggest-2": {
            "text": "Thiss is th mai",  # متن ورودی
            "term": {
                "field": "headers",  # فیلدی که پیشنهاد از آن گرفته می‌شود
                "suggest_mode": "missing",  # پیشنهادها حتی در صورت نبود کلمه
                "max_edits": 2,  # حداکثر تغییرات برای پیشنهاد
                "prefix_length": 1,  # طول پیشوند ثابت
                "min_word_length": 2  # حداقل طول کلمات برای پیشنهاد
            }
        },

    },
)
print(resp)
# چاپ نتایج
for suggest in resp["suggest"].values():
    for option in suggest:
        if option.get("options"):
            print(f"Suggested: {option['options'][0]['text']}")

resp = client.search(
    index=index_name,
    suggest={
        "multi-field-suggest": {
            "text": "This is the mai",
            "phrase": {  # استفاده از phrase suggestion
                "field": "title",  # جستجو در چندین فیلد
                "max_errors": 2,  # حداکثر تغییرات مجاز
                "size": 5  # تعداد پیشنهادها
            }
        }
    }
)

print(resp)

# چاپ نتایج
for suggestion in resp["suggest"]["multi-field-suggest"]:
    for option in suggestion["options"]:
        print(f"Suggested: {option['text']}")

#
# suggest_query = {
#     "query": {
#         "more_like_this": {
#             "fields": ["title", "headers", "body"],  # فیلدهایی که می‌خواهید مشابهت در آن‌ها بررسی شود
#             "like": "Hea",  # کلمه یا عبارت برای جستجوی مشابه
#             "min_term_freq": 1,
#             "max_query_terms": 12
#         }
#     }
# }
#
# response = client.search(index=index_name, body=suggest_query)
#
# # نمایش نتایج جستجو
# print([hit["_source"] for hit in response['hits']['hits']])
#
#
# suggest_query = {
#     "query": {
#         "fuzzy": {
#             "title": {
#                 "value": "Hea",  # عبارت ورودی برای جستجوی مشابه
#                 "fuzziness": "AUTO"  # حالت fuzzy برای تطابق بیشتر
#             }
#         }
#     }
# }
#
# response = client.search(index=index_name, body=suggest_query)
#
# # نمایش نتایج جستجو
# print([hit["_source"] for hit in response['hits']['hits']])
