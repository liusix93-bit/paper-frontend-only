import requests
import json
import os
import config

url = "https://api.notion.com/v1/pages"
headers = {
    "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

data = {
    "parent": {"database_id": config.NOTION_DATABASE_ID},
    "properties": {
        "Name": {"title": [{"text": {"content": "Test PDF Embed"}}]}
    },
    "children": [
        {
            "object": "block",
            "type": "pdf",
            "pdf": {
                "type": "external",
                "external": {
                    "url": "http://localhost:8000/temp/dummy.pdf"
                }
            }
        }
    ]
}

res = requests.post(url, headers=headers, json=data)
print(res.status_code)
print(res.text)
