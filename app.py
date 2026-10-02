import gradio as gr
import fitz  # pymupdf
from openai import OpenAI
import requests
import json
import os

# 从环境变量中读取密钥（保护你的私有资产）
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
NOTION_API_TOKEN = os.environ.get("NOTION_API_TOKEN")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for i, page in enumerate(doc):
        text += page.get_text()
        if len(text) > 40000:
            break
    return text[:40000]

def analyze_with_kimi(text):
    prompt = """
    你是一个顶级科研学术助手。请你对以下英文文献进行深度的拆解与精读。
    【核心任务变更】：现在请你放弃宽泛的全文泛读，而是聚焦于【以图表为核心 (Figure-centric)】的证据链拆解！
    请你从原文的 Results 章节和 Figure Legends 中，找出对所有核心插图（如 Figure 1, Figure 2 等）的描述，并逐图拆解其科学意义！
    
    【重要警告】：必须使用纯正、流利的**中文**来填写所有内容（除了英文文献标题和图表原名）。
    
    请严格按照以下 JSON 格式返回结果（确保输出合法的 JSON，不要附加任何非 JSON 格式的说明文字）：
    {
        "Title": "论文标题(原英文名)",
        "Tags": ["标签1", "标签2"],
        "Sec01_Summary": "一句话核心总结",
        "Sec02_Motivation": "研究动机与填补的 Gap",
        "Sec03_Methods": "核心实验设计与方法",
        "Figure_Analysis": [
            {
                "Figure_Name": "图表名称 (例如：Figure 1)",
                "Core_Conclusion": "这张图证明了什么核心结论？",
                "Key_Details": "用了什么关键实验手段/对比，看到了什么关键差异？"
            }
        ],
        "Sec04_Limitations": "局限性与缺陷",
        "Sec05_Ideas": "对课题组的启发"
    }
    
    以下是论文内容截取：
    """ + text
    
    completion = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
        {"role": "user", "content": prompt}
      ]
    )
    
    raw_response = completion.choices[0].message.content
    if raw_response.startswith("```json"):
        raw_response = raw_response.strip("```json").strip("```").strip()
    elif raw_response.startswith("```"):
        raw_response = raw_response.strip("```").strip()
        
    return json.loads(raw_response)

def push_to_notion(paper_data, reporter_name):
    if not NOTION_API_TOKEN or not NOTION_DATABASE_ID:
        raise Exception("Notion API 密钥或 Database ID 未配置！请在云端后台 Secrets 中配置这三个变量。")
        
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    tags = [{"name": tag} for tag in paper_data.get("Tags", [])[:5]]
    
    children_blocks = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "01. 一句话总结"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": paper_data.get("Sec01_Summary", "")}}]}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "02. 研究动机与 Gap"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": paper_data.get("Sec02_Motivation", "")}}]}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "03. 核心实验设计"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": paper_data.get("Sec03_Methods", "")}}]}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "📈 核心图表逐一深度拆解"}}]}
        }
    ]
    
    fig_analysis = paper_data.get("Figure_Analysis", [])
    if not fig_analysis:
        children_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "未提取到明确的图表解读。"}}]}
        })
    else:
        for fig in fig_analysis:
            fig_name = fig.get("Figure_Name", "Figure")
            core = fig.get("Core_Conclusion", "")
            details = fig.get("Key_Details", "")
            
            children_blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": f"📊 {fig_name}"}}]}
            })
            children_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "🎯 核心结论： "}},
                        {"text": {"content": core}}
                    ]
                }
            })
            children_blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": "🔬 实验细节： "}},
                        {"text": {"content": details}}
                    ]
                }
            })
            children_blocks.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"text": {"content": f"🖼️ 请在此处粘贴 {fig_name} 的原版截图 (Ctrl+V)"}}],
                    "icon": {"emoji": "📸"},
                    "color": "blue_background"
                }
            })
            
    children_blocks.extend([
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "04. 局限性分析"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": paper_data.get("Sec04_Limitations", "")}}]}
        },
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "05. 课题组启发与借鉴思路"}}]}
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": paper_data.get("Sec05_Ideas", "")}}]}
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
                "rich_text": [{"text": {"content": "👇 附件区：请将这篇论文的 PDF 源文件拖拽到此处备份！"}}],
                "icon": {"emoji": "📎"}
            }
        }
    ])
    
    data = {
        "parent": { "database_id": NOTION_DATABASE_ID },
        "properties": {
            "Name": { "title": [{"text": {"content": paper_data.get("Title", "未提取出标题")}}] },
            "标签": { "multi_select": tags },
            "汇报人": { "select": {"name": reporter_name} },
        },
        "children": children_blocks
    }
    
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 200:
        raise Exception(f"Notion 推送失败: {res.text}")

