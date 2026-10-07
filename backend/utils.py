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
        "Sec02_Summary": "02 一句话总结 (What problem, what approach, what result)",
        "Sec03_Question": "03 研究问题 (Research Question: problem, why it matters, why existing fail)",
        "Sec04_Background": "04 研究背景与发展路径 (Background & Development Path)",
        "Sec05_PainPoints": "05 核心痛点 (Core Pain Points Identified by the Paper)",
        "Sec06_Idea": "06 核心思想 (Core Idea: surface method, core insight)",
        "Sec07_Method": "07 方法概览 (Method Overview)",
        "Sec08_Modules": "08 核心模块拆解 (Core Module Breakdown)",
        "Sec09_Formulas": "09 核心公式与符号 (Essential Formulas and Symbols)",
        "Mermaid_Flowchart": "用 mermaid 语法写一段流程图总结整篇文章的核心逻辑。注意：流程图里的【节点内容文本】必须翻译成中文！【节点文本必须用双引号严格包裹】，例如 A[\"组别\"]。",
        "Figure_Analysis": [
            {
                "Figure_Name": "原文图表编号 (必须精确提取原文的编号，如 Figure 1, Fig. 2a。严禁使用『图示』、『表格』等泛指词)",
                "Core_Conclusion": "这张图证明了什么核心结论？",
                "Key_Details": "用了什么关键实验手段/对比，看到了什么关键差异？"
            }
        ],
        "Sec11_Interpretation": "11 结论的正确解读边界 (Correct Interpretation of the Conclusions)",
        "Sec12_Limitations": "12 作者承认的局限性 (Limitations Explicitly Acknowledged)",
        "Sec13_CriticalAnalysis": "13 批判性分析 (Critical Analysis: flaws, alternatives)",
        "Sec14_Knowledge": "14 学到的知识 (Knowledge Learned: transferable concepts)",
        "Sec15_Connections": "15 与已有知识的联系 (Connections to Existing Knowledge)",
        "Sec16_Ideas": "16 研究启发 (Research Ideas: hypothesis, methods)"
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
        
    try:
        data = json.loads(json_str)
        if "Mermaid_Flowchart" in data:
            chart = str(data["Mermaid_Flowchart"]).strip()
            if not chart.startswith(("graph", "flowchart")):
                data["Mermaid_Flowchart"] = ""
        return data
    except Exception as e:
        print("JSON parse error:", e)
        return {"Title_ZH": "解析失败", "Sec01_Summary": "模型返回的格式错误。"}

def generate_skill_with_kimi(text, filename):
    prompt = f"""
    你是一个高级 AI Agent。请你基于以下论文的全文内容，提取一个专业的 Agent Skill。
    这篇论文的文件名是: {filename}
    
    你需要输出的内容格式必须是一个 Markdown 字符串，符合以下格式（必须包含 YAML frontmatter）：
    ---
    name: skill-[简短的主题名称，只能使用小写字母和连字符，且不超过63个字符]
    description: 扮演这篇论文研究领域的专家，基于论文提供的信息回答用户问题。
    ---
    # 角色与背景
    你是一个精通该论文及其研究领域的专家。
    【在这里用一段话详细总结这篇论文的核心内容、方法和主要结论】
    
    # 执行指令
    1. 始终基于这篇论文的方法论和结论回答问题。
    2. [提取并总结论文中的其他 2-3 个核心工作流或专业技能，作为具体指令列出]
    
    # 核心知识库
    【在这里列出这篇论文中最重要的几个专业术语、机制、数据或核心结论，作为参考信息】
    
    请直接输出 Markdown 内容，不要用 ```markdown 包裹，直接输出纯文本内容即可。
    
    论文内容截取如下：
    {text}
    """
    
    completion = client.chat.completions.create(
      model="deepseek-chat",
      messages=[
        {"role": "user", "content": prompt}
      ]
    )
    
    res = completion.choices[0].message.content.strip()
    if res.startswith("```markdown"):
        res = res[len("```markdown"):].strip()
    if res.startswith("```"):
        res = res[3:].strip()
    if res.endswith("```"):
        res = res[:-3].strip()
    return res

def _is_body_text(text, width, col_w, r=None, graphics=None):
    if r and graphics and any(r.intersects(g) for g in graphics):
        return False
    n = len(text)
    return n >= 50 or (n >= 30 and width >= 0.5 * col_w)

def _trim_whitespace(page, rect, dpi=72, thresh=235):
    pix = page.get_pixmap(clip=rect, dpi=dpi, colorspace=fitz.csGRAY, alpha=False)
    w, h, st, s = pix.width, pix.height, pix.stride, pix.samples
    if w == 0 or h == 0:
        return rect
    rows = [y for y in range(h) if min(s[y * st: y * st + w]) < thresh]
    cols = [x for x in range(w) if min(s[x: h * st: st]) < thresh]
    if not rows or not cols:
        return rect
    sx, sy = rect.width / w, rect.height / h
    return fitz.Rect(rect.x0 + cols[0] * sx - 3, rect.y0 + rows[0] * sy - 3,
                     rect.x0 + (cols[-1] + 1) * sx + 3, rect.y0 + (rows[-1] + 1) * sy + 3) & rect

