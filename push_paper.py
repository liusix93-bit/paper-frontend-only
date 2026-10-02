import requests
import json
import config

def push_to_notion():
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    data = {
        "parent": { "database_id": config.NOTION_DATABASE_ID },
        "properties": {
            "Name": { "title": [{"text": {"content": "整合代谢组学和蛋白质组学以识别心力衰竭和房颤的新药物靶点"}}] },
            "标签": { "multi_select": [{"name": "心衰"}, {"name": "心房颤动"}, {"name": "代谢组学"}, {"name": "孟德尔随机化"}, {"name": "Genome Medicine"}] },
            "汇报人": { "select": {"name": "Marion van Vugt (作者)"} },
            "文献链接": { "url": "https://doi.org/10.1186/s13073-024-01395-4" }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📚 AI 精读卡片"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "【期刊与年份】Genome Medicine (2024)"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "【研究背景】代谢改变在心脏疾病（房颤和心衰）的病理生理学中发挥重要作用，本研究旨在寻找新的血浆代谢物和蛋白质药物靶点。"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "【核心方法】使用孟德尔随机化（MR）评估了174种代谢物（在86,507名参与者中）与房颤、心衰等疾病的关联，并对1567种血浆蛋白进行了 cis-MR 分析，寻找影响这些代谢物的蛋白。"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "【关键结论与创新点】研究鉴定出35种与心脏病相关的血浆代谢物，并成功将其与38种在心脏组织中表达的、具备成药潜力的蛋白质联系起来。例如发现较高的 RET 值与磷脂酰胆碱相关，并能降低房颤和心衰风险。这为相关药物开发提供了直接靶点。"}}]}
            }
        ]
    }
    
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        print("✅ 成功推送论文精读卡到 Notion！")
    else:
        print(f"❌ 推送失败: {res.text}")

if __name__ == "__main__":
    push_to_notion()