def process_upload(file_obj, reporter_name):
    if not DEEPSEEK_API_KEY:
        yield "⚠️ 致命错误：未配置 DEEPSEEK_API_KEY！请在云端系统设置(Secrets)中配置。", "*等待上传文献...*"
        return
    if not file_obj or not reporter_name:
        yield "⚠️ 请先上传 PDF 文件并填写汇报人姓名！", "*等待上传文献...*"
        return
        
    try:
        loading_text = "> 🧠 **DeepSeek 核心引擎已接管任务，正在逐图拆解核心证据链中，预计需要 30 秒...**"
        yield "🚀 收到文件！正在提取 PDF 文字内容...", loading_text
        
        text = extract_pdf_text(file_obj.name)
        
        yield f"🧠 正在调用 DeepSeek 进行基于图表 (Figure-centric) 的深度拆解...", loading_text
        paper_data = analyze_with_kimi(text)
        
        yield "📝 精读完成！正在同步至你的 Notion...", loading_text
        push_to_notion(paper_data, reporter_name)
        
        fig_md = ""
        fig_analysis = paper_data.get("Figure_Analysis", [])
        if not fig_analysis:
            fig_md = "未提取到明确的图表解读。\\n"
        else:
            for fig in fig_analysis:
                fig_name = fig.get("Figure_Name", "Figure")
                core = fig.get("Core_Conclusion", "")
                details = fig.get("Key_Details", "")
                fig_md += f"#### 📊 {fig_name}\\n"
                fig_md += f"- **🎯 核心结论：** {core}\\n"
                fig_md += f"- **🔬 实验细节：** {details}\\n\\n"
        
        db_id = NOTION_DATABASE_ID.replace('-', '') if NOTION_DATABASE_ID else ""

        preview_md = f"""
### 📑 图表级核心拆解实时预览
**标题:** {paper_data.get('Title', '未知标题')}
**汇报人:** {reporter_name} | **提取标签:** {', '.join(paper_data.get('Tags', []))}

---

#### 01. 一句话总结
{paper_data.get('Sec01_Summary', '')}

#### 02. 研究动机与 Gap
{paper_data.get('Sec02_Motivation', '')}

#### 03. 核心实验设计
{paper_data.get('Sec03_Methods', '')}

---
### 📈 核心图表逐一深度拆解
*(请在 Notion 页面对应位置贴入原版截图)*

{fig_md}
---

#### 04. 局限性与缺陷分析
{paper_data.get('Sec04_Limitations', '')}

#### 05. 课题组启发与借鉴思路
{paper_data.get('Sec05_Ideas', '')}

*—— 🎉 本内容已永久归档至你的 Notion 知识库！*
        """
        
        yield "✅ 极其完美！以图表为核心深度的专属文献卡片，已成功推送至 Notion！", preview_md
    except Exception as e:
        yield f"❌ 处理失败，错误信息: {str(e)}", "*等待上传文献...*"

custom_theme = gr.themes.Soft(
    primary_hue="indigo",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

with gr.Blocks(title="文献图表级精读归档系统", theme=custom_theme) as demo:
    db_id = os.environ.get("NOTION_DATABASE_ID", "").replace('-', '') if os.environ.get("NOTION_DATABASE_ID") else ""
    notion_url = f"https://notion.so/{db_id}" if db_id else "https://notion.so"
    
    gr.HTML(f"""
    <div style="text-align: center; max-width: 800px; margin: 0 auto; padding-top: 20px; padding-bottom: 20px;">
        <h1 style="font-weight: 800; font-size: 2em; margin-bottom: 8px;">📚 智能文献(图表级)精读与归档系统</h1>
        <p style="font-size: 16px; color: #666; margin-bottom: 15px;">基于图表(Figure-centric)深挖的自动拆解、证据链提取与云端同步引擎</p>
        <a href="{notion_url}" target="_blank" style="display: inline-block; padding: 8px 16px; background-color: #f1f5f9; color: #334155; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px; border: 1px solid #e2e8f0; transition: all 0.2s;">
            👉 点击此处，直达课题组云端知识库
        </a>
    </div>
    """)
    
    with gr.Row():
        with gr.Column():
            reporter = gr.Textbox(label="汇报人姓名", placeholder="填写姓名后可供数据库检索")
            pdf_file = gr.File(label="拖拽上传文献 PDF", file_types=[".pdf"])
            with gr.Row():
                submit_btn = gr.Button("✨ 启动逐图拆解与归档入库", variant="primary", scale=2, size="lg")
                clear_btn = gr.Button("🧹 清空准备下一篇", variant="secondary", scale=1, size="lg")
            
        with gr.Column():
            status_box = gr.Textbox(label="运行状态日志", lines=5)
            
    preview_box = gr.Markdown(label="解析结果实时预览大屏", value="*等待上传文献...*")
    
    gr.HTML("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #eaeaea;">
        <p style="font-size: 14px; color: #888;">
            Designed & Developed by <strong>Liu</strong>
        </p>
    </div>
    """)
    
    submit_btn.click(fn=process_upload, inputs=[pdf_file, reporter], outputs=[status_box, preview_box])
    
    def clear_all():
        return None, "", "", "*等待上传文献...*"
    clear_btn.click(fn=clear_all, inputs=[], outputs=[pdf_file, reporter, status_box, preview_box])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
