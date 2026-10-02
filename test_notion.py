import requests
import json
import config

def test_notion_connection():
    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 构造一条最简单的数据，尝试写入 Notion 默认的 Name 标题列
    data = {
        "parent": { "database_id": config.NOTION_DATABASE_ID },
        "properties": {
            "Name": { 
                "title": [
                    {
                        "text": {
                            "content": "测试文献：Agent 已经成功连接到了 Notion 🚀"
                        }
                    }
                ]
            }
        }
    }
    
    print("正在尝试连接你的 Notion，请稍等...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("\n✅ 恭喜！连接成功！快去看看你的 Notion 表格是不是多了一行数据！")
        else:
            print("\n❌ 连接失败。")
            print(f"请检查:\n1. 你的 Token 和 ID 是否填对且保留了双引号？\n2. 是否在 Notion 表格右上角 '...' -> Connections(连接) 里面，把你的 Agent 添加进去了？")
            print(f"\n技术错误详情: {response.text}")
    except Exception as e:
        print(f"\n❌ 运行出错，错误信息: {e}")
        print("如果你没装 requests 库，请在终端输入: pip install requests")

if __name__ == "__main__":
    test_notion_connection()
