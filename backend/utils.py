import os
import fitz
import re
import json
import requests
import urllib.parse
from openai import OpenAI
import config

client = OpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

def search_crossref(title: str):
    try:
        url = "https://api.crossref.org/works?query.title=" + urllib.parse.quote(title) + "&select=DOI,title,container-title,published,published-print,published-online&rows=1"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            items = data.get("message", {}).get("items", [])
            if items:
                item = items[0]
                doi = item.get("DOI", "未知")
                journal = "未知"
                if "container-title" in item and item["container-title"]:
                    journal = item["container-title"][0]
                
                pub_date = "未知"
                pub_info = item.get("published") or item.get("published-print") or item.get("published-online")
                if pub_info and "date-parts" in pub_info:
                    parts = pub_info["date-parts"][0]
                    if len(parts) >= 3:
                        pub_date = f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
                    elif len(parts) == 2:
                        pub_date = f"{parts[0]}-{parts[1]:02d}-01"
                    elif len(parts) == 1:
                        pub_date = f"{parts[0]}-01-01"
                return {"DOI": doi, "Journal": journal, "PubDate": pub_date}
    except Exception as e:
        print("Crossref API Error:", e)
    return None

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
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
        "Title_EN": "论文英文原标题",
        "Title_ZH": "论文精美的中文翻译标题",
        "DOI": "文献的DOI或网页链接 (例如 https://doi.org/10.1038/s41586... 若无则填未知)",
        "PubDate": "论文发表日期 (格式 YYYY-MM-DD, 若不知则填当前日期)",
        "Journal": "期刊名称 (如果在文中找不到，请凭借知识库推测，若不知则填未知)",
        "JCR": "JCR分区 (如 Q1, 请务必根据知识库估算，不要填 未知)",
        "CAS": "中科院分区 (如 1区, 请务必根据知识库估算，不要填 未知)",
        "IF": "影响因子 (如 15.3, 请务必根据知识库给出最新估算值，不要填 未知)",
        "Tags": ["标签1", "标签2"],
        "Mermaid_Flowchart": "用 mermaid 语法写一段流程图总结整篇文章的核心逻辑。注意：流程图里的【节点内容文本】必须翻译成中文！为了防止语法报错，【节点文本必须用双引号严格包裹】，例如 A[\"组别(包含括号等特殊符号)\"]。mermaid代码中的【语法关键字】必须是纯英文。直接写代码，不要用 markdown包裹",
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
    match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if match:
        json_str = match.group(0)
    else:
        json_str = raw_response
        
    return json.loads(json_str)

def extract_figures_smart(pdf_path, fig_names_to_find):
    output_dir = "extracted_figs"
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    extracted = []
    
    for fig_name in fig_names_to_find:
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
                pattern = r'^(?:Figure|Fig\.?|FIG\.?|图)\s*' + re.escape(fig_num) + r'(?:[^a-zA-Z0-9]|$)'
                if re.match(pattern, text, re.IGNORECASE):
                    found_rect = fitz.Rect(b[:4])
                    matched_caption = text.replace("\n", " ")
                    break
            
            if found_rect:
                try:
                    img_bboxes = [fitz.Rect(img["bbox"]) for img in page.get_image_info()]
                except:
                    img_bboxes = []
                
                target_bboxes = [r for r in img_bboxes if r.height > 50 and r.y0 < found_rect.y1 + 50]
                
                if target_bboxes:
                    closest_dist = min(abs(found_rect.y0 - r.y1) for r in target_bboxes)
                    target_bboxes = [r for r in target_bboxes if abs(found_rect.y0 - r.y1) <= closest_dist + 400]
                    
                    min_x = min(r.x0 for r in target_bboxes)
                    min_y = min(r.y0 for r in target_bboxes)
                    max_x = max(r.x1 for r in target_bboxes)
                    max_y = max(r.y1 for r in target_bboxes)
                    
                    if found_rect.y0 >= min_y:
                        max_y = min(max_y, found_rect.y0 - 2)
                    else:
                        min_y = max(min_y, found_rect.y1 + 2)
                        
                    clip_rect = fitz.Rect(max(0, min_x-2), max(0, min_y-2), min(page.rect.width, max_x+2), min(page.rect.height, max_y+2))
                else:
                    top_y = max(0, found_rect.y0 - 450)
                    clip_rect = fitz.Rect(0, top_y, page.rect.width, max(0, found_rect.y0 - 2))
                
                pix = page.get_pixmap(clip=clip_rect, dpi=200)
                if pix.n - pix.alpha >= 4:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                
                safe_name = fig_name.replace(" ", "_").replace(".", "").replace(":", "")
                import uuid
                unique_id = uuid.uuid4().hex[:8]
                img_path = os.path.join(output_dir, f"{safe_name}_{page_num}_{unique_id}.png")
                try:
                    pix.save(img_path)
                except Exception as e:
                    print(f"Warning: Failed to save image {img_path}: {e}")
                pix = None
                
                extracted.append({
                    "name": fig_name, 
                    "caption": matched_caption,
                    "path": img_path
                })
                break 
                
    return extracted

def upload_image_for_notion(file_path):
    try:
        url = "https://freeimage.host/api/1/upload"
        data = {"key": "6d207e02198a847aa98d0a2a901485a5"}
        with open(file_path, "rb") as f:
            files = {"source": f}
            response = requests.post(url, data=data, files=files)
            if response.status_code == 200:
                result = response.json()
                if "image" in result and "url" in result["image"]:
                    return result["image"]["url"]
    except Exception as e:
        print("Image upload failed:", e)
    return None
