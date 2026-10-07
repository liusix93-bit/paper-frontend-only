import gradio as gr
import time
import push_paper_full 

def process_upload(file_obj, reporter_name):
    if not file_obj or not reporter_name:
        return "⚠️ 请先上传 PDF 文件并填写汇报人姓名！"
    
    # 模拟大模型处理动画
    yield f"🚀 收到文件！Agent 正在急速通读这篇文献..."
    time.sleep(2)
    yield f"🧠 正在提取核心机制、创新点与方法学细节..."
    time.sleep(2)
    yield f"🎨 正在为你绘制 Mermaid 核心流程图..."
    time.sleep(2)
    yield f"📝 正在排版并连接 Notion 知识库..."
    
    # 调用我们刚才写好并跑通的推送代码
    try:
        push_paper_full.push_full_paper_to_notion()
        yield "✅ 大功告成！文献卡片已成功推送至 Notion，全组可见！\n\n（注：这是前门展示版本，由于尚未配置真实 API，本次测试推送的仍是刚才那篇超酷的心衰文章排版。真正的大模型解析接入只需一行代码的事！）"
    except Exception as e:
        yield f"❌ 推送失败，错误信息: {str(e)}"

# 构建高颜值 UI
with gr.Blocks(title="组会文献知识库 - 自动上传端", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🚀 组会文献全自动归档系统")
    gr.Markdown("请在此处上传本周汇报的文献。系统将自动呼叫后台的超级智能体提取精读卡片，并排版推送至我们组的 Notion 知识库画廊！")
    
    with gr.Row():
        with gr.Column():
            reporter = gr.Textbox(label="汇报人姓名", placeholder="例如：张三")
            pdf_file = gr.File(label="拖拽上传文献 PDF", file_types=[".pdf"])
            submit_btn = gr.Button("🔮 点击召唤 Agent 自动分析并归档", variant="primary")
            
        with gr.Column():
            status_box = gr.Textbox(label="Agent 处理状态监控", lines=10)
            
    # 点击按钮触发流式输出
    submit_btn.click(fn=process_upload, inputs=[pdf_file, reporter], outputs=status_box)

# 开启 share=True 以生成公网链接
if __name__ == "__main__":
    demo.launch(share=True)
