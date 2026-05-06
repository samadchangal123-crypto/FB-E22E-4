from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import time
import threading
import uuid
import hashlib
import os
import json
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import database as db
import requests

app = Flask(__name__)
app.secret_key = 'missaliya-secret-key-2026'
app.config['SESSION_TYPE'] = 'filesystem'

# ==================== CHANGES YAHAN SE ====================
ADMIN_PASSWORD = "MISSALIYA@123"  # PASSWORD CHANGE KAR DIYA
WHATSAPP_NUMBER = ""  # HATA DIYA (EMPTY)
APPROVAL_FILE = "approved_keys.json"
PENDING_FILE = "pending_approvals.json"
ADMIN_UID = "MISS_ALIYA_UID"  # CHANGE KAR DIYA

APP_NAME = "Miss Aliya"
# ==================== CHANGES YAHAN TAK ====================

# Global automation states
automation_states = {}

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

def generate_user_key(username, password):
    combined = f"{username}:{password}"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:8].upper()
    return f"KEY-{key_hash}"

def load_approved_keys():
    if os.path.exists(APPROVAL_FILE):
        try:
            with open(APPROVAL_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_approved_keys(keys):
    with open(APPROVAL_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def load_pending_approvals():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pending_approvals(pending):
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending, f, indent=2)

def send_whatsapp_message(user_name, approval_key):
    # WHATSAPP HATA DIYA - AB KUCH NAHI KAREGA
    return "#"

def check_approval(key):
    approved_keys = load_approved_keys()
    if key in approved_keys:
        return True
    return False

def start_automation(config, user_id):
    # Automation logic yahan aayegi
    if user_id not in automation_states:
        automation_states[user_id] = AutomationState()
    
    automation_states[user_id].running = True
    automation_states[user_id].logs.append(f"🚀 Automation started by {APP_NAME}")
    
    def run_automation():
        # Your automation logic here
        pass
    
    thread = threading.Thread(target=run_automation, daemon=True)
    thread.start()

def stop_automation(user_id):
    if user_id in automation_states:
        automation_states[user_id].running = False
        automation_states[user_id].logs.append(f"⛔ Automation stopped by {APP_NAME}")

# ==================== ROUTES ====================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple password check
        if password == ADMIN_PASSWORD:
            session['user_id'] = hashlib.md5(username.encode()).hexdigest()
            session['username'] = username
            session['user_key'] = generate_user_key(username, password)
            flash(f'Welcome {APP_NAME}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template_string(LOGIN_TEMPLATE, app_name=APP_NAME)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_config = db.get_user_config(user_id)
    
    if user_id not in automation_states:
        automation_states[user_id] = AutomationState()
    
    automation_state = automation_states[user_id]
    
    return render_template_string(DASHBOARD_TEMPLATE,
                         username=session.get('username'),
                         user_key=session.get('user_key'),
                         user_id=user_id,
                         user_config=user_config,
                         automation_state=automation_state,
                         app_name=APP_NAME)

@app.route('/save_config', methods=['POST'])
def save_config():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    chat_id = request.form.get('chat_id', '')
    name_prefix = request.form.get('name_prefix', '')
    delay = int(request.form.get('delay', 30))
    cookies = request.form.get('cookies', '')
    messages = request.form.get('messages', '')
    
    db.update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages)
    flash('Configuration saved successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/start_automation', methods=['POST'])
def start_automation_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    user_config = db.get_user_config(user_id)
    
    if not user_config or not user_config['chat_id']:
        return jsonify({'success': False, 'message': 'Please set Chat ID first!'})
    
    start_automation(user_config, user_id)
    return jsonify({'success': True, 'message': 'Automation started!'})

@app.route('/stop_automation', methods=['POST'])
def stop_automation_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    user_id = session['user_id']
    stop_automation(user_id)
    return jsonify({'success': True, 'message': 'Automation stopped!'})

@app.route('/get_logs')
def get_logs():
    if 'user_id' not in session:
        return jsonify({'logs': []})
    
    user_id = session['user_id']
    if user_id in automation_states:
        return jsonify({'logs': automation_states[user_id].logs[-50:]})
    return jsonify({'logs': []})

@app.route('/get_status')
def get_status():
    if 'user_id' not in session:
        return jsonify({'running': False, 'message_count': 0})
    
    user_id = session['user_id']
    if user_id in automation_states:
        automation_state = automation_states[user_id]
        return jsonify({
            'running': automation_state.running,
            'message_count': automation_state.message_count
        })
    return jsonify({'running': False, 'message_count': 0})

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password != ADMIN_PASSWORD:
            flash('Invalid admin password!', 'error')
            return render_template_string(ADMIN_LOGIN_TEMPLATE, app_name=APP_NAME)
    
    pending = load_pending_approvals()
    approved_keys = load_approved_keys()
    
    return render_template_string(ADMIN_PANEL_TEMPLATE,
                         pending=pending,
                         approved_keys=approved_keys,
                         app_name=APP_NAME)

@app.route('/admin/approve/<key>')
def approve_key(key):
    pending = load_pending_approvals()
    approved_keys = load_approved_keys()
    
    if key in pending:
        approved_keys[key] = pending[key]
        save_approved_keys(approved_keys)
        del pending[key]
        save_pending_approvals(pending)
        flash(f'Key {key} approved!', 'success')
    
    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    if 'user_id' in session:
        user_id = session['user_id']
        if user_id in automation_states and automation_states[user_id].running:
            stop_automation(user_id)
    
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# ==================== HTML TEMPLATES (with IBB Background & 3D/Broken CSS) ====================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ app_name }} - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            min-height: 100vh;
            background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            background-position: center;
            font-family: 'Courier New', monospace;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        /* 3D/GLITCH EFFECT */
        @keyframes glitch {
            0% { transform: skew(0deg, 0deg); text-shadow: -2px 0 red, 2px 0 blue; }
            25% { transform: skew(2deg, 1deg); text-shadow: 2px 0 red, -2px 0 blue; }
            50% { transform: skew(-1deg, -1deg); text-shadow: -2px 0 blue, 2px 0 red; }
            75% { transform: skew(1deg, -1deg); text-shadow: 2px 0 blue, -2px 0 red; }
            100% { transform: skew(0deg, 0deg); text-shadow: -2px 0 red, 2px 0 blue; }
        }
        
        .glitch-text {
            font-size: 3rem;
            text-align: center;
            color: #ffd700;
            animation: glitch 0.3s infinite;
            margin-bottom: 20px;
            font-family: 'Cinema', monospace;
        }
        
        .login-container {
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(15px);
            padding: 40px;
            border-radius: 20px;
            width: 400px;
            text-align: center;
            border: 2px solid rgba(255,215,0,0.5);
            box-shadow: 0 20px 40px rgba(0,0,0,0.5), inset 0 0 30px rgba(255,215,0,0.1);
            transform: perspective(800px) translateZ(10px);
            transition: transform 0.3s;
        }
        
        .login-container:hover {
            transform: perspective(800px) translateZ(20px);
        }
        
        input {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            background: rgba(255,255,255,0.1);
            border: 1px solid #ffd700;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
        }
        
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(45deg, #800000, #ff0000);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 5px 0 #4a0000;
            transition: 0.1s;
        }
        
        button:hover {
            transform: translateY(2px);
            box-shadow: 0 2px 0 #4a0000;
        }
        
        .flash {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background: rgba(255,0,0,0.3);
            color: #ff8888;
        }
        
        h2 {
            color: #ffd700;
            margin-bottom: 20px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="glitch-text">👑 {{ app_name }} 👑</div>
        <h2>⚜️ ENTER THE REALM ⚜️</h2>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        
        <form method="POST">
            <input type="text" name="username" placeholder="USERNAME" required>
            <input type="password" name="password" placeholder="PASSWORD" required>
            <button type="submit">🔓 UNLOCK</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ app_name }} - Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            background-attachment: fixed;
            font-family: 'Courier New', monospace;
            color: white;
        }
        
        @keyframes glitch {
            0% { text-shadow: -2px 0 red, 2px 0 blue; }
            50% { text-shadow: 2px 0 red, -2px 0 blue; }
            100% { text-shadow: -2px 0 red, 2px 0 blue; }
        }
        
        .glitch-text {
            animation: glitch 0.3s infinite;
        }
        
        .navbar {
            background: rgba(0,0,0,0.9);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            border-bottom: 2px solid #ffd700;
        }
        
        .container {
            max-width: 1200px;
            margin: 30px auto;
            padding: 0 20px;
        }
        
        .card {
            background: rgba(0,0,0,0.85);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,215,0,0.3);
            transform: perspective(800px) translateZ(5px);
            transition: 0.3s;
        }
        
        .card:hover {
            transform: perspective(800px) translateZ(15px);
        }
        
        input, textarea, select {
            width: 100%;
            padding: 10px;
            margin: 8px 0;
            background: rgba(255,255,255,0.1);
            border: 1px solid #ffd700;
            border-radius: 8px;
            color: white;
        }
        
        button {
            padding: 10px 20px;
            background: linear-gradient(45deg, #800000, #ff0000);
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            box-shadow: 0 4px 0 #4a0000;
            transition: 0.1s;
            font-weight: bold;
        }
        
        button:hover {
            transform: translateY(2px);
            box-shadow: 0 1px 0 #4a0000;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-box {
            background: rgba(0,0,0,0.8);
            padding: 20px;
            text-align: center;
            border-radius: 15px;
            border: 1px solid #ffd700;
        }
        
        .stat-number {
            font-size: 2rem;
            color: #ffd700;
        }
        
        .log-container {
            background: black;
            padding: 15px;
            border-radius: 10px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 0.8rem;
        }
        
        .log-entry {
            color: #0f0;
            padding: 2px 0;
            border-left: 2px solid lime;
            padding-left: 8px;
            margin: 3px 0;
        }
        
        .btn-group {
            display: flex;
            gap: 15px;
            margin-top: 15px;
        }
        
        .btn-group button {
            flex: 1;
        }
        
        h2 {
            color: #ffd700;
            margin-bottom: 20px;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            border-top: 1px solid #ffd700;
            margin-top: 40px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <span style="color:#ffd700;">👑 {{ app_name }}</span>
        <span>Welcome, {{ username }} | <a href="/logout" style="color:#ff4444;">Logout</a></span>
    </div>
    
    <div class="container">
        <div class="glitch-text" style="font-size:2rem; text-align:center; margin-bottom:20px;">⚜️ {{ app_name }}'s THRONE ⚜️</div>
        
        <div class="stats">
            <div class="stat-box">
                <div>📨 MESSAGES</div>
                <div class="stat-number" id="msgCount">{{ automation_state.message_count }}</div>
            </div>
            <div class="stat-box">
                <div>STATUS</div>
                <div class="stat-number" id="status">
                    {% if automation_state.running %}🟢 ACTIVE{% else %}🔴 DORMANT{% endif %}
                </div>
            </div>
            <div class="stat-box">
                <div>📊 LOGS</div>
                <div class="stat-number">{{ automation_state.logs|length }}</div>
            </div>
        </div>
        
        <div class="card">
            <h2>⚙️ CONFIGURATION</h2>
            <form method="POST" action="/save_config">
                <input type="text" name="chat_id" placeholder="CHAT ID" value="{{ user_config.chat_id if user_config else '' }}">
                <input type="text" name="name_prefix" placeholder="NAME PREFIX" value="{{ user_config.prefix if user_config else '' }}">
                <input type="number" name="delay" placeholder="DELAY (seconds)" value="{{ user_config.delay if user_config else 30 }}">
                <textarea name="cookies" rows="5" placeholder="COOKIES (Netscape format)">{{ user_config.cookies if user_config else '' }}</textarea>
                <textarea name="messages" rows="5" placeholder="MESSAGES (one per line)">{{ user_config.messages_file_content if user_config else '' }}</textarea>
                <button type="submit">💾 SAVE CONFIGURATION</button>
            </form>
        </div>
        
        <div class="card">
            <h2>🤖 AUTOMATION CONTROL</h2>
            <div class="btn-group">
                <button onclick="startAuto()" {% if automation_state.running %}disabled{% endif %}>▶️ START E2EE</button>
                <button onclick="stopAuto()" {% if not automation_state.running %}disabled{% endif %}>⏹️ STOP E2EE</button>
            </div>
        </div>
        
        <div class="card">
            <h2>📜 LIVE LOGS</h2>
            <div class="log-container" id="logContainer">
                {% for log in automation_state.logs[-30:] %}
                    <div class="log-entry">{{ log }}</div>
                {% endfor %}
            </div>
        </div>
    </div>
    
    <div class="footer">
        ⚜️ BROKEN SYSTEM // {{ app_name }} EDITION ⚜️
    </div>
    
    <script>
        function startAuto() {
            fetch('/start_automation', {method: 'POST'})
                .then(() => location.reload());
        }
        
        function stopAuto() {
            fetch('/stop_automation', {method: 'POST'})
                .then(() => location.reload());
        }
        
        setInterval(function() {
            fetch('/get_logs')
                .then(r => r.json())
                .then(data => {
                    let container = document.getElementById('logContainer');
                    if(container) {
                        container.innerHTML = data.logs.map(l => `<div class="log-entry">${l}</div>`).join('');
                    }
                });
            
            fetch('/get_status')
                .then(r => r.json())
                .then(data => {
                    let statusEl = document.getElementById('status');
                    if(statusEl) {
                        statusEl.innerHTML = data.running ? '🟢 ACTIVE' : '🔴 DORMANT';
                    }
                    let msgEl = document.getElementById('msgCount');
                    if(msgEl) {
                        msgEl.innerHTML = data.message_count;
                    }
                });
        }, 3000);
    </script>
</body>
</html>
'''

ADMIN_LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ app_name }} - Admin Login</title>
    <style>
        body {
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            font-family: monospace;
        }
        .admin-box {
            background: rgba(0,0,0,0.9);
            padding: 40px;
            border-radius: 20px;
            border: 2px solid #ffd700;
            text-align: center;
        }
        input, button {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
        }
        button {
            background: #800000;
            color: white;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="admin-box">
        <h2 style="color:#ffd700;">{{ app_name }} - Admin</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''

ADMIN_PANEL_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ app_name }} - Admin Panel</title>
    <style>
        body {
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            font-family: monospace;
            color: white;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: rgba(0,0,0,0.85);
            padding: 30px;
            border-radius: 20px;
            border: 2px solid #ffd700;
        }
        h2 { color: #ffd700; }
        .key-item {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        a { color: #00ff00; }
    </style>
</head>
<body>
    <div class="container">
        <h2>👑 {{ app_name }} - Admin Panel</h2>
        
        <h3>Pending Approvals</h3>
        {% for key, data in pending.items() %}
            <div class="key-item">
                Key: {{ key }} | User: {{ data.username }} 
                | <a href="/admin/approve/{{ key }}">✅ Approve</a>
            </div>
        {% else %}
            <p>No pending approvals</p>
        {% endfor %}
        
        <h3>Approved Keys</h3>
        {% for key, data in approved_keys.items() %}
            <div class="key-item">Key: {{ key }} | User: {{ data.username }}</div>
        {% else %}
            <p>No approved keys</p>
        {% endfor %}
        
        <br>
        <a href="/dashboard">← Back to Dashboard</a>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
