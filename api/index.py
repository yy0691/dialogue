import sys
import os

# 将项目根目录添加到sys.path，以便正确导入config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify, session
import json
import google.generativeai as genai
import textwrap
from config import get_google_api_key

# 显式指定模板和静态文件夹的路径
app = Flask(__name__, template_folder='../templates', static_folder='../static')
# 设置密钥以启用session。在生产环境中，应使用更安全的方式（如环境变量）管理密钥。
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_secure_development_secret_key')


# 全局变量仅用于存储不会改变的对话数据和AI模型实例
dialogue_data = {}
model = None

def load_dialogue_data(filename="dialogue_output_2.json"):
    """加载对话JSON数据，如果尚未加载。"""
    global dialogue_data
    if not dialogue_data:
        try:
            file_path = os.path.join(os.path.dirname(__file__), filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                dialogue_data = json.load(f)
        except Exception as e:
            print("错误: 加载对话文件失败: " + str(e))

def get_api_key():
    """从环境变量中获取Google API密钥。"""
    try:
        return get_google_api_key()
    except ValueError as e:
        print("错误: " + str(e))
        raise

def initialize_ai():
    """初始化AI模型，如果尚未初始化。"""
    global model
    if model is None:
        try:
            api_key = get_api_key()
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            print("AI初始化失败: " + str(e))

# 在应用启动时加载数据和初始化AI
load_dialogue_data()
initialize_ai()

def get_stage_from_node_id(node_id):
    """从节点ID中提取阶段标识，例如从 'M1-01' 提取 'M1'。"""
    return node_id.split('-')[0] if '-' in node_id else 'default'

def get_next_node_id(node):
    """安全地从节点的选项中获取下一个节点ID。"""
    choices = node.get("choices", [])
    if choices and isinstance(choices, list) and len(choices) > 0 and 'nextNode' in choices[0]:
        return choices[0]['nextNode']
    return "END"

# --- Prompt构建函数保持不变 ---
def build_client_prompt(counselor_message, client_goal, client_examples=None):
    """为AI构建扮演咨询者的提示词。"""
    persona = "你叫李森，你的舅舅可能患有遗传病（肯尼迪病），你现在非常担心，正在向遗传咨询师咨询。你的风格是有些焦虑，但很有礼貌，希望弄清楚所有问题。"
    context = "咨询师刚刚对你说了：'" + counselor_message + "'"
    goal = client_goal
    
    reference_responses = ""
    if client_examples:
        examples_str = "\n".join([f"- {ex}" for ex in client_examples])
        reference_responses = f"""
# 参考回复 (Reference Responses)
这是你应该说的内容的一些参考例子。你可以选择其中一个，或者结合它们，或者根据这些例子生成一个相似的、自然的回答。
{examples_str}
"""

    constraints = "请只输出你作为咨询者（李森）的回答，语言要自然、口语化，不要包含任何额外的解释或标签，例如不要说“咨询者：”或使用Markdown。"
    
    prompt = f"""
    # 角色设定 (Persona)
    {persona}
    # 对话上下文 (Context)
    {context}
    # 本轮对话核心任务 (Goal)
    {goal}
    {reference_responses}
    # 输出要求 (Constraints)
    {constraints}
    """
    return textwrap.dedent(prompt).strip()

def build_client_custom_response_prompt(question, dialogue_history):
    """为AI构建回答自定义问题的提示词。"""
    persona = "你叫李森，你的舅舅可能患有遗传病（肯尼迪病），你现在非常担心，正在向遗传咨询师咨询。你的风格是有些焦虑，但很有礼貌，希望弄清楚所有问题。"
    
    known_facts = """
    # 已知事实 (Known Facts)
    这是你的家庭背景，你在回答任何问题时都必须严格遵守这些事实，不能杜撰或改变：
    - 你的舅舅：今年50岁，6年前开始出现肌无力症状，已被诊断为肯尼迪病(SBMA)。他没有孩子。
    - 你的妈妈：今年47岁，身体健康。她是你外婆唯一的孩子，没有其他兄弟姐妹。
    - 你自己：你有一个健康的妹妹。
    - 你的外婆：在你小时候就因车祸去世，生前很健康，没有类似舅舅的症状。
    - 你的曾外公（外婆的爸爸）：听妈妈说，他有和舅舅类似的症状。
    """

    context = f"当前的对话历史摘要如下：\n{dialogue_history}"
    goal = "现在，咨询师没有选择预设选项，而是向你提出了一个额外的问题：'" + question + "'"
    
    constraints = "请直接、简洁地回答咨询师提出的额外问题。你的回答必须严格基于以上的‘已知事实’，不得与事实冲突。请只输出你作为咨询者（李森）的回答，语言要自然、口语化，不要包含任何额外的解释或标签。"
    
    prompt = f"""
    # 角色设定 (Persona)
    {persona}
    {textwrap.dedent(known_facts)}
    # 对话上下文 (Context)
    {context}
    # 本轮对话核心任务 (Goal)
    {goal}
    # 输出要求 (Constraints)
    {constraints}
    """
    return textwrap.dedent(prompt).strip()


@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_dialogue():
    """开始或切换对话阶段。如果阶段已存在，则恢复；否则，创建新阶段。"""
    data = request.json or {}
    start_node_id = data.get('node_id', 'M1-01')
    stage = get_stage_from_node_id(start_node_id)
    
    session['active_stage'] = stage
    
    if 'dialogue_states' not in session:
        session['dialogue_states'] = {}
    
    states = session.get('dialogue_states', {})
    
    if stage not in states:
        # --- 初始化新阶段 ---
        node = dialogue_data.get(start_node_id)
        if not node:
            return jsonify({"error": "Start node " + start_node_id + " not found."}), 404

        counselor_message = node.get('examples', ["你好，请坐。需要什么帮助吗？"])[0]
        next_node_id = get_next_node_id(node)
        
        states[stage] = {
            "current_node_id": next_node_id,
            "last_counselor_message": counselor_message,
            "history": [{"speaker": "咨询师", "dialogue": counselor_message}]
        }
        session['dialogue_states'] = states
        session.modified = True
        
        next_node = dialogue_data.get(next_node_id)
        return jsonify({
            "speaker": "咨询师",
            "dialogue": counselor_message,
            "node_info": {
                "id": next_node_id,
                "goal": next_node.get('goal') if next_node else "对话结束"
            }
        })
    else:
        # --- 恢复现有阶段 ---
        state = states[stage]
        current_node_id = state['current_node_id']
        node = dialogue_data.get(current_node_id)
        
        return jsonify({
            "resuming": True,
            "history": state.get('history', []),
            "node_info": {
                "id": current_node_id,
                "goal": node.get('goal') if node else "对话结束",
                "options": node.get('examples', []) if node else []
            }
        })

@app.route('/generate_client_response', methods=['POST'])
def generate_client_response():
    """根据咨询师的话，生成咨询者的回复，并更新当前阶段的状态。"""
    if not model:
        return jsonify({"error": "AI model not initialized"}), 500

    active_stage = session.get('active_stage')
    if not active_stage or 'dialogue_states' not in session or active_stage not in session['dialogue_states']:
        return jsonify({"error": "No active dialogue session."}, 400)
    
    state = session['dialogue_states'][active_stage]

    current_node_id = state['current_node_id']
    last_counselor_message = state['last_counselor_message']
    node = dialogue_data.get(current_node_id)
    if not node:
        return jsonify({"error": "Invalid node ID"}), 400

    prompt = build_client_prompt(last_counselor_message, node.get('goal'), node.get('examples', []))
    try:
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        next_node_id = get_next_node_id(node)
        next_node = dialogue_data.get(next_node_id)

        # 更新状态并标记为已修改
        state['current_node_id'] = next_node_id
        state['history'].append({"speaker": "咨询者", "dialogue": ai_response})
        session.modified = True

        return jsonify({
            "speaker": "咨询者",
            "dialogue": ai_response,
            "node_info": {
                "id": next_node_id,
                "goal": next_node.get('goal') if next_node else "对话结束",
                "options": next_node.get('examples', []) if next_node else []
            }
        })
    except Exception as e:
        return jsonify({"error": "API call failed: " + str(e)}), 500

@app.route('/counselor_turn', methods=['POST'])
def counselor_turn():
    """处理咨询师的选择，并推进到下一个节点。"""
    data = request.json
    selected_option = data.get('dialogue')
    if not selected_option:
        return jsonify({"error": "No dialogue provided"}), 400
        
    active_stage = session.get('active_stage')
    if not active_stage or 'dialogue_states' not in session or active_stage not in session['dialogue_states']:
        return jsonify({"error": "No active dialogue session."}, 400)
    
    state = session['dialogue_states'][active_stage]
    
    current_node_id = state['current_node_id']
    node = dialogue_data.get(current_node_id)
    if not node:
        return jsonify({"error": "Invalid node ID for counselor turn"}), 400

    next_node_id = get_next_node_id(node)
    next_node = dialogue_data.get(next_node_id)

    # 更新状态并标记为已修改
    state['last_counselor_message'] = selected_option
    state['history'].append({"speaker": "咨询师", "dialogue": selected_option})
    state['current_node_id'] = next_node_id
    session.modified = True

    return jsonify({
        "speaker": "咨询师",
        "dialogue": selected_option,
        "node_info": {
            "id": next_node_id,
            "goal": next_node.get('goal') if next_node else "对话结束"
        }
    })

@app.route('/ask_client_custom_question', methods=['POST'])
def ask_client_custom_question():
    """处理用户向咨询者（AI）提出的自定义问题，不改变主对话流程状态。"""
    if not model:
        return jsonify({"error": "AI model not initialized"}), 500

    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400

    active_stage = session.get('active_stage')
    if not active_stage or 'dialogue_states' not in session or active_stage not in session['dialogue_states']:
        return jsonify({"error": "No active dialogue session."}, 400)
    
    state = session['dialogue_states'][active_stage]

    current_node_id = state['current_node_id']
    current_node = dialogue_data.get(current_node_id)
    if not current_node:
        return jsonify({"error": "Invalid current node ID"}), 400

    # 使用更完整的对话历史作为上下文
    history_str = "\n".join([f"{item['speaker']}: {item['dialogue']}" for item in state.get('history', [])])
    prompt = build_client_custom_response_prompt(question, history_str)
    
    try:
        response = model.generate_content(prompt)
        ai_answer = response.text.strip()
        
        # 关键：不改变 state 或 session
        return jsonify({
            "speaker": "咨询者", 
            "dialogue": ai_answer,
            "is_custom": True,
            "options_to_restore": current_node.get('examples', [])
        })
    except Exception as e:
        return jsonify({"error": "API call failed: " + str(e)}), 500

# 本地开发时运行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)