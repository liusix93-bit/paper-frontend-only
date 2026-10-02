import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const mockDataTrend = [
  { name: 'Jan', papers: 4 },
  { name: 'Feb', papers: 7 },
  { name: 'Mar', papers: 5 },
  { name: 'Apr', papers: 12 },
  { name: 'May', papers: 8 },
  { name: 'Jun', papers: 15 },
];

const mockDataJournal = [
  { name: 'Nature', value: 35 },
  { name: 'Science', value: 25 },
  { name: 'Cell', value: 20 },
  { name: 'Neuron', value: 15 },
  { name: 'Other', value: 5 },
];

const COLORS = ['#111111', '#444444', '#777777', '#AAAAAA', '#DDDDDD'];

const Dashboard = () => {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Simulate data loading
    setTimeout(() => setIsLoaded(true), 600);
  }, []);

  if (!isLoaded) {
    return (
      <div className="glass-panel" style={{ padding: '60px', textAlign: 'center', minHeight: '500px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--text-secondary)', animation: 'pulse 1.5s infinite' }}>正在从 Notion 加载大盘数据...</p>
      </div>
    );
  }

  return (
    <div style={{ animation: 'fadeIn 0.5s ease', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* 核心指标卡片区 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>已精读总篇数</p>
          <h3 style={{ fontSize: '36px', fontWeight: 800, marginTop: '8px' }}>128<span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)' }}> 篇</span></h3>
        </div>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>高分文献 (IF &gt; 10)</p>
          <h3 style={{ fontSize: '36px', fontWeight: 800, marginTop: '8px' }}>42<span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)' }}> 篇</span></h3>
        </div>
        <div className="glass-panel" style={{ padding: '24px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px' }}>本月组会主讲王</p>
          <h3 style={{ fontSize: '36px', fontWeight: 800, marginTop: '8px' }}>刘<span style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-secondary)' }}> (8篇)</span></h3>
        </div>
      </div>

      {/* 图表区 */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        
        {/* 趋势图 */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h4 style={{ marginBottom: '24px', fontSize: '16px', fontWeight: 600 }}>阅读量趋势 (最近6个月)</h4>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={mockDataTrend}>
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: 'var(--text-secondary)', fontSize: 12}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: 'var(--text-secondary)', fontSize: 12}} />
                <Tooltip cursor={{fill: 'rgba(0,0,0,0.03)'}} contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-md)' }} />
                <Bar dataKey="papers" fill="var(--accent-color)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 饼图 */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h4 style={{ marginBottom: '24px', fontSize: '16px', fontWeight: 600 }}>核心期刊分布</h4>
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={mockDataJournal}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                  stroke="none"
                >
                  {mockDataJournal.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: 'var(--shadow-md)' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginTop: '16px' }}>
            {mockDataJournal.map((entry, index) => (
              <div key={index} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: COLORS[index % COLORS.length] }}></span>
                {entry.name}
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
