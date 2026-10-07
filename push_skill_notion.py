import requests
import json
import config

def push_skill_to_notion(skill_name, skill_markdown_content):
    """
    将 paper2agent 生成的 Skill 推送到 Notion 知识库中。
    生成的 markdown 内容将被放入 Notion Page 的代码块中，方便用户一键复制。
    """
    url = "https://api.notion.com/v1/pages"
    
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # 构造 Notion Page 的数据体
    data = {
        "parent": { "database_id": config.NOTION_DATABASE_ID },
        "properties": {
            # 数据库的第一列通常叫 "Name" 或 "标题"
            "Name": { 
                "title": [
                    {
                        "text": {
                            "content": f"🛠️ Agent Skill: {skill_name}"
                        }
                    }
                ]
            }
        },
        # children 用来定义点进 Page 里面的正文内容
        "children": [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "使用说明"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": "请点击下方代码块右上角的“Copy”按钮，将其保存为本地的 SKILL.md 文件即可在您的 Agent 中加载使用。"}}]
                }
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": skill_markdown_content}}],
                    "language": "markdown"
                }
            }
        ]
    }
    
    print(f"正在将 Skill [{skill_name}] 推送到 Notion 知识库...")
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if response.status_code == 200:
            print("\n✅ 推送成功！")
            result = response.json()
            page_url = result.get('url', 'URL未返回')
            print(f"🔗 Notion 页面链接: {page_url}")
            return True, page_url
        else:
            print(f"\n❌ 推送失败，错误代码: {response.status_code}")
            print(f"错误详情: {response.text}")
            return False, response.text
    except Exception as e:
        print(f"\n❌ 运行出错，错误信息: {e}")
        return False, str(e)

if __name__ == "__main__":
    # 测试数据模拟 paper2agent 的输出
    sample_skill_name = "AI-Paper-Analyzer"
    sample_skill_content = """---
name: ai-paper-analyzer
description: 专门解析大模型架构论文的智能体技能
---
# 指令
1. 提取模型架构图的描述。
2. 总结数据集来源和训练参数。
3. 输出为 Notion 可读的格式。
"""
    push_skill_to_notion(sample_skill_name, sample_skill_content)
