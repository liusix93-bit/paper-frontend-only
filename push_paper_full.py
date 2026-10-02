import requests
import json
import config

def push_full_paper_to_notion():
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    mermaid_code = """graph TD
    A[HF & AF 患者临床队列] -->|全基因组关联| B(代谢组学数据: 174种)
    A -->|全基因组关联| C(蛋白组学数据: 1567种)
    B --> D{孟德尔随机化<br/>Mendelian Randomization}
    C --> D
    D --> E[35种心脏病相关代谢物]
    D --> F[38种心脏特异性成药蛋白]
    E --> G(药物靶点相互作用图谱)
    F --> G
    G --> H((核心靶点发现<br/>例如: RET受体调控磷脂酰胆碱))"""

    data = {
        "parent": { "database_id": config.NOTION_DATABASE_ID },
        "properties": {
            "Name": { "title": [{"text": {"content": "[完全体展示] 整合代谢组与蛋白组鉴定心衰/房颤新靶点"}}] },
            "标签": { "multi_select": [{"name": "心衰"}, {"name": "多组学"}, {"name": "孟德尔随机化"}, {"name": "靶点发现"}] },
            "汇报人": { "select": {"name": "张三 (演示)"} },
            "文献链接": { "url": "https://doi.org/10.1186/s13073-024-01395-4" }
        },
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📌 核心机制流程图 (Mermaid)"}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "language": "mermaid",
                    "rich_text": [{"text": {"content": mermaid_code}}]
                }
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🔬 1. 研究背景与临床痛点"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "心力衰竭 (HF) 和心房颤动 (AF) 是主要的全球健康负担，存在显著的未满足医疗需求。尽管已知能量代谢紊乱和脂质分布改变是其病理生理学特征，但驱动这些代谢变化的具体蛋白质及其因果关系尚不明确。因此，本研究试图打通“基因-蛋白-代谢物-疾病”的关联通路，为老药新用或新药开发提供直接的干预靶点。"}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🧪 2. 核心方法与数据集"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "采用了强大的多组学两样本孟德尔随机化（Two-sample MR）设计。\n• 代谢组学：获取了174种循环代谢物的GWAS数据（包含脂质、氨基酸等）。\n• 蛋白质组学：引入了1567种血浆蛋白作为暴露因素。\n• 结果变量：利用AF和HF的大规模GWAS汇总统计数据，评估蛋白质对代谢物和疾病的因果效应。"}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "📊 3. 关键结果与证据链"}}]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "鉴定出 35 种在 AF 或 HF 发生中具有潜在因果作用的代谢物（如特定脂质和氨基酸亚型）。"}}]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "成功地将这些代谢物与 38 种具有“成药潜力”且在心脏组织高表达的蛋白质建立起了上下游联系。"}}]}
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"text": {"content": "明星发现：RET（一种原癌基因酪氨酸激酶受体）的水平升高与磷脂酰胆碱浓度上升有关，并且明确指向 AF 和 HF 风险的降低！这一发现极具临床转化价值。"}}]}
            },
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "💡 4. 局限性与研究启示"}}]}
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"text": {"content": "虽然 MR 设计减少了混杂，但依赖于可用 GWAS 的统计功效，且主要局限于欧洲血统人群。未来的启示在于：可以通过体外实验直接针对 RET 受体进行验证，探讨其调控磷脂酰胆碱代谢并保护心脏的具体分子机制。"}}]}
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            },
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": "👇 附件区：请直接将这篇论文的 PDF 源文件和同学汇报的 PPT 拖拽到下方的空白区域中！"}}],
                    "icon": {"emoji": "📎"}
                }
            }
        ]
    }
    
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        print("✅ 成功推送【完全体】精读卡到 Notion！")
    else:
        print(f"❌ 推送失败: {res.text}")

if __name__ == "__main__":
    push_full_paper_to_notion()