def _locate_figure(page, cap):
    W, H = page.rect.width, page.rect.height
    mid = W / 2
    if cap.width > 0.6 * W:
        cx0, cx1 = 0, W
    elif (cap.x0 + cap.x1) / 2 < mid:
        cx0, cx1 = 0, mid
    else:
        cx0, cx1 = mid, W
    col_w = cx1 - cx0

    graphics = []
    try:
        for img in page.get_image_info():
            r = fitz.Rect(img["bbox"])
            if r.get_area() < 0.6 * page.rect.get_area():
                if r.y0 > H * 0.05 and r.y1 < H * 0.95:
                    graphics.append(r)
    except Exception:
        pass
    try:
        for d in page.get_drawings():
            r = d["rect"]
            # 排除长条形的页眉页脚线
            if (r.width > 3 or r.height > 3) and r.width < W * 0.9 and r.height < H * 0.9:
                if r.y0 > H * 0.05 and r.y1 < H * 0.95:
                    graphics.append(r)
    except Exception:
        pass

    bounds = []
    for b in page.get_text("blocks"):
        if b[6] != 0:
            continue
        r = fitz.Rect(b[:4])
        if r == cap or r.x1 <= cx0 + 5 or r.x0 >= cx1 - 5:
            continue
        text = b[4].strip()
        if _is_body_text(text, r.width, col_w, r, graphics) or r.y1 < H * 0.07 or r.y0 > H * 0.94:
            bounds.append(r)

    top = max([r.y1 for r in bounds if r.y1 <= cap.y0 + 1] + [H * 0.04])
    bottom = min([r.y0 for r in bounds if r.y0 >= cap.y1 - 1] + [H * 0.96])
    above = fitz.Rect(cx0, top + 1, cx1, cap.y0 - 1)
    below = fitz.Rect(cx0, cap.y1 + 1, cx1, bottom - 1)

    def score(region):
        if region.is_empty or region.height < 30:
            return -1
        return sum((g & region).get_area() for g in graphics if g.intersects(region))

    sa, sb = score(above), score(below)
    if sa <= 0 and sb <= 0:  
        region, sc = (above, 0) if above.height >= 60 else (below, 0)
        if region.height < 60:
            return None, -1
    else:
        region, sc = (above, sa) if (sa > 500 or sb <= 500) else (below, sb)

    inside = [g & region for g in graphics if g.intersects(region)]
    if inside:
        u = fitz.Rect(inside[0])
        for g in inside[1:]:
            u |= g
        region = u
    region = _trim_whitespace(page, region)
    return region, sc


def extract_figures_smart(pdf_path, fig_names_to_find):
    import uuid
    output_dir = "extracted_figs"
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    extracted = []

    for fig_name in fig_names_to_find:
        m = re.search(r'(?:图|Figure|Fig\.?|FIG\.?)\s*([A-Za-z0-9]+(?:[-.][A-Za-z0-9]+)?)', fig_name, re.IGNORECASE)
        if not m:
            continue
        fig_num = re.escape(m.group(1))
        head = r'^(?:Figure|Fig\.?|FIG\.?|图)\s*' + fig_num
        # 严格图注："Fig. 3." / "Figure 3:" / "Fig. 3 Title"；排除正文里的 "Fig. 3 shows ..."
        strict = re.compile(head + r'\s*(?:[.:：|]|\s+[A-Z(\u4e00-\u9fff]|$)', re.IGNORECASE)
        loose = re.compile(head + r'(?:[^a-zA-Z0-9]|$)', re.IGNORECASE)

        candidates = []  # (优先级, 页码, 图注rect, 图注文本)
        for page_num, page in enumerate(doc):
            for b in page.get_text("blocks"):
                text = b[4].strip()
                if strict.match(text):
                    candidates.append((0, page_num, fitz.Rect(b[:4]), text))
                elif loose.match(text):
                    candidates.append((1, page_num, fitz.Rect(b[:4]), text))
        candidates.sort(key=lambda c: c[0])

        best = None  # (得分, 页码, rect, 文本)
        for prio, page_num, cap, text in candidates:
            rect, sc = _locate_figure(doc[page_num], cap)
            if rect is None:
                continue
            if best is None or sc > best[0]:
                best = (sc, page_num, rect, text)
            if sc > 0 and prio == 0:
                break
        if best is None:
            continue

        _, page_num, clip_rect, caption = best
        pix = doc[page_num].get_pixmap(clip=clip_rect, dpi=200)
        if pix.n - pix.alpha >= 4:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        safe_name = fig_name.replace(" ", "_").replace(".", "").replace(":", "")
        img_path = os.path.join(output_dir, f"{safe_name}_{page_num}_{uuid.uuid4().hex[:8]}.png")
        try:
            pix.save(img_path)
        except Exception as e:
            print(f"Warning: Failed to save image {img_path}: {e}")
            continue
        extracted.append({
            "name": fig_name,
            "caption": caption.replace("\n", " "),
            "path": img_path
        })

    return extracted

def upload_image_for_notion(file_path):
    try:
        url = "https://freeimage.host/api/1/upload"
        data = {"key": "6d207e02198a847aa98d0a2a901485a5"}
        with open(file_path, "rb") as f:
            files = {"source": f}
            response = requests.post(url, data=data, files=files, timeout=8)
            if response.status_code == 200:
                result = response.json()
                if "image" in result and "url" in result["image"]:
                    return result["image"]["url"]
    except Exception as e:
        print("Image upload failed, falling back to local URL:", e)
    
    # 终极备用方案：如果免费图床挂了，直接返回你自己后端的公网链接！
    # 只要保证路径中的斜杠是正斜杠
    safe_path = file_path.replace('\\', '/')
    return f"https://paper-frontend-only-2.onrender.com/{safe_path}"
