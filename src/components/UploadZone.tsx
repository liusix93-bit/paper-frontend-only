import React, { useState, useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const ChatBox = ({ filename, onClose }: { filename: string, onClose: () => void }) => {
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const newMsgs = [...messages, { role: 'user', content: input }];
    setMessages(newMsgs);
    setInput('');
    setLoading(true);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/papers/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, messages: newMsgs })
      });
      const data = await res.json();
      if (data.status === "success") {
        setMessages([...newMsgs, { role: 'assistant', content: data.reply }]);
      } else {
        alert("Chat Error: " + data.message);
      }
    } catch (e) {
      console.error(e);
      alert("Network Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', bottom: '24px', right: '24px', width: '400px', background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(10px)', borderRadius: '16px', boxShadow: '0 10px 40px rgba(0,0,0,0.15)', border: '1px solid var(--border-color)', zIndex: 9999, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px 20px', background: 'var(--accent-color)', color: 'white' }}>
        <div>
          <div style={{ fontWeight: 600, fontSize: '15px' }}>💬 Chat with Paper</div>
          <div style={{ fontSize: '11px', opacity: 0.8, marginTop: '2px', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', maxWidth: '300px' }}>{filename}</div>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'white', fontSize: '20px', cursor: 'pointer', opacity: 0.8 }}>&times;</button>
      </div>
      
      <div style={{ height: '400px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '12px', padding: '20px', background: 'rgba(0,0,0,0.01)' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', background: msg.role === 'user' ? 'var(--accent-color)' : '#fff', color: msg.role === 'user' ? '#fff' : '#333', padding: '12px 16px', borderRadius: '12px', maxWidth: '85%', boxShadow: '0 2px 8px rgba(0,0,0,0.06)', border: msg.role === 'assistant' ? '1px solid var(--border-color)' : 'none' }}>
            <p style={{ margin: 0, fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.content}</p>
          </div>
        ))}
        {loading && <div style={{ fontSize: '13px', color: '#666', padding: '8px' }}>🤖 AI is thinking...</div>}
        {messages.length === 0 && <div style={{ fontSize: '14px', color: '#999', textAlign: 'center', margin: '30px 0' }}>有什么关于这篇文献的问题？直接问我吧！我会基于全文寻找答案。</div>}
        <div ref={chatEndRef} />
      </div>
      <div style={{ display: 'flex', gap: '12px', padding: '16px', borderTop: '1px solid var(--border-color)', background: '#fff' }}>
        <input type="text" className="input-field" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} placeholder="Ask anything about this paper..." style={{ flex: 1, margin: 0 }} />
        <button className="btn btn-primary" onClick={sendMessage} disabled={loading} style={{ padding: '0 20px', borderRadius: '8px', fontWeight: 600 }}>Send</button>
      </div>
    </div>
  );
};

