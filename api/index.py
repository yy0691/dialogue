import sys
import os
import json
import time
from flask import Flask, render_template, request, jsonify, session, Response

# 将项目根目录添加到sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 延迟导入，避免初始化时的错误
def get_api_modules():
    """延迟导入API相关模块"""
    try:
        import google.generativeai as genai
        from openai import OpenAI
        return genai, OpenAI
    except ImportError as e:
        print(f"导入API模块失败: {e}")
        return None, None

# 创建Flask应用
app = Flask(__name__, template_folder='./templates', static_folder='./static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key_for_vercel')

# 全局变量
dialogue_data = {}

class APIClient:
    """简化的API客户端"""
    
    def __init__(self, provider="gemini", api_key=None):
        self.provider = provider
        self.api_key = api_key
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化API客户端"""
        try:
            genai, OpenAI = get_api_modules()
            if not genai:
                raise Exception("无法导入API模块")
                
            if self.provider == "gemini" and self.api_key:
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel('gemini-1.5-flash')
            else:
                raise Exception("API配置不完整")
        except Exception as e:
            print(f"API客户端初始化失败: {e}")
            self.client = None
    
    def generate_content(self, prompt, stream=False):
        """生成内容"""
        if not self.client:
            raise Exception("API客户端未初始化")
        return self.client.generate_content(prompt, stream=stream)

def load_dialogue_data():
    """加载对话数据"""
    global dialogue_data
    if dialogue_data:
        return
        
    try:
        # 尝试多个路径
        possible_files = [
            'dialogue_output_2.json',
            'dialogue_output.json',
            os.path.join(os.path.dirname(__file__), 'dialogue_output_2.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dialogue_output_2.json')
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    dialogue_data = json.load(f)
                print(f"成功加载对话数据: {file_path}")
                return
        
        # 如果找不到文件，使用默认数据
        dialogue_data = {
            "M1-01": {
                "character": "咨询师",
                "goal": "开始遗传咨询对话",
                "examples": ["你好，我是遗传咨询师，请坐。今天来咨询什么问题？"],
                "choices": [{"nextNode": "M1-02"}]
            },
            "M1-02": {
                "character": "咨询者",
                "goal": "表达担忧",
                "examples": ["医生您好，我很担心，我舅舅最近被诊断出肯尼迪病，我想了解这个病会不会遗传给我。"],
                "choices": [{"nextNode": "END"}]
            }
        }
        print("使用默认对话数据")
        
    except Exception as e:
        print(f"加载对话数据失败: {e}")
        dialogue_data = {}

def get_api_key():
    """获取API密钥"""
    # 优先从环境变量获取
    api_key = os.environ.get('GOOGLE_API_KEY')
    if api_key:
        return api_key
    
    # 如果环境变量没有，尝试从config获取
    try:
        from config import get_google_api_key
        return get_google_api_key()
    except:
        # 最后使用硬编码的密钥（仅用于测试）
        return "AIzaSyD-mbv6XXPnxuwIuanGrpjNMJ55gQbzoCw"

def get_model_for_session():
    """获取当前会话的模型"""
    try:
        api_key = get_api_key()
        if api_key:
            return APIClient(provider="gemini", api_key=api_key)
    except Exception as e:
        print(f"获取模型失败: {e}")
    return None

@app.route('/')
def index():
    """主页"""
    load_dialogue_data()
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_dialogue():
    """开始对话"""
    load_dialogue_data()
    
    data = request.json or {}
    start_node_id = data.get('node_id', 'M1-01')
    
    # 初始化会话状态
    if 'dialogue_states' not in session:
        session['dialogue_states'] = {}
    
    session['active_stage'] = 'M1'
    
    node = dialogue_data.get(start_node_id)
    if not node:
        return jsonify({"error": f"节点 {start_node_id} 不存在"}), 404
    
    # 初始化状态
    session['dialogue_states']['M1'] = {
        "current_node_id": start_node_id,
        "last_counselor_message": "",
        "history": []
    }
    session.modified = True
    
    return jsonify({
        "session_id": f"session_{int(time.time())}",
        "node_info": {
            "id": start_node_id,
            "goal": node.get('goal', ''),
            "options": node.get('examples', [])
        }
    })

@app.route('/generate_client_response', methods=['POST'])
def generate_client_response():
    """生成咨询者回复"""
    try:
        model = get_model_for_session()
        if not model:
            return jsonify({"error": "AI模型未初始化"}), 500
        
        active_stage = session.get('active_stage', 'M1')
        if 'dialogue_states' not in session or active_stage not in session['dialogue_states']:
            return jsonify({"error": "没有活跃的对话会话"}), 400
        
        state = session['dialogue_states'][active_stage]
        counselor_message = state.get('last_counselor_message', '你好')
        
        # 简化的提示词
        prompt = f"""你是李森，你的舅舅患有肯尼迪病，你很担心遗传问题，正在咨询遗传咨询师。
        
咨询师刚才说："{counselor_message}"

请以李森的身份回复，语气要自然、有些焦虑但礼貌。只输出回复内容，不要其他解释。"""
        
        response = model.generate_content(prompt)
        if not response or not response.text:
            return jsonify({"error": "AI返回空响应"}), 500
        
        ai_response = response.text.strip()
        
        # 更新历史
        state['history'].append({"speaker": "咨询者", "dialogue": ai_response})
        session.modified = True
        
        return jsonify({
            "speaker": "咨询者",
            "dialogue": ai_response,
            "session_id": f"session_{int(time.time())}"
        })
        
    except Exception as e:
        print(f"生成回复失败: {e}")
        return jsonify({"error": f"生成回复失败: {str(e)}"}), 500

@app.route('/counselor_turn', methods=['POST'])
def counselor_turn():
    """处理咨询师回合"""
    try:
        data = request.json
        selected_option = data.get('dialogue')
        if not selected_option:
            return jsonify({"error": "没有提供对话内容"}), 400
        
        active_stage = session.get('active_stage', 'M1')
        if 'dialogue_states' not in session:
            session['dialogue_states'] = {}
        if active_stage not in session['dialogue_states']:
            session['dialogue_states'][active_stage] = {
                "current_node_id": "M1-01",
                "last_counselor_message": "",
                "history": []
            }
        
        state = session['dialogue_states'][active_stage]
        state['last_counselor_message'] = selected_option
        state['history'].append({"speaker": "咨询师", "dialogue": selected_option})
        session.modified = True
        
        return jsonify({
            "speaker": "咨询师",
            "dialogue": selected_option,
            "session_id": f"session_{int(time.time())}"
        })
        
    except Exception as e:
        print(f"处理咨询师回合失败: {e}")
        return jsonify({"error": f"处理失败: {str(e)}"}), 500

@app.route('/test_api_key', methods=['POST'])
def test_api_key():
    """测试API密钥"""
    try:
        data = request.json or {}
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({"success": False, "message": "API密钥不能为空"}), 400
        
        # 创建测试客户端
        test_client = APIClient(provider="gemini", api_key=api_key)
        if not test_client.client:
            return jsonify({"success": False, "message": "API客户端初始化失败"})
        
        # 发送测试请求
        response = test_client.generate_content("请回复'测试成功'")
        if response and response.text:
            return jsonify({"success": True, "message": "API密钥有效，连接成功！"})
        else:
            return jsonify({"success": False, "message": "API响应为空"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"测试失败: {str(e)}"})

# 健康检查端点
@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok", "timestamp": int(time.time())})

# Vercel需要的应用对象
application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
