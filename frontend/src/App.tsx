import { useState, useEffect } from 'react';
import './index.css';
import UploadZone from './components/UploadZone';
import SkillConverter from './components/SkillConverter';

function App() {
  const [isConnected, setIsConnected] = useState(true);
  const [activeTab, setActiveTab] = useState<'read' | 'skill'>('read');

  // Mock server connection check
  useEffect(() => {
    const checkConnection = () => {
      setIsConnected(true);
    };
    checkConnection();
  }, []);

  return (
    <div className="app-container" style={{ maxWidth: '1440px', margin: '0 auto', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '40px 60px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ fontSize: '24px', fontWeight: 800, letterSpacing: '-0.5px', color: 'var(--text-primary)' }}>
            nova<span style={{ color: 'var(--accent-color)' }}>•</span>read
          </div>
        </div>
        
        <nav style={{ display: 'flex', gap: '40px', fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 600 }}>
          <span 
            onClick={() => setActiveTab('read')}
            style={{ 
              cursor: 'pointer', 
              color: activeTab === 'read' ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'read' ? '2px solid var(--accent-color)' : '2px solid transparent',
              paddingBottom: '4px',
              transition: 'all 0.3s ease'
            }}>
            文献精读系统
          </span>
          <span 
            onClick={() => setActiveTab('skill')}
            style={{ 
              cursor: 'pointer', 
              color: activeTab === 'skill' ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: activeTab === 'skill' ? '2px solid var(--accent-color)' : '2px solid transparent',
              paddingBottom: '4px',
              transition: 'all 0.3s ease'
            }}>
            提取文献Skill
          </span>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: isConnected ? '#10B981' : '#EF4444', boxShadow: isConnected ? '0 0 10px #10B981' : 'none' }}></div>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: 500 }}>{isConnected ? 'API 已连接' : '离线状态'}</span>
          </div>
        </div>
      </header>

      <main style={{ flex: 1, padding: '0 60px', position: 'relative', overflow: 'hidden' }}>
        <div style={{
          position: 'absolute',
          top: 0, left: 60, right: 60, bottom: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: activeTab === 'read' ? 1 : 0,
          pointerEvents: activeTab === 'read' ? 'auto' : 'none',
          visibility: activeTab === 'read' ? 'visible' : 'hidden',
          transition: 'all 0.4s ease-in-out',
          transform: activeTab === 'read' ? 'translateY(0)' : 'translateY(-20px)'
        }}>
          <UploadZone />
        </div>
        
        <div style={{
          position: 'absolute',
          top: 0, left: 60, right: 60, bottom: 60,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: activeTab === 'skill' ? 1 : 0,
          pointerEvents: activeTab === 'skill' ? 'auto' : 'none',
          visibility: activeTab === 'skill' ? 'visible' : 'hidden',
          transition: 'all 0.4s ease-in-out',
          transform: activeTab === 'skill' ? 'translateY(0)' : 'translateY(20px)'
        }}>
          <SkillConverter />
        </div>
      </main>
    </div>
  );
}

export default App;