const UploadZone = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [pushedIndexes, setPushedIndexes] = useState<Set<number>>(new Set());
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);
  const [activeChatFilename, setActiveChatFilename] = useState<string | null>(null);
  const reportRef = useRef<HTMLDivElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
      setFiles(prev => [...prev, ...newFiles]);
    }
  };

  const [reporter, setReporter] = useState('');
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [channel, setChannel] = useState('group');

  const startAnalysis = async () => {
    if (files.length === 0) return;
    if (!reporter.trim()) {
      alert("⚠️ 请先填写汇报人姓名再进行扫描！");
      return;
    }
    
    setIsAnalyzing(true);
    
    const currentResults = [...results];
    
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("reporter", reporter);
      formData.append("report_date", reportDate);
      formData.append("database_id", channel);
      
      try {
        const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/papers/analyze`, {
          method: "POST",
          body: formData
        });
        const data = await response.json();
        
        if (data.status === "success") {
          currentResults.push({ ...data.data, _filename: file.name });
          setResults([...currentResults]);
        } else {
          alert(`分析 ${file.name} 失败: ${data.message}`);
        }
      } catch (error) {
        console.error("Analysis failed", error);
        alert(`分析 ${file.name} 失败，网络错误！`);
      }
    }
    
    setFiles([]); // 清空上传队列
    setIsAnalyzing(false);
    
    setTimeout(() => {
      reportRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 500);
  };

  const pushToNotion = async (res: any, index: number) => {
    try {
      const payload = {
        ...res,
        reporter: reporter,
        report_date: reportDate,
        database_id: channel
      };
      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/papers/push_to_notion`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (data.status === "success") {
        alert("🎉 成功同步至 Notion！");
        setPushedIndexes(prev => new Set(prev).add(index));
      } else {
        alert("同步失败: " + JSON.stringify(data));
      }
    } catch (e) {
      alert("网络错误: " + String(e));
    }
  };

  useEffect(() => {
    mermaid.initialize({ startOnLoad: false, theme: 'default' });
    results.forEach((res, index) => {
      if (res.Mermaid_Flowchart) {
        try {
          mermaid.render(`mermaid-svg-${index}`, res.Mermaid_Flowchart).then((m) => {
            const el = document.getElementById(`mermaid-container-${index}`);
            if (el) el.innerHTML = m.svg;
          });
        } catch (e) {
          console.error("Mermaid error:", e);
        }
      }
    });
  }, [results]);

  return (
    <div style={{ width: '100%', paddingBottom: '100px' }}>
      {zoomedImage && (
        <div 
          style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(0,0,0,0.85)', zIndex: 9999, display: 'flex', justifyContent: 'center', alignItems: 'center', cursor: 'zoom-out', backdropFilter: 'blur(4px)' }} 
          onClick={() => setZoomedImage(null)}
        >
          <img src={zoomedImage} style={{ maxWidth: '90vw', maxHeight: '90vh', objectFit: 'contain', borderRadius: '8px', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' }} />
        </div>
      )}

      {/* Hero 区 */}
      <div className="upload-container" style={{ display: 'flex', width: '100%', gap: '80px', alignItems: 'center', minHeight: '80vh' }}>
        <style>{`
          .scanner-container {
            position: relative;
            width: 70px;
            height: 90px;
            margin: 0 auto 24px auto;
          }
          .pdf-doc {
            position: absolute;
            inset: 0;
            border: 3px solid var(--accent-color);
            border-radius: 8px;
            background: rgba(255,255,255,0.9);
            overflow: hidden;
            box-shadow: var(--shadow-md);
          }
          .pdf-doc::before {
            content: 'PDF';
            position: absolute;
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            font-weight: 800;
            color: rgba(0, 0, 0, 0.1);
            font-size: 24px;
          }
          .laser-line {
            position: absolute;
            left: -10px;
            right: -10px;
            height: 1px;
            background: var(--accent-color);
            box-shadow: 0 0 10px 2px var(--accent-color);
            animation: scan 2.5s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
            z-index: 10;
          }
          @keyframes scan {
            0% { top: 0%; opacity: 0; }
            15% { opacity: 1; }
            85% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
          }
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}</style>

        <div style={{ flex: 1, paddingBottom: '40px' }}>
          <h1 style={{ fontSize: '72px', lineHeight: 1.1, fontWeight: 800, letterSpacing: '-2.5px', marginBottom: '32px', color: 'var(--text-primary)' }}>
            Deep read <br />
            <span style={{ position: 'relative', display: 'inline-block' }}>
              <span style={{ position: 'relative', zIndex: 1 }}>with all your</span>
              <span style={{ position: 'absolute', bottom: '10px', left: '-8px', right: '-12px', height: '24px', background: 'var(--highlight-color)', zIndex: 0, borderRadius: '2px', opacity: 0.8 }}></span>
            </span><br />
            academic needs.
          </h1>
          <p style={{ fontSize: '18px', color: 'var(--text-secondary)', marginBottom: '40px', maxWidth: '480px', lineHeight: 1.6, fontWeight: 500 }}>
            Batch upload your PDFs, extract the core mechanisms, chat with papers, and sync to Notion instantly. No fees. No hassle. No stress.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
            <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '2px', fontWeight: 700, color: 'var(--text-secondary)' }}>
              BATCH PROCESSING ENABLED • SELECT MULTIPLE FILES ON THE RIGHT
            </span>
          </div>
        </div>

        <div style={{ flex: 1, position: 'relative', height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="glass-panel" style={{ position: 'absolute', top: '50%', left: '50%', width: '380px', height: '240px', transform: 'translate(-30%, -70%) rotate(12deg)', opacity: 0.4, zIndex: 0 }}></div>
          <div className="glass-panel" style={{ position: 'relative', zIndex: 1, width: '420px', padding: '40px', display: 'flex', flexDirection: 'column', gap: '24px', transform: 'translate(-10%, 10%)', background: 'rgba(255,255,255,0.7)', boxShadow: '0 20px 50px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
              <div>
                <label className="input-label">Archive Channel</label>
                <select className="input-field" value={channel} onChange={(e) => setChannel(e.target.value)}>
                  <option value="group">Team Database (Public)</option>
                  <option value="private">Personal Workspace</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label className="input-label">Reporter <span style={{color:'var(--danger-color)'}}>*</span></label>
                  <input type="text" className="input-field" placeholder="E.g. John Doe" value={reporter} onChange={(e) => setReporter(e.target.value)} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="input-label">Date</label>
                  <input type="date" className="input-field" value={reportDate} onChange={(e) => setReportDate(e.target.value)} />
                </div>
              </div>
            </div>

            <div 
              className={`dropzone ${isDragging ? 'active' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-upload')?.click()}
              style={{
                 border: `2px dashed ${isDragging ? 'var(--accent-color)' : 'rgba(0,0,0,0.1)'}`,
                 borderRadius: '16px', padding: '40px 20px', textAlign: 'center',
                 background: isDragging ? 'rgba(123,115,212,0.05)' : 'rgba(255,255,255,0.5)',
                 cursor: 'pointer', transition: 'all 0.3s',
                 height: '160px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'
              }}
            >
              <div className="scanner-container" style={{ transform: 'scale(0.8)', margin: '0 0 16px 0', filter: isAnalyzing ? 'brightness(1.5)' : 'none' }}>
                <div className="pdf-doc"></div>
                {(files.length === 0 || isAnalyzing) && <div className="laser-line" style={{ animationDuration: isAnalyzing ? '0.8s' : '2.5s' }}></div>}
              </div>
              
              <h3 style={{ fontSize: '15px', color: 'var(--text-primary)', margin: 0, fontWeight: 600 }}>
                {isAnalyzing ? "Analyzing via DeepSeek..." : (files.length > 0 ? `Ready: ${files.length} file(s)` : 'Drop PDFs here or click')}
              </h3>
              {files.length > 0 && !isAnalyzing && (
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '8px' }}>
                  {files.map(f => f.name).join(', ').slice(0, 30) + (files.map(f => f.name).join(', ').length > 30 ? '...' : '')}
                </div>
              )}
              <input type="file" id="file-upload" accept=".pdf" multiple style={{ display: 'none' }} onChange={(e) => {
                if (e.target.files && e.target.files.length > 0) {
                  const newFiles = Array.from(e.target.files).filter(f => f.type === 'application/pdf');
                  setFiles(prev => [...prev, ...newFiles]);
                }
              }} />
            </div>

            {files.length > 0 && !isAnalyzing && (
              <button 
                className={reporter.trim() ? "btn btn-primary" : "btn"} 
                onClick={(e) => { e.stopPropagation(); startAnalysis(); }}
                style={{ width: '100%', padding: '16px', fontSize: '14px', borderRadius: '8px', fontWeight: 600, opacity: reporter.trim() ? 1 : 0.5, cursor: reporter.trim() ? 'pointer' : 'not-allowed', background: 'var(--text-primary)', color: 'white', textTransform: 'uppercase', letterSpacing: '1px', border: 'none' }}
              >
                {reporter.trim() ? `Start Batch Scan (${files.length})` : "Enter Reporter Name"}
              </button>
            )}
            
            {files.length > 0 && !isAnalyzing && (
              <button onClick={(e) => { e.stopPropagation(); setFiles([]); }} style={{ background: 'transparent', border: 'none', color: 'var(--danger-color)', fontSize: '12px', cursor: 'pointer', marginTop: '-12px' }}>
                Clear Queue
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 第二屏：解析结果 */}
      <div ref={reportRef} style={{ display: 'flex', flexDirection: 'column', gap: '80px', marginTop: '40px' }}>
        {results.map((res, index) => {
          const isPushed = pushedIndexes.has(index);
          return (
            <div key={index} className="report-container" style={{ animation: 'fadeIn 0.5s ease', paddingTop: '40px', borderTop: '2px dashed var(--border-color)', width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <h2 style={{ fontSize: '28px', color: 'var(--text-primary)', letterSpacing: '-0.5px', margin: 0 }}>{res.Title_ZH || res.Title_EN || res._filename}</h2>
                <div style={{ fontSize: '13px', background: 'var(--highlight-color)', padding: '4px 12px', borderRadius: '20px', fontWeight: 600, color: 'var(--accent-color)' }}>
                  📄 {res._filename}
                </div>
              </div>
              <p style={{ color: 'var(--text-secondary)', fontFamily: 'monospace', marginBottom: '32px' }}>{res.Journal || '未知期刊'} | IF: {res.IF || '未知'} | {res.PubDate || '未知'} | 汇报人: {reporter}</p>
              
              <div style={{ display: 'flex', gap: '16px', marginBottom: '32px' }}>
                <button className="btn btn-primary" style={{ flex: 1, padding: '16px', fontWeight: 600, opacity: isPushed ? 0.6 : 1, cursor: isPushed ? 'not-allowed' : 'pointer' }} 
                  onClick={() => !isPushed && pushToNotion(res, index)} 
                  disabled={isPushed}>
                  {isPushed ? "✅ 已成功同步至 Notion" : "📤 确认无误，同步至 Notion"}
                </button>
              </div>

              <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>核心总结</h3>
                <p style={{ lineHeight: 1.8 }}>{res.Sec01_Summary}</p>
              </div>

              <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>🔬 1. 研究背景与临床痛点</h3>
                <p style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{res.Sec02_Motivation}</p>
              </div>

              <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>🧪 2. 核心方法与数据集</h3>
                <p style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}>{res.Sec03_Methods}</p>
              </div>

              <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>📌 核心机制流程图 (Mermaid)</h3>
                {res.Mermaid_Flowchart && (
                  <div style={{ textAlign: 'center', margin: '20px 0', overflowX: 'auto', background: 'white', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div id={`mermaid-container-${index}`}></div>
                  </div>
                )}
                <details>
                  <summary style={{ cursor: 'pointer', color: '#666', fontSize: '13px', marginBottom: '10px' }}>查看原生 Mermaid 代码</summary>
                  <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '8px', fontSize: '12px', whiteSpace: 'pre-wrap', color: '#666' }}>{res.Mermaid_Flowchart}</pre>
                </details>
              </div>

              {Array.isArray(res.Figure_Analysis) && res.Figure_Analysis.length > 0 && (
                <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
                  <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>📊 3. 核心图表与数据结论</h3>
                  <div style={{ display: 'grid', gap: '24px' }}>
                    {res.Figure_Analysis.map((fig: any, idx: number) => {
                      const figName = typeof fig === 'string' ? fig : (fig?.Figure_Name || "");
                      const matchedFig = Array.isArray(res.extracted_figs) && figName
                        ? res.extracted_figs.find((ef: any) => 
                            ef?.name?.toLowerCase() === figName.toLowerCase() || 
                            ef?.label?.toLowerCase() === figName.toLowerCase()
                          )
                        : null;
                      
                      return (
                        <div key={idx} style={{ background: 'rgba(0,0,0,0.02)', padding: '20px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
                          <h4 style={{ color: 'var(--accent-color)', marginBottom: '12px', fontSize: '16px' }}>{figName || "未命名图表"}</h4>
                          
                          {matchedFig ? (
                            <div style={{ marginBottom: '16px', textAlign: 'center', background: '#f8f9fa', padding: '16px', borderRadius: '8px' }}>
                              <img 
                                src={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/${matchedFig.path}`} 
                                alt={figName} 
                                onClick={() => setZoomedImage(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/${matchedFig.path}`)}
                                style={{ maxWidth: '100%', maxHeight: '400px', objectFit: 'contain', borderRadius: '4px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', cursor: 'zoom-in' }} 
                              />
                              {matchedFig.caption && <p style={{ fontSize: '13px', color: '#666', marginTop: '12px', fontStyle: 'italic', textAlign: 'left' }}>📄 <b>原文图注：</b> {matchedFig.caption}</p>}
                            </div>
                          ) : (
                            <div style={{ marginBottom: '16px', background: '#fff3cd', color: '#856404', padding: '12px', borderRadius: '6px', fontSize: '13px' }}>
                              ⚠️ 无法在此页精确定位该图表的图像块，可能是矢量图或超出了页面提取范围。
                            </div>
                          )}

                          <div style={{ lineHeight: 1.6, fontSize: '14px', marginTop: '16px' }}>
                            <div style={{ marginBottom: '8px' }}><strong>🎯 核心结论：</strong>{typeof fig === 'string' ? fig : (fig?.Core_Conclusion || "无")}</div>
                            <div><strong>🔑 关键细节：</strong>{typeof fig === 'string' ? "" : (fig?.Key_Details || "无")}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="glass-panel" style={{ padding: '32px', marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>💡 4. 局限性与研究启示</h3>
                <p style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap' }}><strong>局限性：</strong><br/>{res.Sec04_Limitations}</p>
                <p style={{ lineHeight: 1.8, whiteSpace: 'pre-wrap', marginTop: '12px' }}><strong>启示：</strong><br/>{res.Sec05_Ideas}</p>
              </div>

              {/* Chat with Paper Trigger */}
              <div style={{ padding: '0 0 24px 0' }}>
                <button 
                  className="btn btn-primary" 
                  onClick={() => setActiveChatFilename(res._filename)}
                  style={{ padding: '12px 24px', borderRadius: '30px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px', background: 'var(--accent-color)', color: 'white', border: 'none', cursor: 'pointer', boxShadow: '0 4px 15px rgba(123, 115, 212, 0.3)' }}
                >
                  💬 AI 深度追问这篇文献
                </button>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* Floating Chat Box */}
      {activeChatFilename && (
        <ChatBox filename={activeChatFilename} onClose={() => setActiveChatFilename(null)} />
      )}
    </div>
  );
};

export default UploadZone;
