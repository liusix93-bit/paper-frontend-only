import React, { useState, useRef } from 'react';

const SkillConverter: React.FC = () => {
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [notionUrl, setNotionUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    setIsUploading(true);
    setError(null);
    setNotionUrl(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/skills/extract', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      if (response.ok && data.status === 'success') {
        setNotionUrl(data.url);
      } else {
        setError(data.message || '上传失败，请重试');
      }
    } catch (err: any) {
      if (err.message === 'Failed to fetch') {
        setError('网络连接失败 (Failed to fetch) - 请检查后端服务器是否已在 8000 端口启动');
      } else {
        setError(err.message || '网络错误，请确保后端服务已启动');
      }
    } finally {
      setIsUploading(false);
      setIsDragging(false);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    if (!isUploading) setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    
    if (isUploading) return;
    
    const file = event.dataTransfer.files?.[0];
    if (file && file.type === 'application/pdf') {
      processFile(file);
    } else if (file) {
      setError('仅支持 PDF 格式的文件');
    }
  };



  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      width: '100%',
      height: '100%',
      padding: '40px',
      background: 'var(--card-bg, #ffffff)',
      borderRadius: '16px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.05)'
    }}>
      <h2 style={{ marginBottom: '20px', color: 'var(--text-primary)' }}>论文转换为 Agent Skill</h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '30px', textAlign: 'center' }}>
        上传你的论文，我们将使用大模型自动为你提取一篇具备专业知识的 Agent Skill。<br />
        生成的 Skill 将自动推送到 Notion 知识库中，方便大家随时查阅和使用。
      </p>
      
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleFileUpload} 
        accept=".pdf" 
        style={{ display: 'none' }} 
      />

      {notionUrl ? (
        <div style={{
          border: '2px solid #10B981',
          backgroundColor: '#ECFDF5',
          borderRadius: '12px',
          padding: '40px',
          width: '100%',
          maxWidth: '600px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎉</div>
          <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px', color: '#065F46' }}>
            Skill 提取并归档成功！
          </div>
          <a 
            href={notionUrl} 
            target="_blank" 
            rel="noreferrer"
            style={{ 
              display: 'inline-block',
              padding: '12px 24px', 
              background: '#10B981', 
              color: 'white', 
              textDecoration: 'none',
              borderRadius: '8px',
              fontWeight: 600
            }}
          >
            前往 Notion 知识库查看并复制
          </a>
          <div 
            onClick={() => setNotionUrl(null)} 
            style={{ marginTop: '20px', cursor: 'pointer', color: '#6B7280', fontSize: '14px', textDecoration: 'underline' }}
          >
            继续提取下一篇
          </div>
        </div>
      ) : (
        <div 
          onClick={() => !isUploading && fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          style={{
            border: `2px dashed ${isDragging ? '#10B981' : (isUploading ? '#9CA3AF' : 'var(--accent-color)')}`,
            backgroundColor: isDragging ? '#ECFDF5' : 'transparent',
            borderRadius: '12px',
            padding: '60px 40px',
            width: '100%',
            maxWidth: '600px',
            textAlign: 'center',
            cursor: isUploading ? 'wait' : 'pointer',
            transition: 'all 0.3s ease',
            opacity: isUploading ? 0.7 : 1
          }}
        >
          <div style={{ fontSize: '48px', marginBottom: '16px', transform: isDragging ? 'scale(1.1)' : 'scale(1)', transition: 'transform 0.2s' }}>
            {isUploading ? '⏳' : (isDragging ? '📥' : '📚')}
          </div>
          <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: 'var(--text-primary)' }}>
            {isUploading ? '正在极速提取并推送到 Notion...' : (isDragging ? '松开鼠标即可上传' : '点击或拖拽论文到此处')}
          </div>
          <div style={{ fontSize: '14px', color: 'var(--text-tertiary)' }}>支持 PDF 格式</div>
          
          {error && (
            <div style={{ marginTop: '20px', color: '#EF4444', fontSize: '14px', background: '#FEE2E2', padding: '8px', borderRadius: '4px' }}>
              {error}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SkillConverter;
