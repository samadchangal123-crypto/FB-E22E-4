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
app.secret_key = 'your-secret-key-here-make-it-strong'
app.config['SESSION_TYPE'] = 'filesystem'

# ==================== SIRF YAHAN CHANGE KIYA HAI ====================
ADMIN_PASSWORD = "MISSALIYA@123"           # CHANGE 1: Password
WHATSAPP_NUMBER = ""                        # CHANGE 2: WhatsApp number hata diya
APPROVAL_FILE = "approved_keys.json"
PENDING_FILE = "pending_approvals.json"
ADMIN_UID = "MISS_ALIYA_UID"                # CHANGE 3: UID change
# ================================================================

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
    # CHANGE 4: WhatsApp message hata diya, ab kuch nahi bhejega
    return "#"

def check_approval(key):
    approved_keys = load_approved_keys()
    if key in approved_keys:
        return True
    return False

def start_automation(config, user_id):
    if user_id not in automation_states:
        automation_states[user_id] = AutomationState()
    
    automation_states[user_id].running = True
    automation_states[user_id].logs.append("🚀 Automation started")
    
    def run_automation():
        # Automation logic
        pass
    
    thread = threading.Thread(target=run_automation, daemon=True)
    thread.start()

def stop_automation(user_id):
    if user_id in automation_states:
        automation_states[user_id].running = False
        automation_states[user_id].logs.append("⛔ Automation stopped")

# ==================== ROUTES (Bilkul Original) ====================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        pending = load_pending_approvals()
        user_key = generate_user_key(username, password)
        
        if check_approval(user_key):
            session['user_id'] = str(uuid.uuid4())
            session['username'] = username
            session['user_key'] = user_key
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            if username not in [data['username'] for data in pending.values()]:
                pending[user_key] = {'username': username, 'timestamp': time.time()}
                save_pending_approvals(pending)
                whatsapp_url = send_whatsapp_message(username, user_key)
                flash(f'Approval requested! Share this key with admin: {user_key}', 'info')
            else:
                flash('Approval pending. Please wait for admin.', 'warning')
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user_config = db.get_user_config(user_id)
    
    if not user_config:
        user_config = {'chat_id': '', 'prefix': '', 'delay': 30, 'cookies': '', 'messages_file_content': ''}
    
    if user_id not in automation_states:
        automation_states[user_id] = AutomationState()
    
    automation_state = automation_states[user_id]
    
    return render_template_string(DASHBOARD_TEMPLATE,
                         username=session.get('username'),
                         user_key=session.get('user_key'),
                         user_id=user_id,
                         user_config=user_config,
                         automation_state=automation_state)

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
            return render_template_string(ADMIN_LOGIN_TEMPLATE)
    
    pending = load_pending_approvals()
    approved_keys = load_approved_keys()
    
    return render_template_string(ADMIN_PANEL_TEMPLATE,
                         pending=pending,
                         approved_keys=approved_keys)

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

