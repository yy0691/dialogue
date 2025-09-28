"""
最小化版本的Flask应用 - 专门为Vercel部署优化
解决404和500错误
"""
import os
import json
import time
from flask import Flask, jsonify, request, session

# 创建Flask应用 - 不依赖模板文件
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dialogue_app_secret_key_2024')

# 延迟导入API模块
def get_gemini_client():
    """延迟导入并创建Gemini客户端"""
    try:
        import google.generativeai as genai
        
        # 获取API密钥
        api_key = os.environ.get('GOOGLE_API_KEY', 'AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw')
        if not api_key:
            return None
            
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        print(f"Gemini客户端初始化失败: {e}")
        return None

@app.route('/')
def index():
    """返回简单的HTML页面"""
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SBMA 遗传咨询 AI 对话系统</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
            .dialogue-area { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .counselor { background: #e3f2fd; }
            .client { background: #f3e5f5; }
            button { padding: 10px 20px; margin: 5px; background: #2196f3; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #1976d2; }
            .options { margin: 10px 0; }
            .option-btn { display: block; width: 100%; text-align: left; margin: 5px 0; padding: 15px; background: #fff; border: 1px solid #ddd; }
            .option-btn:hover { background: #f0f0f0; }
            #response-area { min-height: 100px; border: 1px solid #ddd; padding: 10px; margin: 10px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SBMA 遗传咨询 AI 对话仿真系统</h1>
            
            <div id="dialogue-history"></div>
            
            <div class="options">
                <h3>请选择咨询师的话：</h3>
                <button class="option-btn" onclick="sendCounselorMessage('你好，我是遗传咨询师，请坐。今天来咨询什么问题？')">
                    你好，我是遗传咨询师，请坐。今天来咨询什么问题？
                </button>
                <button class="option-btn" onclick="sendCounselorMessage('我了解你的担心。能详细说说你舅舅的症状吗？')">
                    我了解你的担心。能详细说说你舅舅的症状吗？
                </button>
                <button class="option-btn" onclick="sendCounselorMessage('肯尼迪病确实有遗传性。让我为你详细解释一下遗传模式。')">
                    肯尼迪病确实有遗传性。让我为你详细解释一下遗传模式。
                </button>
            </div>
            
            <div id="response-area">
                <p><strong>AI咨询者回复将显示在这里</strong></p>
            </div>
            
            <div>
                <button onclick="testAPI()">测试API连接</button>
                <button onclick="startNewDialogue()">开始新对话</button>
            </div>
            
            <div id="status" style="margin-top: 20px; padding: 10px; background: #fff; border-radius: 5px;"></div>
        </div>

        <script>
            let sessionId = null;
            
            function showStatus(message, isError = false) {
                const status = document.getElementById('status');
                status.innerHTML = message;
                status.style.background = isError ? '#ffebee' : '#e8f5e8';
                status.style.color = isError ? '#c62828' : '#2e7d32';
            }
            
            function addToHistory(speaker, message) {
                const history = document.getElementById('dialogue-history');
                const div = document.createElement('div');
                div.className = `dialogue-area ${speaker.toLowerCase()}`;
                div.innerHTML = `<strong>${speaker}：</strong>${message}`;
                history.appendChild(div);
                history.scrollTop = history.scrollHeight;
            }
            
            async function testAPI() {
                showStatus('正在测试API连接...');
                try {
                    const response = await fetch('/test_api_key', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const data = await response.json();
                    showStatus(data.message, !data.success);
                } catch (error) {
                    showStatus(`API测试失败: ${error.message}`, true);
                }
            }
            
            async function startNewDialogue() {
                showStatus('正在开始新对话...');
                try {
                    const response = await fetch('/start', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ node_id: 'M1-01' })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const data = await response.json();
                    sessionId = data.session_id;
                    showStatus(`对话已开始，会话ID: ${sessionId}`);
                    document.getElementById('dialogue-history').innerHTML = '';
                } catch (error) {
                    showStatus(`开始对话失败: ${error.message}`, true);
                }
            }
            
            async function sendCounselorMessage(message) {
                if (!sessionId) {
                    await startNewDialogue();
                }
                
                addToHistory('咨询师', message);
                showStatus('正在生成AI回复...');
                
                try {
                    // 发送咨询师消息
                    await fetch('/counselor_turn', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ dialogue: message })
                    });
                    
                    // 生成AI回复
                    const response = await fetch('/generate_client_response', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({})
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    
                    const data = await response.json();
                    
                    if (data.error) {
                        showStatus(data.error, true);
                        if (data.need_api_key) {
                            showStatus(data.error + ' - 请检查API密钥配置', true);
                        }
                    } else {
                        addToHistory('咨询者（李森）', data.dialogue);
                        document.getElementById('response-area').innerHTML = 
                            `<p><strong>最新回复：</strong>${data.dialogue}</p>`;
                        showStatus('回复生成成功');
                    }
                } catch (error) {
                    showStatus(`生成回复失败: ${error.message}`, true);
                }
            }
            
            // 页面加载时自动测试API
            window.onload = function() {
                showStatus('页面加载完成，正在初始化...');
                testAPI();
            };
        </script>
    </body>
    </html>
    """
    return html_content

@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        "status": "ok", 
        "timestamp": int(time.time()),
        "version": "minimal_v1.0"
    })

@app.route('/test_api_key', methods=['POST'])
def test_api_key():
    """测试API密钥"""
    try:
        client = get_gemini_client()
        if not client:
            return jsonify({
                "success": False, 
                "message": "无法初始化Gemini客户端，请检查API密钥"
            })
        
        # 发送测试请求
        response = client.generate_content("请回复'测试成功'")
        if response and response.text:
            return jsonify({
                "success": True, 
                "message": f"API连接成功！回复: {response.text}"
            })
        else:
            return jsonify({
                "success": False, 
                "message": "API响应为空"
            })
            
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return jsonify({
                "success": False, 
                "message": "API配额已用完，请设置您自己的Google API密钥"
            })
        else:
            return jsonify({
                "success": False, 
                "message": f"测试失败: {error_msg}"
            })

@app.route('/start', methods=['POST'])
def start_dialogue():
    """开始对话"""
    try:
        session['dialogue_state'] = {
            'current_node': 'M1-01',
            'history': [],
            'last_counselor_message': ''
        }
        session.modified = True
        
        return jsonify({
            "session_id": f"session_{int(time.time())}",
            "status": "started"
        })
    except Exception as e:
        return jsonify({"error": f"开始对话失败: {str(e)}"}), 500

@app.route('/counselor_turn', methods=['POST'])
def counselor_turn():
    """处理咨询师回合"""
    try:
        data = request.json
        message = data.get('dialogue', '')
        
        if 'dialogue_state' not in session:
            session['dialogue_state'] = {'history': [], 'last_counselor_message': ''}
        
        session['dialogue_state']['last_counselor_message'] = message
        session['dialogue_state']['history'].append({
            'speaker': '咨询师', 
            'message': message
        })
        session.modified = True
        
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500

@app.route('/generate_client_response', methods=['POST'])
def generate_client_response():
    """生成咨询者回复"""
    try:
        client = get_gemini_client()
        if not client:
            return jsonify({
                "error": "AI模型未初始化，请检查API密钥配置",
                "need_api_key": True
            }), 500
        
        # 获取对话状态
        dialogue_state = session.get('dialogue_state', {})
        counselor_message = dialogue_state.get('last_counselor_message', '你好')
        
        # 构建提示词
        prompt = f"""你是李森，你的舅舅患有肯尼迪病（SBMA），你很担心这个病会遗传给你，正在咨询遗传咨询师。

咨询师刚才说："{counselor_message}"

请以李森的身份回复。你的特点：
- 有些焦虑但很有礼貌
- 希望弄清楚所有关于遗传的问题
- 关心自己和家人的健康

请只输出你的回复内容，不要其他解释。"""
        
        # 调用API
        response = client.generate_content(prompt)
        if not response or not response.text:
            return jsonify({"error": "AI返回空响应"}), 500
        
        ai_response = response.text.strip()
        
        # 更新对话历史
        dialogue_state['history'].append({
            'speaker': '咨询者', 
            'message': ai_response
        })
        session['dialogue_state'] = dialogue_state
        session.modified = True
        
        return jsonify({
            "speaker": "咨询者",
            "dialogue": ai_response
        })
        
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return jsonify({
                "error": "API配额已用完，请设置您自己的Google API密钥",
                "quota_exceeded": True,
                "need_api_key": True
            }), 500
        else:
            return jsonify({
                "error": f"生成回复失败: {error_msg}",
                "need_api_key": False
            }), 500

# Vercel需要的应用对象
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
