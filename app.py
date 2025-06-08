
from flask import Flask, render_template, request, redirect, jsonify, send_file, session
import json
import random
import os
from datetime import datetime
from collections import defaultdict
import socket
import sys
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "replace_this_with_a_real_secret_key")

USER_DATA_FILE = 'users.json'

# Load users from the JSON file
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        '0': {'password': 'yihan0326dhmaker', 'nickname': '管理员0', 'is_admin': True}
    }

# Save users data to the JSON file
def save_users(users):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users_db = load_users()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users_db and users_db[username]['password'] == password:
            session['username'] = username
            session['nickname'] = users_db[username]['nickname']
            session['is_admin'] = users_db[username].get('is_admin', False)
            return redirect('/')
        else:
            return '用户名或密码错误！'
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nickname = request.form['nickname']
        if username not in users_db:
            users_db[username] = {'password': password, 'nickname': nickname, 'is_admin': False}
            save_users(users_db)
            session['username'] = username
            session['nickname'] = nickname
            session['is_admin'] = False
            return redirect('/')
        else:
            return '用户名已存在，请换一个！'
    return render_template('signup.html')

@app.route('/')
def index():
    if 'username' not in session:
        return redirect('/login')
    history = session.get('history', [])
    return render_template('index.html', history=history, username=session['username'], nickname=session['nickname'], is_admin=session.get('is_admin', False))

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return '权限不足！'
    return render_template('admin.html', users=users_db)

@app.route('/delete_user/<username>', methods=['POST'])
def delete_user(username):
    if not session.get('is_admin'):
        return '权限不足！'
    if username == 'admin':
        return '无法删除管理员账号'
    users_db.pop(username, None)
    save_users(users_db)
    return redirect('/admin')

@app.route('/create_admin', methods=['GET', 'POST'])
def create_admin():
    if not session.get('is_admin'):
        return '权限不足！'
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nickname = request.form['nickname']
        if username not in users_db:
            users_db[username] = {'password': password, 'nickname': nickname, 'is_admin': True}
            save_users(users_db)
            return redirect('/admin')
        else:
            return '用户名已存在！'
    return render_template('create_admin.html')

@app.route('/random', methods=['POST'])
def do_random():
    raw = request.form['options']
    options = [line.split('#')[0].strip() for line in raw.strip().splitlines() if line.strip() and not line.startswith('#')]
    if len(options) < 2:
        return jsonify({'error': '至少输入两个有效选项'})
    result = random.choice(options)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = f"[{ts}] 最终选择：{result}"
    history = session.get('history', [])
    history.append(record)
    session['history'] = history
    return jsonify({'result': result})

@app.route('/custom', methods=['POST'])
def do_custom():
    raw = request.form['options']
    times = int(request.form['times'])
    options = [line.split('#')[0].strip() for line in raw.strip().splitlines() if line.strip() and not line.startswith('#')]

    if len(options) < 2 or times < 1:
        return jsonify({'error': '请输入有效选项和次数'})

    result_count = defaultdict(int)
    for _ in range(times):
        result = random.choice(options)
        result_count[result] += 1

    grouped = defaultdict(list)
    for k, v in result_count.items():
        grouped[v].append(k)

    sorted_counts = sorted(grouped.items(), reverse=True)
    top_count = sorted_counts[0][0]
    top_items = sorted(grouped[top_count])
    display_text = f"共随机 {times} 次，出现最多的是：\n" + "\n".join(f"{item}: {top_count} 次" for item in top_items)

    summary_parts = []
    for count, items in sorted_counts:
        for item in sorted(items):
            summary_parts.append(f"{item}: {count}次")
    full_summary = ", ".join(summary_parts)
    log = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 自定义随机 {times} 次：{full_summary}"

    history = session.get('history', [])
    history.append(log)
    session['history'] = history

    return jsonify({
        'display': display_text,
        'labels': list(result_count.keys()),
        'values': list(result_count.values())
    })

@app.route('/clear', methods=['POST'])
def clear_history():
    session['history'] = []
    return jsonify({'ok': True})

@app.route('/export')
def export_history():
    history = session.get('history', [])
    return '\n'.join(history), 200, {'Content-Type': 'text/plain; charset=utf-8'}

@app.route('/export_excel')
def export_excel():
    wb = Workbook()
    ws = wb.active
    ws.title = "历史记录"
    ws.append(["记录"])
    history = session.get('history', [])
    for line in history:
        ws.append([line])
    filename = "history.xlsx"
    wb.save(filename)
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    try:
        port = int(os.environ.get("PORT", 5000))
        host = '0.0.0.0'
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
            except OSError:
                print(f"Error: Port {port} is already in use.")
                sys.exit(1)
        app.run(debug=False, host=host, port=port)
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        sys.exit(1)