# ==================== TEMPLATES (Original Style) ====================

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Miss Aliya E2EE - Login</title>
    <style>
        body {
            background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .login-container {
            background: rgba(0,0,0,0.85);
            padding: 40px;
            border-radius: 10px;
            width: 350px;
            text-align: center;
            border: 2px solid #ffd700;
        }
        h2 { color: #ffd700; }
        input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border: 1px solid #ffd700;
            background: rgba(255,255,255,0.1);
            color: white;
        }
        button {
            width: 100%;
            padding: 10px;
            background: #ffd700;
            color: black;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }
        .flash { color: #ffaa00; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="login-container">
        <h2>👑 Miss Aliya E2EE 👑</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% for category, message in messages %}
                <div class="flash">{{ message }}</div>
            {% endfor %}
        {% endwith %}
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Miss Aliya - Dashboard</title>
    <style>
        body {
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            font-family: Arial, sans-serif;
            color: white;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: auto;
        }
        .card {
            background: rgba(0,0,0,0.85);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #ffd700;
        }
        h1, h2 { color: #ffd700; }
        input, textarea {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            background: rgba(255,255,255,0.1);
            border: 1px solid #ffd700;
            color: white;
        }
        button {
            padding: 10px 20px;
            background: #ffd700;
            color: black;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin: 5px;
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-box {
            background: rgba(0,0,0,0.8);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            flex: 1;
            border: 1px solid #ffd700;
        }
        .stat-number {
            font-size: 2em;
            color: #ffd700;
        }
        .log-container {
            background: black;
            padding: 10px;
            border-radius: 5px;
            height: 300px;
            overflow-y: auto;
            font-family: monospace;
        }
        .log-entry {
            color: #0f0;
            padding: 2px 0;
        }
        .navbar {
            background: rgba(0,0,0,0.9);
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
        }
        a { color: #ffd700; }
    </style>
</head>
<body>
    <div class="navbar">
        <span>👑 Miss Aliya E2EE</span>
        <span>Welcome, {{ username }} | <a href="/logout">Logout</a></span>
    </div>
    <div class="container">
        <div class="stats">
            <div class="stat-box">
                <div>📨 Messages Sent</div>
                <div class="stat-number" id="msgCount">{{ automation_state.message_count }}</div>
            </div>
            <div class="stat-box">
                <div>Status</div>
                <div class="stat-number" id="status">
                    {% if automation_state.running %}🟢 Running{% else %}🔴 Stopped{% endif %}
                </div>
            </div>
            <div class="stat-box">
                <div>User Key</div>
                <div class="stat-number" style="font-size:1em;">{{ user_key }}</div>
            </div>
        </div>
        
        <div class="card">
            <h2>⚙️ Configuration</h2>
            <form method="POST" action="/save_config">
                <input type="text" name="chat_id" placeholder="Chat ID" value="{{ user_config.chat_id }}">
                <input type="text" name="name_prefix" placeholder="Name Prefix" value="{{ user_config.prefix }}">
                <input type="number" name="delay" placeholder="Delay (seconds)" value="{{ user_config.delay }}">
                <textarea name="cookies" rows="5" placeholder="Cookies">{{ user_config.cookies }}</textarea>
                <textarea name="messages" rows="5" placeholder="Messages (one per line)">{{ user_config.messages_file_content }}</textarea>
                <button type="submit">💾 Save Configuration</button>
            </form>
        </div>
        
        <div class="card">
            <h2>🤖 Automation Control</h2>
            <button onclick="startAuto()" {% if automation_state.running %}disabled{% endif %}>▶️ Start Automation</button>
            <button onclick="stopAuto()" {% if not automation_state.running %}disabled{% endif %}>⏹️ Stop Automation</button>
        </div>
        
        <div class="card">
            <h2>📜 Live Logs</h2>
            <div class="log-container" id="logContainer">
                {% for log in automation_state.logs[-30:] %}
                    <div class="log-entry">{{ log }}</div>
                {% endfor %}
            </div>
        </div>
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
                    document.getElementById('status').innerHTML = data.running ? '🟢 Running' : '🔴 Stopped';
                    document.getElementById('msgCount').innerHTML = data.message_count;
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
    <title>Miss Aliya - Admin</title>
    <style>
        body {
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .admin-box {
            background: rgba(0,0,0,0.9);
            padding: 40px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid #ffd700;
        }
        input, button {
            padding: 10px;
            margin: 10px;
            border-radius: 5px;
        }
        button { background: #ffd700; cursor: pointer; }
    </style>
</head>
<body>
    <div class="admin-box">
        <h2 style="color:#ffd700;">Miss Aliya - Admin</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password">
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
    <title>Miss Aliya - Admin Panel</title>
    <style>
        body {
            background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)),
                        url('https://i.ibb.co/fV5vsYkJ/IMG-20260505-222322-503.jpg');
            background-size: cover;
            font-family: Arial, sans-serif;
            color: white;
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: rgba(0,0,0,0.85);
            padding: 20px;
            border-radius: 10px;
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
        <h2>👑 Miss Aliya - Admin Panel</h2>
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
        <br><a href="/dashboard">← Back to Dashboard</a>
    </div>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
