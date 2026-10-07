from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import uvicorn
from typing import Optional, List
import datetime
import urllib.parse

app = FastAPI(title="Paper Notion Agent API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://mypapertool.site", "https://www.mypapertool.site", "https://paper-frontend-only-bice.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("extracted_figs", exist_ok=True)
app.mount("/extracted_figs", StaticFiles(directory="extracted_figs"), name="extracted_figs")

os.makedirs("temp", exist_ok=True)
app.mount("/temp", StaticFiles(directory="temp"), name="temp")

@app.get("/health")
def health_check():
    import utils
    fig_ver = "v3-body-text-bound" if hasattr(utils, "_locate_figure") else "OLD"
    return {"status": "ok", "message": "Backend is running!", "figure_extractor": fig_ver}

@app.get("/api/notion/databases")
def list_notion_databases():
    # Placeholder for fetching available Notion databases
    return {
        "databases": [
            {"id": "default-db", "name": "组会文献精读库 (Default)"},
            {"id": "private-db", "name": "个人私有库 (Private)"}
        ]
    }

@app.post("/api/papers/analyze")
async def analyze_paper(file: UploadFile = File(...)):
    import utils
    import traceback
    try:
        os.makedirs("temp", exist_ok=True)
        file_path = os.path.join("temp", file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 1. 提取全文
        text = utils.extract_text_from_pdf(file_path)
        
        # 2. 发给大模型进行图表级拆解
        result_json = utils.analyze_with_kimi(text)
        
        # 3. 补充 CrossRef 数据如果需要的话
        if "Title_EN" in result_json:
            crossref_data = utils.search_crossref(result_json["Title_EN"])
            if crossref_data:
                if result_json.get("DOI") == "未知" or not result_json.get("DOI"):
                    result_json["DOI"] = crossref_data["DOI"]
                if result_json.get("Journal") == "未知" or not result_json.get("Journal"):
                    result_json["Journal"] = crossref_data["Journal"]
                if result_json.get("PubDate") == "未知" or not result_json.get("PubDate"):
                    result_json["PubDate"] = crossref_data["PubDate"]

        # 4. 智能截屏图表
        fig_analysis = result_json.get("Figure_Analysis", [])
        fig_names_to_find = [fig.get("Figure_Name") for fig in fig_analysis if fig.get("Figure_Name")]
        extracted_figs = utils.extract_figures_smart(file_path, fig_names_to_find)
        result_json["extracted_figs"] = extracted_figs
                    
        return JSONResponse(content={
            "status": "success", 
            "data": result_json
        })
    except Exception as e:
        print("Analysis Error:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/papers/push_to_notion")
async def push_to_notion(payload: dict, request: Request):
    import requests
    import config
    import utils
    import re
    import math

    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    db_id = config.NOTION_DATABASE_ID
    
    title = payload.get("Title_ZH") or payload.get("Title_EN", "未知标题")
    tags = [{"name": t} for t in payload.get("Tags", [])]
    reporter = payload.get("reporter", "")
    report_date = payload.get("report_date", "")
    doi_url = payload.get("DOI", "")
    pub_date = payload.get("PubDate", "")
    journal = payload.get("Journal", "")
    jcr = payload.get("JCR", "")
    cas = payload.get("CAS", "")
    filename = payload.get("_filename", "")
    
    if not doi_url.startswith("http"):
        doi_url = f"https://doi.org/{doi_url}" if doi_url else ""

    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
        "标签": {"multi_select": tags},
    }
    if reporter:
        properties["汇报人"] = {"select": {"name": reporter}}
    if doi_url and doi_url.startswith("http"):
        properties["文献链接"] = {"url": doi_url}
    if pub_date and pub_date != "未知":
        properties["发表时间"] = {"date": {"start": pub_date}}
    if report_date:
        properties["汇报时间"] = {"date": {"start": report_date}}
    if journal and journal != "未知":
        properties["期刊名称"] = {"rich_text": [{"text": {"content": str(journal)}}]}
    if jcr and jcr != "未知":
        properties["JCR分区"] = {"select": {"name": str(jcr)}}
    if cas and cas != "未知":
        properties["中科院分区"] = {"select": {"name": str(cas)}}

    # 处理影响因子 IF
    if_val = payload.get("IF", "")
    if if_val and if_val != "未知":
        num_match = re.search(r"[-+]?\d*\.\d+|\d+", str(if_val))
        if num_match:
            try:
                val = float(num_match.group(0))
                if not math.isnan(val) and not math.isinf(val):
                    properties["影响因子"] = {"number": val}
            except Exception:
                pass

    def text_block(h2, text):
        return [
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": h2}}]}},
            {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": text}}]}}
        ]

    children = []
    
    mermaid = payload.get("Mermaid_Flowchart", "")
    if mermaid:
        children.extend([
            {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📌 核心机制流程图 (Mermaid)"}}]}},
            {"object": "block", "type": "code", "code": {"language": "mermaid", "rich_text": [{"text": {"content": mermaid}}]}}
        ])
    
    children.extend(text_block("🔬 1. 研究背景与临床痛点", payload.get("Sec02_Motivation", "")))
    children.extend(text_block("🧪 2. 核心方法与数据集", payload.get("Sec03_Methods", "")))
    
    summary = payload.get("Sec01_Summary", "")
    children.extend([
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📊 3. 关键结果与结论"}}]}},
        {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": summary}}]}}
    ])
    
    # 插入图表解析和原图
    fig_analysis = payload.get("Figure_Analysis", [])
    extracted_figs = payload.get("extracted_figs", [])
    if fig_analysis:
        children.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📈 核心图表逐一深度拆解"}}]}})
        for fig in fig_analysis:
            fig_name = fig.get("Figure_Name", "Figure")
            core = fig.get("Core_Conclusion", "")
            details = fig.get("Key_Details", "")
            
            children.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": f"📊 {fig_name}"}}]}})
            
            # 查找并上传原图
            notion_image_url = None
            matched_caption = ""
            for ef in extracted_figs:
                if ef["name"] == fig_name:
                    matched_caption = ef.get("caption", "")
                    notion_image_url = utils.upload_image_for_notion(ef["path"])
                    break
            
            if notion_image_url:
                children.append({
                    "object": "block", "type": "image",
                    "image": {"type": "external", "external": {"url": notion_image_url}}
                })
            else:
                children.append({
                    "object": "block", "type": "callout",
                    "callout": {"rich_text": [{"text": {"content": f"🖼️ 原图上传异常，请在此处手动粘贴 {fig_name} 的截图"}}], "icon": {"emoji": "⚠️"}}
                })
            
            if matched_caption:
                children.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
                    {"type": "text", "text": {"content": "📄 原文图注： "}, "annotations": {"bold": True, "color": "gray"}},
                    {"type": "text", "text": {"content": matched_caption}, "annotations": {"color": "gray", "italic": True}}
                ]}})
            
            children.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
                {"text": {"content": "🎯 核心结论： "}}, {"text": {"content": core}}
            ]}})
            children.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [
                {"text": {"content": "🔬 实验细节： "}}, {"text": {"content": details}}
            ]}})
            
    children.extend(text_block("💡 4. 局限性与研究启示", payload.get("Sec04_Limitations", "") + "\n\n启示: " + payload.get("Sec05_Ideas", "")))

    # ------ 新增: PDF Embed 功能 ------
    filename = payload.get("_filename", "")
    # 使用 FastAPI 提供的当前服务器真实基础域名（例如 https://paper-notion-agent-1.onrender.com）
    base_url = str(request.base_url).rstrip("/")
    if "localhost" in base_url or "127.0.0.1" in base_url:
        # 为了防止本地调试时 Notion API 报错导致整个推送失败，必须给一个虚拟外网域名
        base_url = "https://paper-notion-agent-1.onrender.com"
        
    encoded_filename = urllib.parse.quote(filename) if filename else "document.pdf"
    pdf_url = f"{base_url}/temp/{encoded_filename}"

    children.extend([
        {"object": "block", "type": "divider", "divider": {}},
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📄 原文 PDF 预览"}}]}},
        {"object": "block", "type": "pdf", "pdf": {"type": "external", "external": {"url": pdf_url}}}
    ])
    # --------------------------------

    children.extend([
        {"object": "block", "type": "divider", "divider": {}},
        {"object": "block", "type": "callout", "callout": {
            "rich_text": [{"text": {"content": "👇 附件区：请直接将这篇论文的 PDF 源文件和同学汇报的 PPT 拖拽到下方的空白区域中！"}}],
            "icon": {"emoji": "📎"}
        }}
    ])

    data = {
        "parent": {"database_id": db_id},
        "properties": properties,
        "children": children
    }
    
    try:
        res = requests.post(url, headers=headers, json=data)
        if res.status_code == 200:
            notion_data = res.json()
            page_url = notion_data.get("url", "")
            return JSONResponse(content={"status": "success", "message": "Successfully pushed to Notion!", "url": page_url})
        else:
            return JSONResponse(content={"status": "error", "message": res.text}, status_code=500)
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/api/papers/chat")
async def chat_with_paper(payload: dict):
    import utils
    import os
    filename = payload.get("filename")
    messages = payload.get("messages", [])
    if not filename or not messages:
        raise HTTPException(status_code=400, detail="Missing filename or messages")
    
    file_path = os.path.join("temp", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    text = utils.extract_text_from_pdf(file_path)
    
    system_prompt = f"""
    你是一个顶级科研学术助手。以下是用户正在阅读的论文全文提取内容：
    
    {text}
    
    请严格根据以上论文内容，回答用户的问题。如果问题超出了论文范围，请明确告知。使用纯正、流利的中文回答。
    """
    
    formatted_messages = [{"role": "system", "content": system_prompt}] + messages
    
    try:
        completion = utils.client.chat.completions.create(
            model="deepseek-chat",
            messages=formatted_messages,
            temperature=0.3
        )
        reply = completion.choices[0].message.content
        return JSONResponse(content={"status": "success", "reply": reply})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


