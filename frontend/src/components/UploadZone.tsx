import React, { useState, useEffect, useRef } from 'react';
import mermaid from 'mermaid';

const formatText = (text: string) => {
  if (!text) return "";
  // 仅在明确的分隔符（冒号、分号、句号）或中文字符后的空格处进行换行，避免误伤文献括号内的数字(如 PCSK9, n=507)
  let res = text.replace(/([:：;；])\s*(?=[1-9][0-9]?[.、)）])/g, '$1\n\n');
  res = res.replace(/([.。])\s*(?=[1-9][0-9]?[.、)）])/g, '$1\n\n');
  res = res.replace(/([\u4e00-\u9fa5])\s+(?=[1-9][0-9]?[.、)）])/g, '$1\n\n');
  return res.trim();
};

const Toast = ({ message, type }: { message: string, type: 'info' | 'success' | 'error' }) => {
  if (!message) return null;
  const bg = type === 'error' ? 'rgba(239, 68, 68, 0.95)' : (type === 'success' ? 'rgba(16, 185, 129, 0.95)' : 'rgba(15, 15, 20, 0.95)');
  return (
    <div style={{ position: 'fixed', top: '24px', left: '50%', transform: 'translateX(-50%)', background: bg, color: 'white', padding: '16px 32px', borderRadius: '32px', boxShadow: '0 12px 32px rgba(0,0,0,0.15)', zIndex: 10000, fontWeight: 600, fontSize: '15px', backdropFilter: 'blur(10px)', display: 'flex', alignItems: 'center', gap: '8px', animation: 'fadeInDown 0.3s ease' }}>
      {type === 'info' && <span className="spinner" style={{ display: 'inline-block', width: '16px', height: '16px', border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></span>}
      {message}
      <style>{`
        @keyframes fadeInDown { from { opacity: 0; transform: translate(-50%, -20px); } to { opacity: 1; transform: translate(-50%, 0); } }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

const ChatBox = ({ availableFiles, initialFilename, onClose }: { availableFiles: any[], initialFilename: string, onClose: () => void }) => {
  const [currentFilename, setCurrentFilename] = useState(initialFilename || (availableFiles[0]?._filename || ''));
  const [messages, setMessages] = useState<{role: string, content: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages([]);
  }, [currentFilename]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const sendMessage = async () => {
    if (!input.trim() || loading || !currentFilename) return;
    const newMsgs = [...messages, { role: 'user', content: input }];
    setMessages(newMsgs);
    setInput('');
    setLoading(true);
    
    try {
      const apiUrl = import.meta.env.PROD ? "" : "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/papers/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: currentFilename, messages: newMsgs })
      });
      const data = await res.json();
      if (res.ok && data.status === "success") {
        setMessages([...newMsgs, { role: 'assistant', content: data.reply }]);
      } else {
        const errorMsg = data.detail || data.message || "文件可能已从服务器过期或丢失，请重新上传扫描后再对话。";
        alert("AI 解析报错: " + errorMsg);
      }
    } catch (e) {
      console.error(e);
      alert("Network Error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-box" style={{ position: 'fixed', bottom: '24px', right: '24px', width: '420px', background: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(20px)', borderRadius: '24px', boxShadow: 'var(--shadow-lg)', border: '1px solid var(--border-color)', zIndex: 9999, display: 'flex', flexDirection: 'column', overflow: 'hidden', animation: 'fadeInUp 0.3s ease' }}>
      <style>{`@keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }`}</style>
      <div style={{ display: 'flex', flexDirection: 'column', padding: '16px 20px', background: 'rgba(250, 250, 252, 0.9)', borderBottom: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ fontWeight: 800, fontSize: '16px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
            AI Assistant
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', fontSize: '24px', cursor: 'pointer', lineHeight: 1 }}>&times;</button>
        </div>
        <select 
          className="input-field" 
          value={currentFilename} 
          onChange={e => setCurrentFilename(e.target.value)}
          style={{ padding: '8px 12px', fontSize: '13px', borderRadius: '8px', background: 'white' }}
        >
          {availableFiles.map((f, i) => (
            <option key={i} value={f._filename}>📄 {f._filename}</option>
          ))}
        </select>
      </div>
      
      <div style={{ height: '400px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px', padding: '20px', background: 'rgba(0,0,0,0.01)' }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', background: msg.role === 'user' ? 'var(--text-primary)' : 'white', color: msg.role === 'user' ? 'white' : 'var(--text-primary)', padding: '14px 18px', borderRadius: '16px', borderBottomRightRadius: msg.role === 'user' ? '4px' : '16px', borderBottomLeftRadius: msg.role === 'assistant' ? '4px' : '16px', maxWidth: '85%', boxShadow: 'var(--shadow-sm)', border: msg.role === 'assistant' ? '1px solid var(--border-color)' : 'none' }}>
            <p style={{ margin: 0, fontSize: '14px', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{msg.content}</p>
          </div>
        ))}
        {loading && <div style={{ alignSelf: 'flex-start', background: 'white', padding: '12px 16px', borderRadius: '16px', borderBottomLeftRadius: '4px', boxShadow: 'var(--shadow-sm)', border: '1px solid var(--border-color)' }}><div className="spinner" style={{ width: '16px', height: '16px', border: '2px solid var(--text-secondary)', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div></div>}
        {messages.length === 0 && <div style={{ fontSize: '14px', color: 'var(--text-secondary)', textAlign: 'center', margin: 'auto' }}>上下滑动预览全文，有问题随时在这里问我。我会基于这篇文献进行深度解答！</div>}
        <div ref={chatEndRef} />
      </div>
      <div style={{ display: 'flex', gap: '12px', padding: '16px', borderTop: '1px solid var(--border-color)', background: 'white' }}>
        <input type="text" className="input-field" value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} placeholder="就这篇论文提问..." style={{ flex: 1, margin: 0, borderRadius: '24px', padding: '12px 16px' }} />
        <button className="btn" onClick={sendMessage} disabled={loading} style={{ width: '44px', height: '44px', padding: 0, borderRadius: '50%', display: 'flex', justifyContent: 'center', alignItems: 'center', background: 'var(--text-primary)', color: 'white', border: 'none' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
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
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [initialChatFile, setInitialChatFile] = useState('');
  
  const [isPushing, setIsPushing] = useState(false);
  const [notionSyncTarget, setNotionSyncTarget] = useState<string>("all");
  const reportRef = useRef<HTMLDivElement>(null);
  
  const [toast, setToast] = useState<{msg: string, type: 'info'|'success'|'error'} | null>(null);

  const showToast = (msg: string, type: 'info'|'success'|'error' = 'info', duration: number = 3000) => {
    setToast({ msg, type });
    if (duration > 0) {
      setTimeout(() => setToast(null), duration);
    }
  };

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
      showToast("⚠️ 请先填写汇报人姓名再进行扫描！", "error");
      return;
    }
    
    setIsAnalyzing(true);
    showToast("正在深度解析 PDF，这可能需要几十秒，请稍候...", "info", 0);
    
    const currentResults = [...results];
    
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("reporter", reporter);
      formData.append("report_date", reportDate);
      formData.append("database_id", channel);
      
      try {
        const apiUrl = import.meta.env.PROD ? "" : "http://localhost:8000";
        const response = await fetch(`${apiUrl}/api/papers/analyze`, {
          method: "POST",
          body: formData
        });
        const data = await response.json();
        
        if (data.status === "success") {
          currentResults.push({ ...data.data, _filename: file.name });
          setResults([...currentResults]);
        } else {
          showToast(`分析 ${file.name} 失败: ${data.message}`, "error");
        }
      } catch (error) {
        console.error("Analysis failed", error);
        showToast(`分析 ${file.name} 失败，网络错误！`, "error");
      }
    }
    
    setFiles([]); 
    setIsAnalyzing(false);
    setToast(null);
    
    setTimeout(() => {
      reportRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 500);
  };

  const handlePushTarget = async () => {
    if (isPushing) return;
    setIsPushing(true);
    
    let targetsToPush: any[] = [];
    if (notionSyncTarget === "all") {
      targetsToPush = results.map((res, index) => ({res, index})).filter(x => !pushedIndexes.has(x.index));
    } else {
      const idx = parseInt(notionSyncTarget);
      targetsToPush = [{ res: results[idx], index: idx }];
    }

    if (targetsToPush.length === 0) {
      showToast("没有需要同步的文献！(可能已全部同步)", "info");
      setIsPushing(false);
      return;
    }

    showToast(`正在将 ${targetsToPush.length} 篇文献同步至 Notion，包含图注和原文PDF提取，请耐心等待...`, "info", 0);

    let successCount = 0;
    for (const target of targetsToPush) {
      try {
        const apiUrl = import.meta.env.PROD ? "" : "http://localhost:8000";
        const payload = {
          ...target.res,
          reporter: reporter,
          report_date: reportDate,
          database_id: channel,
          api_url: apiUrl
        };
        const response = await fetch(`${apiUrl}/api/papers/push_to_notion`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (data.status === "success") {
          setPushedIndexes(prev => new Set(prev).add(target.index));
          if (data.url) {
            setResults(prev => {
              const newRes = [...prev];
              newRes[target.index] = { ...newRes[target.index], notion_url: data.url };
              return newRes;
            });
          }
          successCount++;
        } else {
          showToast(`同步 ${target.res._filename} 失败: ` + JSON.stringify(data), "error", 5000);
        }
      } catch (e) {
        showToast(`网络错误同步 ${target.res._filename}: ` + String(e), "error", 5000);
      }
    }
    
    setIsPushing(false);
    if (successCount > 0) {
      showToast(`🎉 成功同步 ${successCount} 篇文献！您可以点击卡片上的"立即前往"查看。`, "success", 6000);
    } else {
      setToast(null);
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

  const openChatForFile = (filename: string) => {
    setInitialChatFile(filename);
    setIsChatOpen(true);
  };

  return (
    <div style={{ width: '100%', paddingBottom: '100px' }}>
      {toast && <Toast message={toast.msg} type={toast.type} />}

      {zoomedImage && (
        <div 
          style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: 'rgba(255,255,255,0.8)', zIndex: 9999, display: 'flex', justifyContent: 'center', alignItems: 'center', cursor: 'zoom-out', backdropFilter: 'blur(12px)' }} 
          onClick={() => setZoomedImage(null)}
        >
          <img src={zoomedImage} style={{ maxWidth: '90vw', maxHeight: '90vh', objectFit: 'contain', borderRadius: '12px', boxShadow: '0 24px 64px rgba(0,0,0,0.12)' }} />
        </div>
      )}

      {/* Global AI Chat FAB */}
      {results.length > 0 && !isChatOpen && (
        <button
          onClick={() => setIsChatOpen(true)}
          style={{
            position: 'fixed', bottom: '32px', right: '32px', width: '64px', height: '64px', borderRadius: '32px',
            background: 'var(--text-primary)', color: 'white', display: 'flex', justifyContent: 'center', alignItems: 'center',
            cursor: 'pointer', boxShadow: 'var(--shadow-lg)', zIndex: 9998, border: 'none', transition: 'transform 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
          }}
          onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.05) translateY(-4px)'}
          onMouseLeave={e => e.currentTarget.style.transform = 'none'}
        >
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        </button>
      )}

      {/* Floating Chat Box */}
      {isChatOpen && results.length > 0 && (
        <ChatBox availableFiles={results} initialFilename={initialChatFile} onClose={() => setIsChatOpen(false)} />
      )}

      {/* Hero 区 */}
      <div className="hero-container upload-container" style={{ display: 'flex', width: '100%', gap: '80px', alignItems: 'center', minHeight: '80vh' }}>
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
            border: 2px solid var(--text-primary);
            border-radius: 8px;
            background: white;
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
            font-size: 20px;
            letter-spacing: 1px;
          }
          .laser-line {
            position: absolute;
            left: -10px;
            right: -10px;
            height: 2px;
            background: var(--text-primary);
            box-shadow: 0 0 10px 2px rgba(0,0,0,0.2);
            animation: scan 2s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
            z-index: 10;
          }
          @keyframes scan {
            0% { top: 0%; opacity: 0; }
            15% { opacity: 1; }
            85% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
          }
        `}</style>

        <div className="hero-text" style={{ flex: 1, paddingBottom: '40px' }}>
          <h1 style={{ fontSize: '72px', lineHeight: 1.05, marginBottom: '24px' }}>
            深度阅读。<br/>
            即刻同步。
          </h1>
          <p style={{ fontSize: '18px', color: 'var(--text-secondary)', marginBottom: '40px', maxWidth: '480px', lineHeight: 1.6, fontWeight: 400 }}>
            批量上传学术论文，提取核心机制，与 AI 对话，并直接归档至你的 Notion 知识库。干净、快速、优雅。
          </p>
        </div>

        <div className="hero-panel-wrapper" style={{ flex: 1, position: 'relative', height: '600px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div className="hero-panel-bg glass-panel" style={{ position: 'absolute', top: '50%', left: '50%', width: '380px', height: '240px', transform: 'translate(-30%, -70%) rotate(8deg)', opacity: 0.5, zIndex: 0 }}></div>
          <div className="hero-panel glass-panel" style={{ position: 'relative', zIndex: 1, width: '420px', padding: '40px', display: 'flex', flexDirection: 'column', gap: '24px', transform: 'translate(-10%, 10%)' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '16px' }}>
              <div>
                <label className="input-label">归档频道</label>
                <select className="input-field" value={channel} onChange={(e) => setChannel(e.target.value)}>
                  <option value="group">团队数据库 (公开)</option>
                  <option value="private">个人工作区</option>
                </select>
              </div>
              <div className="form-row" style={{ display: 'flex', gap: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label className="input-label">汇报人 <span style={{color:'red'}}>*</span></label>
                  <input type="text" className="input-field" placeholder="例如：张三" value={reporter} onChange={(e) => setReporter(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); startAnalysis(); } }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label className="input-label">日期</label>
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
                 border: `2px dashed ${isDragging ? '#000' : 'rgba(0,0,0,0.1)'}`,
                 borderRadius: '16px', padding: '40px 20px', textAlign: 'center',
                 background: isDragging ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.4)',
                 cursor: 'pointer', transition: 'all 0.3s',
                 height: '160px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center'
              }}
            >
              <div className="scanner-container" style={{ transform: 'scale(0.8)', margin: '0 0 16px 0', filter: isAnalyzing ? 'brightness(1.1)' : 'none' }}>
                <div className="pdf-doc"></div>
                {(files.length === 0 || isAnalyzing) && <div className="laser-line" style={{ animationDuration: isAnalyzing ? '0.8s' : '2.5s' }}></div>}
              </div>
              
              <h3 style={{ fontSize: '15px', color: 'var(--text-primary)', margin: 0, fontWeight: 600 }}>
                {isAnalyzing ? "正在使用 DeepSeek 解析..." : (files.length > 0 ? `就绪: ${files.length} 个文件` : '拖拽 PDF 至此或点击上传')}
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
                className="btn"
                onClick={(e) => { e.stopPropagation(); startAnalysis(); }}
                style={{ width: '100%', padding: '16px', fontSize: '14px', borderRadius: '12px', fontWeight: 600, opacity: reporter.trim() ? 1 : 0.5, cursor: reporter.trim() ? 'pointer' : 'not-allowed', background: 'var(--text-primary)', color: 'white', border: 'none' }}
              >
                {reporter.trim() ? `开始批量扫描 (${files.length})` : "请输入汇报人姓名"}
              </button>
            )}
            
            {files.length > 0 && !isAnalyzing && (
              <button onClick={(e) => { e.stopPropagation(); setFiles([]); }} style={{ background: 'transparent', border: 'none', color: 'var(--text-secondary)', fontSize: '12px', cursor: 'pointer', marginTop: '-12px' }}>
                清空队列
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 第二屏：解析结果 */}
      <div ref={reportRef} style={{ display: 'flex', flexDirection: 'column', gap: '40px', marginTop: '40px' }}>
        
        {/* 全局 Notion 黏性操作条 */}
        {results.length > 0 && (
          <div style={{ position: 'sticky', top: '24px', zIndex: 100, background: 'rgba(255,255,255,0.85)', backdropFilter: 'blur(20px)', padding: '16px 24px', borderRadius: '16px', boxShadow: 'var(--shadow-md)', display: 'flex', gap: '16px', alignItems: 'center', border: '1px solid var(--border-color)' }}>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>同步至 Notion:</span>
            <select 
              className="input-field" 
              style={{ margin: 0, flex: 1, padding: '10px 16px', borderRadius: '8px', cursor: 'pointer', background: 'transparent', border: 'none', boxShadow: 'none', fontWeight: 500 }} 
              value={notionSyncTarget} 
              onChange={(e) => setNotionSyncTarget(e.target.value)}
              disabled={isPushing}
            >
              <option value="all">同步所有文件 (剩余 {results.length - pushedIndexes.size} 个)</option>
              {results.map((res, index) => (
                <option key={index} value={index}>
                  📄 {res.Title_ZH || res._filename} {pushedIndexes.has(index) ? ' (✅ Synced)' : ''}
                </option>
              ))}
            </select>
            <button 
              className="btn" 
              disabled={isPushing || (results.length - pushedIndexes.size === 0 && notionSyncTarget === 'all')} 
              onClick={handlePushTarget}
              style={{ padding: '10px 24px', borderRadius: '8px', whiteSpace: 'nowrap', fontWeight: 600, opacity: isPushing ? 0.7 : 1, cursor: isPushing ? 'wait' : 'pointer', background: 'var(--text-primary)', color: 'white', border: 'none' }}
            >
              {isPushing ? "同步中..." : "推向Notion"}
            </button>
          </div>
        )}
        
        {results.map((res, index) => {
          return (
            <div key={index} className="report-container glass-panel" style={{ padding: '40px', width: '100%', display: 'flex', flexDirection: 'column', gap: '32px' }}>
              <div>
                <div className="report-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <h2 style={{ fontSize: '32px', color: 'var(--text-primary)', letterSpacing: '-0.5px', margin: 0, lineHeight: 1.2 }}>{res.Title_ZH || res.Title_EN || res._filename}</h2>
                  <div className="report-header-actions" style={{ display: 'flex', gap: '8px', marginLeft: '16px' }}>
                    <button onClick={() => openChatForFile(res._filename)} style={{ background: 'var(--text-primary)', color: 'white', border: 'none', borderRadius: '20px', padding: '4px 16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> Chat
                    </button>
                    <div style={{ fontSize: '12px', background: 'rgba(0,0,0,0.05)', padding: '4px 12px', borderRadius: '20px', fontWeight: 600, color: 'var(--text-secondary)', whiteSpace: 'nowrap', display: 'flex', alignItems: 'center' }}>
                      {res._filename}
                    </div>
                  </div>
                </div>
                {res.notion_url && (
                  <div style={{ marginTop: '4px', marginBottom: '16px' }}>
                    <button className="notion-goto-btn" onClick={() => window.open(res.notion_url, '_blank')}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                      立即前往 Notion 查阅排版
                    </button>
                  </div>
                )}
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: 0 }}>
                  {res.Journal || '未知期刊'} • IF: {res.IF || 'N/A'} • {res.PubDate || '未知日期'} • 汇报人: {reporter}
                </p>
              </div>

              {/* Paper Card Sections (Pre-Figure) */}
              {[
                { title: '02 一句话总结 (Summary)', content: res.Sec02_Summary || res.Sec01_Summary },
                { title: '03 研究问题 (Research Question)', content: res.Sec03_Question },
                { title: '04 研究背景 (Background)', content: res.Sec04_Background },
                { title: '05 核心痛点 (Pain Points)', content: res.Sec05_PainPoints || res.Sec02_Motivation },
                { title: '06 核心思想 (Core Idea)', content: res.Sec06_Idea },
                { title: '07 方法概览 (Method)', content: res.Sec07_Method || res.Sec03_Methods },
                { title: '08 模块拆解 (Modules)', content: res.Sec08_Modules },
                { title: '09 核心公式 (Formulas)', content: res.Sec09_Formulas },
              ].map((section, idx) => section.content ? (
                <div key={`sec-a-${idx}`}>
                  <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>{section.title}</h3>
                  <p style={{ lineHeight: 1.8, color: 'var(--text-primary)', whiteSpace: 'pre-line' }}>{formatText(section.content)}</p>
                </div>
              ) : null)}

              <div>
                <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>机制流程图</h3>
                {res.Mermaid_Flowchart && (
                  <div style={{ textAlign: 'center', margin: '20px 0', overflowX: 'auto', background: 'white', padding: '32px', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
                    <div id={`mermaid-container-${index}`}></div>
                  </div>
                )}
              </div>

              {Array.isArray(res.Figure_Analysis) && res.Figure_Analysis.length > 0 && (
                <div>
                  <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '24px' }}>关键发现与数据</h3>
                  <div style={{ display: 'grid', gap: '24px', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))' }}>
                    {res.Figure_Analysis.map((fig: any, idx: number) => {
                      const figName = typeof fig === 'string' ? fig : (fig?.Figure_Name || "");
                      const matchedFig = Array.isArray(res.extracted_figs) && figName
                        ? res.extracted_figs.find((ef: any) => 
                            ef?.name?.toLowerCase() === figName.toLowerCase() || 
                            ef?.label?.toLowerCase() === figName.toLowerCase()
                          )
                        : null;
                      
                      return (
                        <div key={idx} style={{ background: 'white', padding: '24px', borderRadius: '16px', border: '1px solid var(--border-color)', boxShadow: 'var(--shadow-sm)', display: 'flex', flexDirection: 'column' }}>
                          <h4 style={{ color: 'var(--text-primary)', marginBottom: '16px', fontSize: '16px', fontWeight: 700 }}>{figName || "未命名图表"}</h4>
                          
                          {matchedFig ? (
                            <div style={{ marginBottom: '20px', textAlign: 'center', background: '#f9f9fb', padding: '16px', borderRadius: '8px' }}>
                              <img 
                                src={`${import.meta.env.PROD ? "" : "http://localhost:8000"}/${matchedFig.path}`} 
                                alt={figName} 
                                onClick={() => setZoomedImage(`${import.meta.env.PROD ? "" : "http://localhost:8000"}/${matchedFig.path}`)}
                                style={{ maxWidth: '100%', maxHeight: '250px', objectFit: 'contain', borderRadius: '4px', cursor: 'zoom-in' }} 
                              />
                            </div>
                          ) : (
                            <div style={{ marginBottom: '16px', background: 'rgba(0,0,0,0.02)', color: 'var(--text-secondary)', padding: '12px', borderRadius: '8px', fontSize: '13px', textAlign: 'center' }}>
                              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{opacity: 0.5, marginBottom: '8px'}}><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                              <br/>图表图片未提取。
                            </div>
                          )}

                          <div style={{ lineHeight: 1.6, fontSize: '14px', color: 'var(--text-primary)', flex: 1 }}>
                            <div style={{ marginBottom: '8px' }}><strong style={{color:'var(--text-primary)'}}>结论: </strong>{typeof fig === 'string' ? fig : (fig?.Core_Conclusion || "N/A")}</div>
                            <div><strong style={{color:'var(--text-primary)'}}>详细信息: </strong>{typeof fig === 'string' ? "" : (fig?.Key_Details || "N/A")}</div>
                          </div>

                          {/* 强化原文图注展示 */}
                          {matchedFig && matchedFig.caption && (
                            <div style={{ background: 'rgba(0,0,0,0.02)', padding: '12px 16px', borderRadius: '8px', marginTop: '16px', borderLeft: '3px solid var(--text-primary)' }}>
                              <strong style={{fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px'}}>📄 原文图注:</strong>
                              <p style={{fontSize: '13px', margin: 0, color: 'var(--text-secondary)', fontStyle: 'italic', lineHeight: 1.5}}>{matchedFig.caption}</p>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Paper Card Sections (Post-Figure) */}
              {[
                { title: '11 结论的正确解读边界 (Interpretation)', content: res.Sec11_Interpretation },
                { title: '12 局限性 (Limitations)', content: res.Sec12_Limitations || res.Sec04_Limitations },
                { title: '13 批判性分析 (Critical Analysis)', content: res.Sec13_CriticalAnalysis },
                { title: '14 学到的知识 (Knowledge Learned)', content: res.Sec14_Knowledge },
                { title: '15 与已有知识的联系 (Connections)', content: res.Sec15_Connections },
                { title: '16 研究启发 (Research Ideas)', content: res.Sec16_Ideas || res.Sec05_Ideas },
              ].map((section, idx) => section.content ? (
                <div key={`sec-b-${idx}`}>
                  <h3 style={{ fontSize: '18px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', marginBottom: '16px' }}>{section.title}</h3>
                  <p style={{ lineHeight: 1.8, color: 'var(--text-primary)', whiteSpace: 'pre-line' }}>{formatText(section.content)}</p>
                </div>
              ) : null)}
            </div>
          );
        })}
      </div>
      
    </div>
  );
};

export default UploadZone;
