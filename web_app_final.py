import gradio as gr
import fitz  # pymupdf
from openai import OpenAI
import requests
import json
import config
import os
import re
import urllib.parse
import sys

# --- 终极 Windows 编码崩溃补丁 ---
class SafeStream:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        try:
            self.stream.write(data)
        except UnicodeEncodeError:
            encoding = getattr(self.stream, 'encoding', 'ascii') or 'ascii'
            self.stream.write(data.encode(encoding, 'ignore').decode(encoding))
    def flush(self):
        try:
            self.stream.flush()
        except:
            pass
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

if not getattr(sys.stdout, '_is_safe', False):
    sys.stdout = SafeStream(sys.stdout)
    sys.stdout._is_safe = True
if not getattr(sys.stderr, '_is_safe', False):
    sys.stderr = SafeStream(sys.stderr)
    sys.stderr._is_safe = True
# ---------------------------------

# 配置 DeepSeek 客户端
client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
)

def extract_pdf_text(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    # 提取前几万字，足够覆盖摘要、背景、方法、和核心结论
    for i, page in enumerate(doc):
        text += page.get_text()
        if len(text) > 40000:
            break
    return text[:40000]

def extract_figures_smart(pdf_path, fig_names_to_find):
    output_dir = "extracted_figs"
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    extracted = []
    
    for fig_name in fig_names_to_find:
        # 核心防翻车设计：提取更复杂的图号，支持 "1-1", "S1", "1.1", "1A", "1-A"
        m = re.search(r'(?:图|Figure|Fig\.?|FIG\.?)\s*([A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)?)', fig_name, re.IGNORECASE)
        if not m:
            continue
        fig_num = m.group(1)
        
        found_rect = None
        matched_caption = ""
        for page_num, page in enumerate(doc):
            blocks = page.get_text("blocks")
            for b in blocks:
                text = b[4].strip()
                # 兼容中英双语图注，支持 "图1-1心衰组" (无空格)，且防止 Figure 1 误匹配 Figure 10
                pattern = r'^(?:Figure|Fig\.?|FIG\.?|图)\s*' + re.escape(fig_num) + r'(?:[^a-zA-Z0-9]|$)'
                if re.match(pattern, text, re.IGNORECASE):
                    found_rect = fitz.Rect(b[:4])
                    matched_caption = text.replace("\n", " ")
                    break
            
            if found_rect:
                # 智能寻找与图注匹配的真实图像区域 (Raster Images)
                try:
                    img_bboxes = [fitz.Rect(img["bbox"]) for img in page.get_image_info()]
                except:
                    img_bboxes = []
                
                # 筛选出在图注上方或同一页的真实图片 (高度>50剔除页眉小标)
                target_bboxes = [r for r in img_bboxes if r.height > 50 and r.y0 < found_rect.y1 + 50]
                
                if target_bboxes:
                    # 增强防污：如果有多个图片块，过滤掉可能是上一张图（离当前图注过远）的无关图片
                    closest_dist = min(abs(found_rect.y0 - r.y1) for r in target_bboxes)
                    target_bboxes = [r for r in target_bboxes if abs(found_rect.y0 - r.y1) <= closest_dist + 400]
                    
                    min_x = min(r.x0 for r in target_bboxes)
                    min_y = min(r.y0 for r in target_bboxes)
                    max_x = max(r.x1 for r in target_bboxes)
                    max_y = max(r.y1 for r in target_bboxes)
                    
                    # 核心防污设计：坚决避开图注本身！
                    if found_rect.y0 >= min_y: # 图注在图片下方
                        max_y = min(max_y, found_rect.y0 - 2)
                    else: # 图注在图片上方
                        min_y = max(min_y, found_rect.y1 + 2)
                        
                    clip_rect = fitz.Rect(max(0, min_x-2), max(0, min_y-2), min(page.rect.width, max_x+2), min(page.rect.height, max_y+2))
                else:
                    # 极端兜底：如果是纯矢量图，退化为截取上方固定区域，但严格砍掉图注文字
                    top_y = max(0, found_rect.y0 - 450)
                    clip_rect = fitz.Rect(0, top_y, page.rect.width, max(0, found_rect.y0 - 2))
                
                pix = page.get_pixmap(clip=clip_rect, dpi=200)
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                safe_name = fig_name.replace(" ", "_").replace(".", "").replace(":", "")
                img_path = os.path.join(output_dir, f"{safe_name}_{page_num}.png")
                pix.save(img_path)
                pix = None
                
                extracted.append({
                    "name": fig_name, 
                    "caption": matched_caption,
                    "path": img_path
                })
                break 
                
    return extracted

def analyze_with_kimi(text):
    prompt = """
    你是一个顶级科研学术助手。请你对以下英文文献进行深度的拆解与精读。
    【核心任务变更】：现在请你放弃宽泛的全文泛读，而是聚焦于【以图表为核心 (Figure-centric)】的证据链拆解！
    请你从原文的 Results 章节和 Figure Legends 中，找出对所有核心插图（如 Figure 1, Figure 2 等）的描述，并逐图拆解其科学意义！
    
    【重要警告】：必须使用纯正、流利的**中文**来填写所有内容（除了英文文献标题和图表原名）。
    
    请严格按照以下 JSON 格式返回结果（确保输出合法的 JSON，不要附加任何非 JSON 格式的说明文字）：
    {
        "Title_EN": "论文英文原标题",
        "Title_ZH": "论文精美的中文翻译标题",
        "DOI": "文献的DOI或网页链接 (例如 https://doi.org/10.1038/s41586... 若无则填未知)",
        "PubDate": "论文发表日期 (格式 YYYY-MM-DD, 若不知则填当前日期)",
        "Journal": "期刊名称 (如果在文中找不到，请凭借知识库推测，若不知则填未知)",
        "JCR": "JCR分区 (如 Q1, 若不知则填 未知)",
        "CAS": "中科院分区 (如 1区, 若不知则填 未知)",
        "IF": "影响因子 (如 15.3, 若不知则填 未知)",
        "Tags": ["标签1", "标签2"],
        "Mermaid_Flowchart": "用 mermaid 语法写一段流程图总结整篇文章的核心逻辑。注意：流程图里的【节点内容文本】必须全部翻译成纯正的中文！但 mermaid代码中的【语法关键字】（如 flowchart TD, 箭头等）必须是纯英文，绝对不能翻译为中文。直接写代码，不要用 markdown包裹",
        "Sec01_Summary": "一句话核心总结",
        "Sec02_Motivation": "研究动机与填补的 Gap",
        "Sec03_Methods": "核心实验设计与方法",
        "Figure_Analysis": [
            {
                "Figure_Name": "原版图表名称 (【绝对不能翻译】，必须保持原文如 Figure 1)",
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
    
    # 使用正则表达式强制提取最外层的 {} 包围的 JSON 字符串，防止模型输出额外对话文本
    match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if match:
        json_str = match.group(0)
    else:
        json_str = raw_response
        
    return json.loads(json_str)

def upload_image_for_notion(file_path):
    print(f"Start uploading image for Notion: {file_path}")
    
    # 使用更加稳定且能在国内环境访问的 freeimage.host API
    try:
        url = "https://freeimage.host/api/1/upload"
        data = {"key": "6d207e02198a847aa98d0a2a901485a5"}
        with open(file_path, "rb") as f:
            files = {"source": f}
            response = requests.post(url, data=data, files=files, timeout=20)
            if response.status_code == 200:
                res_json = response.json()
                if "image" in res_json and "url" in res_json["image"]:
                    img_url = res_json["image"]["url"]
                    print(f"Image upload success: {img_url}")
                    return img_url
    except Exception as e:
        print(f"Image upload exception: {e}")
        pass
        
    return None

def get_notion_db_properties():
    url = f"https://api.notion.com/v1/databases/{config.NOTION_DATABASE_ID}"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Notion-Version": "2022-06-28"
    }
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("properties", {})
    except:
        pass
    return {}

def push_to_notion(paper_data, reporter_name, report_date_str, extracted_figs=None, progress=None):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {config.NOTION_API_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    tags = [{"name": tag} for tag in paper_data.get("Tags", [])[:5]]
    
    children_blocks = [
        {
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"text": {"content": f"🇬🇧 {paper_data.get('Title_EN', '未提取出英文标题')}"}}],
                "color": "gray_background"
            }
        }
    ]
    
    mermaid_code = paper_data.get("Mermaid_Flowchart", "")
    if mermaid_code:
        if mermaid_code.startswith("```mermaid"):
            mermaid_code = mermaid_code.replace("```mermaid", "").strip("```").strip()
        elif mermaid_code.startswith("```"):
            mermaid_code = mermaid_code.strip("```").strip()
            
        children_blocks.extend([
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "🗺️ 核心逻辑流程图"}}]}
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"text": {"content": mermaid_code}}],
                    "language": "mermaid"
                }
            }
        ])
    
    children_blocks.extend([
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
    ])
    
    fig_analysis = paper_data.get("Figure_Analysis", [])
    if not fig_analysis:
        children_blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [{"text": {"content": "未提取到明确的图表解读。"}}]}
        })
    else:
        total_figs = len(fig_analysis)
        for idx, fig in enumerate(fig_analysis):
            fig_name = fig.get("Figure_Name", "Figure")
            core = fig.get("Core_Conclusion", "")
            details = fig.get("Key_Details", "")
            
            matched_caption = ""
            matched_path = ""
            if extracted_figs:
                for ef in extracted_figs:
                    if ef["name"] == fig_name:
                        matched_caption = ef["caption"]
                        matched_path = ef["path"]
                        break
            
            children_blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": f"📊 {fig_name}"}}]}
            })
            
            if matched_path:
                if progress:
                    # 分配 Notion 上传阶段进度的动态描述
                    progress(0.75 + (0.2 * (idx / total_figs)), desc=f"☁️ 正在将 {fig_name} 发送给 Notion 图床...")
                notion_image_url = upload_image_for_notion(matched_path)
                if notion_image_url:
                    for ef in extracted_figs:
                        if ef["name"] == fig_name:
                            ef["public_url"] = notion_image_url
                            break
            else:
                notion_image_url = None
                
            if notion_image_url:
                children_blocks.append({
                    "object": "block",
                    "type": "image",
                    "image": {
                        "type": "external",
                        "external": {
                            "url": notion_image_url
                        }
                    }
                })
            else:
                children_blocks.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [{"text": {"content": f"🖼️ 原图上传异常，请在此处手动粘贴 {fig_name} 的截图"}}],
                        "icon": {"emoji": "⚠️"},
                        "color": "yellow_background"
                    }
                })
                
            if matched_caption:
                children_blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "📄 原文图注： "}, "annotations": {"bold": True, "color": "gray"}},
                            {"type": "text", "text": {"content": matched_caption}, "annotations": {"color": "gray", "italic": True}}
                        ]
                    }
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
    
    db_props = get_notion_db_properties()
    properties = {
        "Name": { "title": [{"text": {"content": paper_data.get("Title_ZH", "未提取出标题")}}] },
        "标签": { "multi_select": tags },
        "汇报人": { "select": {"name": reporter_name} },
    }
    
    # 动态注入文献链接和日期
    if "文献链接" in db_props and paper_data.get("DOI") and paper_data.get("DOI") != "未知":
        if db_props["文献链接"]["type"] == "url":
            doi_val = paper_data.get("DOI")
            if not doi_val.startswith("http"):
                doi_val = "https://doi.org/" + doi_val.replace("doi.org/", "")
            properties["文献链接"] = {"url": doi_val}
        elif db_props["文献链接"]["type"] == "rich_text":
            properties["文献链接"] = {"rich_text": [{"text": {"content": paper_data.get("DOI")}}]}
            
    pub_date_val = None
    if paper_data.get("PubDate") and paper_data.get("PubDate") != "未知":
        import re
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", paper_data.get("PubDate"))
        if date_match: pub_date_val = date_match.group(0)
            
    if pub_date_val:
        if "发表时间" in db_props:
            if db_props["发表时间"]["type"] == "date": properties["发表时间"] = {"date": {"start": pub_date_val}}
            elif db_props["发表时间"]["type"] == "rich_text": properties["发表时间"] = {"rich_text": [{"text": {"content": pub_date_val}}]}
        elif "日期" in db_props:
            if db_props["日期"]["type"] == "date": properties["日期"] = {"date": {"start": pub_date_val}}
            elif db_props["日期"]["type"] == "rich_text": properties["日期"] = {"rich_text": [{"text": {"content": pub_date_val}}]}

    if "汇报时间" in db_props and report_date_str:
        if db_props["汇报时间"]["type"] == "date": properties["汇报时间"] = {"date": {"start": report_date_str}}
        elif db_props["汇报时间"]["type"] == "rich_text": properties["汇报时间"] = {"rich_text": [{"text": {"content": report_date_str}}]}

    # 动态注入期刊属性，防止用户未创建该列导致 API 报错
    for key, source_key in [("期刊名称", "Journal"), ("JCR分区", "JCR"), ("中科院分区", "CAS"), ("影响因子", "IF")]:
        if key in db_props:
            prop_type = db_props[key]["type"]
            val = str(paper_data.get(source_key, ""))
            if not val or val == "未知":
                continue
            if prop_type == "rich_text":
                properties[key] = {"rich_text": [{"text": {"content": val}}]}
            elif prop_type == "select":
                properties[key] = {"select": {"name": val}}
            elif prop_type == "number":
                try:
                    import re
                    num_match = re.search(r"[-+]?\d*\.\d+|\d+", val)
                    if num_match:
                        properties[key] = {"number": float(num_match.group(0))}
                except:
                    pass

    data = {
        "parent": { "database_id": config.NOTION_DATABASE_ID },
        "properties": properties,
        "children": children_blocks
    }
    
    if progress:
        progress(0.95, desc="📝 排版完毕，请求 Notion 最终写库...")
        
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 200:
        raise Exception(f"Notion 推送失败: {res.text}")

def search_crossref(title):
    try:
        import urllib.parse
        safe_title = urllib.parse.quote(title)
        url = f"https://api.crossref.org/works?query.title={safe_title}&select=title,DOI,container-title,published-print,published-online&rows=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data["message"]["items"]:
                item = data["message"]["items"][0]
                doi = item.get("DOI", "")
                journal = item.get("container-title", [""])[0] if item.get("container-title") else ""
                
                pub_date = ""
                date_parts = item.get("published-print", item.get("published-online", {})).get("date-parts", [[]])[0]
                if date_parts:
                    if len(date_parts) == 3:
                        pub_date = f"{date_parts[0]}-{date_parts[1]:02d}-{date_parts[2]:02d}"
                    elif len(date_parts) == 2:
                        pub_date = f"{date_parts[0]}-{date_parts[1]:02d}-01"
                    elif len(date_parts) == 1:
                        pub_date = f"{date_parts[0]}-01-01"
                
                return {"DOI": doi, "Journal": journal, "PubDate": pub_date}
    except:
        pass
    return None

def process_upload(file_obj, reporter_name, report_date_str, progress=gr.Progress()):
    if not file_obj or not reporter_name:
        yield "⚠️ 请先上传 PDF 文件并填写汇报人姓名！", "*等待上传文献...*"
        return
        
    try:
        loading_text = "> 🧠 **DeepSeek 核心引擎已接管任务，全自动执行中...**"
        
        # 阶段 1：解析文字
        progress(0.05, desc="🐾 喵呜！正在努力拆解 PDF 文字结构...")
        yield "🚀 收到文件！正在提取 PDF 文字内容...", loading_text
        text = extract_pdf_text(file_obj.name)
        
        # 阶段 2：模型推理
        progress(0.20, desc="🧠 DeepSeek 开始深度思考与证据链推演 (这步稍微耗时，请喝口茶~ 🍵)")
        yield f"🧠 正在调用 DeepSeek 进行基于图表 (Figure-centric) 的深度拆解...", loading_text
        paper_data = analyze_with_kimi(text)
        
        title_en = paper_data.get('Title_EN', '')
        if title_en and (not paper_data.get('DOI') or paper_data.get('DOI') == '未知' or not paper_data.get('Journal') or paper_data.get('Journal') == '未知'):
            progress(0.25, desc="🌐 正在通过 Crossref 引擎全网定位文献元数据...")
            yield "🌐 DeepSeek 提取元数据失败，启动 Crossref 全网检索补全...", loading_text
            meta = search_crossref(title_en)
            if meta:
                if meta["DOI"] and paper_data.get("DOI", "未知") == "未知": paper_data["DOI"] = meta["DOI"]
                if meta["Journal"] and paper_data.get("Journal", "未知") == "未知": paper_data["Journal"] = meta["Journal"]
                if meta["PubDate"] and paper_data.get("PubDate", "未知") == "未知": paper_data["PubDate"] = meta["PubDate"]
                
        fig_analysis = paper_data.get("Figure_Analysis", [])
        fig_names_to_find = [fig.get("Figure_Name") for fig in fig_analysis if fig.get("Figure_Name")]
        
        # 阶段 3：智能截屏取图
        progress(0.60, desc="✂️ 模型解析完毕！小猫咪启动雷达定位引擎，正在回源精确截图中...")
        yield "🎯 深度拆解完毕！正在回到原文档中智能精准定位并截取高清大图...", loading_text
        extracted_figs = extract_figures_smart(file_obj.name, fig_names_to_find)
            
        yield "📝 图表提取完毕！正在自动同步并转存图片至 Notion...", loading_text
        
        # 阶段 4：图床同步与 Notion 写入
        progress(0.75, desc="☁️ 提取完成！准备推流图片到公网云端...")
        push_to_notion(paper_data, reporter_name, report_date_str, extracted_figs, progress=progress)
        
        # 阶段 5：前端渲染
        progress(1.0, desc="🎉 大功告成，完美落地！")
        
        fig_md = ""
        if not fig_analysis:
            fig_md = "未提取到明确的图表解读。\\n"
        else:
            for fig in fig_analysis:
                fig_name = fig.get("Figure_Name", "Figure")
                core = fig.get("Core_Conclusion", "")
                details = fig.get("Key_Details", "")
                
                matched_caption = ""
                matched_path = ""
                pub_url = ""
                for ef in extracted_figs:
                    if ef["name"] == fig_name:
                        matched_caption = ef["caption"]
                        matched_path = ef["path"]
                        pub_url = ef.get("public_url", "")
                        break
                        
                fig_md += f"#### 📊 {fig_name}\n"
                if pub_url:
                    fig_md += f"![{fig_name}]({pub_url})\n\n"
                elif matched_path:
                    abs_path = os.path.abspath(matched_path).replace("\\", "/")
                    safe_path = urllib.parse.quote(abs_path)
                    fig_md += f"![{fig_name}](/file={safe_path})\n\n"
                    
                fig_md += f"- **🎯 核心结论：** {core}\n"
                fig_md += f"- **🔬 实验细节：** {details}\n"
                if matched_caption:
                    fig_md += f"- **📄 原文图注：** *{matched_caption}*\n\n"
                fig_md += "\n"

        mermaid_code = paper_data.get("Mermaid_Flowchart", "")
        if mermaid_code.startswith("```mermaid"):
            mermaid_code = mermaid_code.replace("```mermaid", "").strip("```").strip()
        elif mermaid_code.startswith("```"):
            mermaid_code = mermaid_code.strip("```").strip()
            
        preview_md = f"""
### 📑 图表级核心拆解实时预览
**标题:** {paper_data.get('Title_ZH', '未知标题')}
**英文:** {paper_data.get('Title_EN', '')}
**期刊:** {paper_data.get('Journal', '')} | **IF:** {paper_data.get('IF', '')} | **JCR:** {paper_data.get('JCR', '')} | **中科院:** {paper_data.get('CAS', '')}
**链接:** {paper_data.get('DOI', '')} | **日期:** {paper_data.get('PubDate', '')}
**汇报人:** {reporter_name} | **提取标签:** {', '.join(paper_data.get('Tags', []))}

---

#### 🗺️ 核心逻辑流程图
*(✨ 核心逻辑框架已成功生成，由于网页端不支持高级渲染，请点击上方按钮去 Notion 中查阅精美可视化的原图！)*

#### 01. 一句话总结
{paper_data.get('Sec01_Summary', '')}

#### 02. 研究动机与 Gap
{paper_data.get('Sec02_Motivation', '')}

#### 03. 核心实验设计
{paper_data.get('Sec03_Methods', '')}

---
### 📈 核心图表逐一深度拆解
*(高清原图及拆解均已成功传输至 Notion)*

{fig_md}
---

#### 04. 局限性与缺陷分析
{paper_data.get('Sec04_Limitations', '')}

#### 05. 课题组启发与借鉴思路
{paper_data.get('Sec05_Ideas', '')}

*—— 🎉 本内容已永久归档至你的 Notion 知识库！*
        """
        
        yield "✅ 极其完美！图注、解析连带高清原图，已全部硬核上传并完美推送到 Notion 笔记里！", preview_md
    except Exception as e:
        progress(1.0, desc=f"❌ 哎呀，翻车了：{str(e)}")
        # 即使 Notion 推送失败，也要在页面上显示已经提取成功的图集！
        try:
            yield f"❌ 同步失败，错误信息: {str(e)}", preview_md if 'preview_md' in locals() else "*解析错误*"
        except:
            yield f"❌ 处理失败，错误信息: {str(e)}", "*等待上传文献...*"

# --- UI 界面搭建与可爱风 CSS 注入 ---
custom_css = """
/* 进度条外层容器美化 */
.progress-bar {
    border-radius: 20px !important;
    background-color: #f8fafc !important; /* 浅白偏蓝底轨 */
    border: 1px solid #e2e8f0 !important;
}

/* 进度条填充与渐变光泽 */
.progress-level, .wrap > div > div[class*="bg-"] {
    position: relative;
    border-radius: 20px !important;
    background: linear-gradient(90deg, #e0f2fe 0%, #7dd3fc 100%) !important;
    box-shadow: 0 4px 10px rgba(125, 211, 252, 0.3);
    transition: width 0.3s ease-in-out !important;
}

/* 🐾 可爱移动光标：绑定在进度条右侧伪元素 */
.progress-level::after, .wrap > div > div[class*="bg-"]::after {
    content: "🐱"; /* 保留小猫咪 */
    font-size: 28px;
    position: absolute;
    right: -14px;
    top: -12px;
    z-index: 100;
    /* 加入浮动动画 */
    animation: bounceFly 1.2s infinite alternate cubic-bezier(0.45, 0.05, 0.55, 0.95);
    filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1));
}

