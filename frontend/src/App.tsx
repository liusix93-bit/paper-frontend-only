import { useState, useEffect } from 'react';
import './index.css';
import UploadZone from './components/UploadZone';

function App() {
  const [isConnected, setIsConnected] = useState(true);
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
            style={{ 
              color: 'var(--text-primary)',
              borderBottom: '2px solid var(--accent-color)',
              paddingBottom: '4px',
            }}>
            文献精读系统
          </span>
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: isConnected ? '#10B981' : '#EF4444', boxShadow: isConnected ? '0 0 10px #10B981' : 'none' }}></div>
            <span style={{ fontSize: '12px', color: '#666', fontWeight: 500 }}>{isConnected ? 'API 已连接' : '离线状态'}</span>
          </div>
        </div>
      </header>

      <main style={{ flex: 1, padding: '0 60px 60px', position: 'relative' }}>
        <UploadZone />
      </main>
    </div>
  );
}

export default App;
