import requests
import json
import config

def find_authorized_pages():
    print("Agent: 正在使用雷达扫描所有向我开放大门的房间...")
    url = "https://api.notion.com/v1/search"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "query": "",
        "sort": {
            "direction": "descending",
            "timestamp": "last_edited_time"
        }
    }
    
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        results = res.json().get("results", [])
        if not results:
            print("❌ 扫描结果: 空！\n即使你说你加了连接，但 Notion 认为没有任何页面对我开放。可能是你在别的浏览器账号，或者建了多个 Paper Agent 搞混了！")
        else:
            print(f"✅ 找到了 {len(results)} 个向我开放的对象:")
            first_id = None
            for item in results:
                obj_type = item.get('object')
                # 尝试安全地获取标题
                title = "未命名"
                try:
                    if obj_type == "page":
                        if "title" in item["properties"]:
                            title = item["properties"]["title"]["title"][0]["plain_text"]
                        elif "Name" in item["properties"]:
                            title = item["properties"]["Name"]["title"][0]["plain_text"]
                    elif obj_type == "database":
                        title = item["title"][0]["plain_text"]
                except:
                    pass
                
                print(f"  - 名字: [{title}] | 类型: [{obj_type}] | ID: {item.get('id')}")
                if not first_id:
                    first_id = item.get('id').replace("-", "")
            
            print(f"\n💡 自动帮你锁定第一个找到的 ID: {first_id}")
            
            with open("config.py", "r", encoding="utf-8") as f:
                content = f.read()
            new_content = content.replace(config.NOTION_DATABASE_ID, first_id)
            with open("config.py", "w", encoding="utf-8") as f:
                f.write(new_content)
    else:
        print(f"❌ 请求失败: {res.text}")

if __name__ == "__main__":
    find_authorized_pages()