@keyframes bounceFly {
    0% { transform: translateY(0px) rotate(-5deg) scale(0.95); }
    100% { transform: translateY(-5px) rotate(5deg) scale(1.05); }
}

/* 进度文字颜色 */
.progress-text {
    font-family: 'Inter', 'Nunito', sans-serif !important;
    font-weight: 600 !important;
    color: #0284c7 !important;
    text-shadow: 1px 1px 2px #f0f9ff;
}
"""

custom_theme = gr.themes.Soft(
    primary_hue="sky",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "system-ui", "sans-serif"]
)

custom_head = """
<meta name="google" content="notranslate">
<style>
    /* 强行隐藏任何可能出现的谷歌翻译工具条 */
    .goog-te-banner-frame { display: none !important; }
    body { top: 0px !important; }
</style>
<script>
    // 强制设置页面语言，尝试让组件优先渲染中文
    document.documentElement.lang = 'zh-CN';
    Object.defineProperty(navigator, 'language', { value: 'zh-CN', configurable: true });
    Object.defineProperty(navigator, 'languages', { value: ['zh-CN', 'zh'], configurable: true });
</script>
"""

with gr.Blocks(title="文献图表级精读归档系统", theme=custom_theme, css=custom_css, head=custom_head) as demo:
    gr.HTML(f"""
    <div style="text-align: center; max-width: 800px; margin: 0 auto; padding-top: 20px; padding-bottom: 20px;">
        <h1 style="font-weight: 800; font-size: 2em; margin-bottom: 8px;">📚 智能文献(图表级)精读与归档系统</h1>
        <p style="font-size: 16px; color: #666; margin-bottom: 15px;">集成 AI 深度拆解 与 PyMuPDF 智能包围盒截屏引擎，全自动 Notion 连图同步</p>
        <a href="https://notion.so/{config.NOTION_DATABASE_ID.replace('-', '')}" target="_blank" style="display: inline-block; padding: 8px 16px; background-color: #f0f9ff; color: #0284c7; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 14px; border: 1px solid #bae6fd; transition: all 0.2s;">
            👉 点击此处，直达课题组云端知识库
        </a>
    </div>
    """)
    
    with gr.Column():
        with gr.Row():
            with gr.Column(scale=1):
                import datetime
                with gr.Row():
                    reporter = gr.Textbox(label="汇报人姓名", placeholder="填写姓名", scale=1)
                    report_date = gr.DateTime(label="汇报时间", include_time=False, type="string", value=datetime.date.today().strftime("%Y-%m-%d"), scale=1)
                pdf_file = gr.File(label="拖拽上传文献 PDF", file_types=[".pdf"])
                with gr.Row():
                    submit_btn = gr.Button("✨ 启动深度拆解并向 Notion 自动推图", variant="primary", scale=2, size="lg")
                    clear_btn = gr.Button("🧹 清空准备下一篇", variant="secondary", scale=1, size="lg")
            with gr.Column(scale=1):
                status_box = gr.Textbox(label="运行状态日志", lines=5)
                
        gr.HTML("<h3 style='margin-top:20px'>📖 沉浸式图表精读 (图文并茂模式)</h3>")
        preview_box = gr.Markdown(label="解析结果实时预览大屏", value="*等待上传文献...*")
            
    gr.HTML("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; border-top: 1px solid #e2e8f0;">
        <p style="font-size: 14px; color: #94a3b8;">
            Designed & Developed by <strong>Liu</strong> | 🚀 Powered by DeepSeek & PyMuPDF
        </p>
    </div>
    """)
    
    submit_btn.click(fn=process_upload, inputs=[pdf_file, reporter, report_date], outputs=[status_box, preview_box])
    
    def clear_all():
        import datetime
        return None, "", datetime.date.today().strftime("%Y-%m-%d"), "", "*等待上传文献...*"
    clear_btn.click(fn=clear_all, inputs=[], outputs=[pdf_file, reporter, report_date, status_box, preview_box])

if __name__ == "__main__":
    app, local_url, share_url = demo.launch(
        share=True, 
        prevent_thread_lock=True,
        allowed_paths=[os.path.abspath("extracted_figs")]
    )
    with open("public_url.txt", "w", encoding="utf-8") as f:
        f.write(str(share_url))
    
    import time
    while True:
        time.sleep(1)
