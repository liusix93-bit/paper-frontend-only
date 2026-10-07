import re
import os

css_code = """@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400&display=swap');

:root {
  --bg-color: #050505;
  --surface-color: rgba(255, 255, 255, 0.03);
  --surface-hover: rgba(255, 255, 255, 0.05);
  --border-color: rgba(255, 255, 255, 0.08);
  --border-highlight: rgba(255, 255, 255, 0.2);
  
  --text-primary: #FFFFFF;
  --text-secondary: #888888;
  --text-tertiary: #555555;
  
  --accent-color: #5E6AD2;
  --accent-hover: #7582FF;
  --highlight-color: #00F0FF;
  --danger-color: #FF453A;
  --success-color: #32D74B;
  
  --shadow-sm: 0 4px 12px rgba(0, 0, 0, 0.5);
  --shadow-md: 0 10px 30px rgba(0, 0, 0, 0.8);
  --shadow-glow: 0 0 20px rgba(94, 106, 210, 0.4);
  
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  
  --font-sans: 'Outfit', -apple-system, sans-serif;
  --font-mono: 'JetBrains Mono', monospace;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: var(--font-sans);
  background-color: var(--bg-color);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
  overflow-x: hidden;
  background-image: 
    radial-gradient(circle at 15% 50%, rgba(94, 106, 210, 0.15), transparent 25%),
    radial-gradient(circle at 85% 30%, rgba(0, 240, 255, 0.1), transparent 25%);
}

body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
  z-index: -1;
  mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
  -webkit-mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
}

.glass-panel {
  background: var(--surface-color);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.3s ease, border-color 0.3s ease;
}

.glass-panel:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 40px rgba(0,0,0,0.8), 0 0 0 1px var(--border-highlight);
  border-color: var(--border-highlight);
}

.btn {
  font-family: var(--font-sans);
  border: none;
  background: var(--surface-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.btn:hover:not(:disabled) {
  background: var(--surface-hover);
  border-color: var(--border-highlight);
  transform: translateY(-2px);
}

.btn:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary {
  background: var(--text-primary);
  color: var(--bg-color);
  border: none;
}

.btn-primary:hover:not(:disabled) {
  background: var(--text-primary);
  box-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
  transform: translateY(-2px) scale(1.02);
}

.input-field {
  width: 100%;
  padding: 16px 20px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: rgba(0, 0, 0, 0.2);
  font-family: var(--font-sans);
  font-size: 15px;
  color: var(--text-primary);
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.input-field:focus {
  border-color: var(--accent-color);
  background: rgba(0, 0, 0, 0.4);
  outline: none;
  box-shadow: var(--shadow-glow);
}

.input-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-secondary);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Animations */
@keyframes glowPulse {
  0% { box-shadow: 0 0 20px rgba(94, 106, 210, 0.2); }
  50% { box-shadow: 0 0 40px rgba(94, 106, 210, 0.6); }
  100% { box-shadow: 0 0 20px rgba(94, 106, 210, 0.2); }
}

@keyframes slideUpFade {
  from { opacity: 0; transform: translateY(30px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-in {
  animation: slideUpFade 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: var(--bg-color);
}
::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}
"""

with open('src/index.css', 'w', encoding='utf-8') as f:
    f.write(css_code)

print('Updated index.css')

with open('src/components/UploadZone.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = {
    r"'#fff'": "'var(--surface-color)'",
    r"'#ffffff'": "'var(--surface-color)'",
    r"'#333'": "'var(--text-primary)'",
    r"'#666'": "'var(--text-secondary)'",
    r"'#999'": "'var(--text-tertiary)'",
    r"'rgba\(255, 255, 255, 0\.95\)'": "'var(--bg-color)'",
    r"'rgba\(255, 255, 255, 0\.85\)'": "'rgba(5,5,5,0.85)'",
    r"'rgba\(255, 255, 255, 0\.7\)'": "'var(--surface-color)'",
    r"'rgba\(255, 255, 255, 0\.9\)'": "'var(--surface-color)'",
    r"'rgba\(255, 255, 255, 0\.5\)'": "'var(--surface-color)'",
    r"'rgba\(0, 0, 0, 0\.01\)'": "'transparent'",
    r"'rgba\(0, 0, 0, 0\.02\)'": "'var(--surface-color)'",
    r"'#f8f9fa'": "'var(--surface-color)'",
    r"'#f5f5f5'": "'var(--surface-color)'",
    r"'white'": "'var(--text-primary)'",
    r"boxShadow: '0 20px 50px rgba\(0,0,0,0\.1\)'": "boxShadow: 'var(--shadow-md)'",
    r"background: 'rgba\(123,115,212,0\.05\)'": "background: 'var(--surface-hover)'",
    r"color: 'white'": "color: 'var(--bg-color)'",
    r"background: 'white'": "background: 'var(--surface-color)'",
    r"filter: isAnalyzing \? 'brightness\(1\.5\)' : 'none'": "filter: isAnalyzing ? 'brightness(1.5) drop-shadow(0 0 20px rgba(94, 106, 210, 0.8))' : 'none'",
    r"color: rgba\(0, 0, 0, 0\.1\)": "color: 'rgba(255, 255, 255, 0.05)'"
}

for pattern, repl in replacements.items():
    content = re.sub(pattern, repl, content)

content = content.replace('className="report-container"', 'className="report-container animate-in"')
content = content.replace('className="upload-container"', 'className="upload-container animate-in"')

with open('src/components/UploadZone.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Updated UploadZone.tsx')
