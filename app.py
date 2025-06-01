# app.py - Web 版本终极决策助手 (Flask 后端)
from flask import Flask, render_template, request, redirect, jsonify
import json
import random
import os
from datetime import datetime

app = Flask(__name__)
DATA_FILE = 'decision_data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'history': []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

@app.route('/')
def index():
    return render_template('index.html', history=data.get('history', []))

@app.route('/random', methods=['POST'])
def do_random():
    raw = request.form['options']
    options = [line.split('#')[0].strip() for line in raw.strip().splitlines() if line.strip() and not line.startswith('#')]
    if len(options) < 2:
        return jsonify({'error': '至少输入两个有效选项'})
    result = random.choice(options)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record = f"[{ts}] 最终选择：{result}"
    data['history'].append(record)
    save_data(data)
    return jsonify({'result': result})

@app.route('/custom', methods=['POST'])
def do_custom():
    raw = request.form['options']
    times = int(request.form['times'])
    options = [line.split('#')[0].strip() for line in raw.strip().splitlines() if line.strip() and not line.startswith('#')]
    if len(options) < 2 or times < 1:
        return jsonify({'error': '请输入有效选项和次数'})
    result_count = {opt: 0 for opt in options}
    for _ in range(times):
        result = random.choice(options)
        result_count[result] += 1
    max_count = max(result_count.values())
    most_common = [k for k, v in result_count.items() if v == max_count]
    result_text = f"共随机 {times} 次，出现最多的是：\n" + "\n".join(f"{k}: {max_count} 次" for k in most_common)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data['history'].append(f"[{ts}] 自定义随机 {times} 次，最多：{', '.join(most_common)} ({max_count}次)")
    save_data(data)
    return jsonify({'result': result_text})

@app.route('/clear', methods=['POST'])
def clear_history():
    data['history'] = []
    save_data(data)
    return jsonify({'ok': True})

@app.route('/export')
def export_history():
    return '\n'.join(data.get('history', [])), 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
