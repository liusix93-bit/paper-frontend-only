import requests
import json
import config
import os

def setup():
    print("Agent: 检测到你提供的可能是一栋大楼(外层页面)的 ID...")
    print("Agent: 不要紧！既然你已经给我开了门，我直接在里面为你新建一个完美的卡片抽屉(数据库)！")
    
    url = "https://api.notion.com/v1/databases"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 构建完美的表头
    data = {
        "parent": { "page_id": config.NOTION_DATABASE_ID },
        "title": [{"type": "text", "text": {"content": "📚 组会文献精读库 (Agent自动创建)"}}],
        "properties": {
            "Name": {"title": {}},
            "标签": {"multi_select": {}},
            "汇报人": {"select": {}},
            "日期": {"date": {}},
            "文献链接": {"url": {}}
        }
    }
    
    res = requests.post(url, headers=headers, json=data)
    
    if res.status_code == 200:
        real_db_id = res.json()["id"]
        print(f"\n[成功] 已经建好了一个带所有属性标签的完美表格！\n真正的表格 ID 是: {real_db_id}")
        
        # 自动替换 config.py
        config_path = "config.py"
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 考虑到 Notion API 返回的 ID 带横杠，而用户填的不带横杠，我们统一去掉横杠写入
        clean_id = real_db_id.replace("-", "")
        new_content = content.replace(config.NOTION_DATABASE_ID, clean_id)
        
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(new_content)
            
        print("[成功] 已经自动帮你把正确的 ID 写进 config.py 啦！\n接下来自动开始写入测试卡片...")
    else:
        print(f"\n[失败] 自动创建失败，原因: {res.text}")

if __name__ == "__main__":
    setup()
