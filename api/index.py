from flask import Flask, render_template, request, jsonify
import json
import os
import google.generativeai as genai
import textwrap
from config import get_google_api_key

app = Flask(__name__)

# 全局变量来管理对话状态
dialogue_data = {}
current_node_id = "M1-01"
last_counselor_message = "你好，请坐。需要什么帮助吗？"

def load_dialogue_data(filename="dialogue_output.json"):
    """加载并返回对话JSON数据。"""
    global dialogue_data
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            dialogue_data = json.load(f)
    except Exception as e:
        print(f"错误: 加载对话文件失败: {e}")

def get_api_key():
    """从环境变量中获取Google API密钥。"""
    try:
        return get_google_api_key()
    except ValueError as e:
        print(f"错误: {e}")
        raise ValueError("API Key not set")

def initialize_ai():
    """初始化AI模型"""
    try:
        api_key = get_api_key()
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash')
    except Exception as e:
        print(f"AI初始化失败: {e}")
        return None

# 在应用启动时加载数据和初始化AI
load_dialogue_data()
model = initialize_ai()

def build_client_prompt(counselor_message, client_goal, client_examples=None):
    """为AI构建扮演咨询者的提示词。"""
    persona = "你叫李森，你的舅舅可能患有遗传病（肯尼迪病），你现在非常担心，正在向遗传咨询师咨询。你的风格是有些焦虑，但很有礼貌，希望弄清楚所有问题。"
    context = f"咨询师刚刚对你说了：'{counselor_message}'"
    goal = client_goal
    
    reference_responses = ""
    if client_examples:
        examples_str = "\n".join([f"- {ex}" for ex in client_examples])
        reference_responses = f"""
# 参考回复 (Reference Responses)
这是你应该说的内容的一些参考例子。你可以选择其中一个，或者结合它们，或者根据这些例子生成一个相似的、自然的回答。
{examples_str}
"""

    constraints = "请只输出你作为咨询者（李森）的回答，语言要自然、口语化，不要包含任何额外的解释或标签，例如不要说"咨询者："或使用Markdown。"
    
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
    
    # 硬编码的背景事实，确保AI回答的一致性
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
    goal = f"现在，咨询师没有选择预设选项，而是向你提出了一个额外的问题：'{question}'"
    
    constraints = "请直接、简洁地回答咨询师提出的额外问题。你的回答必须严格基于以上的'已知事实'，不得与事实冲突。请只输出你作为咨询者（李森）的回答，语言要自然、口语化，不要包含任何额外的解释或标签。"
    
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

def get_next_node_id(node):
    """Safely gets the next node ID from a node's choices."""
    choices = node.get("choices", [])
    if choices and isinstance(choices, list) and len(choices) > 0 and 'nextNode' in choices[0]:
        return choices[0]['nextNode']
    return "END"

@app.route('/')
def index():
    """渲染主页面"""
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start_dialogue():
    """开始对话，返回第一个节点的信息"""
    global current_node_id, last_counselor_message
    current_node_id = "M1-01"
    node = dialogue_data.get(current_node_id)
    
    if not node:
        return jsonify({"error": "Start node M1-01 not found."}), 500

    # 第一个节点是咨询师，直接给出开场白和选项
    last_counselor_message = node.get('examples', ["你好，请坐。需要什么帮助吗？"])[0]
    
    # 移动到下一个节点，让AI扮演咨询者
    current_node_id = get_next_node_id(node)
    next_node = dialogue_data.get(current_node_id)

    if not next_node:
         return jsonify({
            "speaker": "咨询师",
            "dialogue": last_counselor_message,
            "node_info": { "id": "END", "goal": "对话结束" }
        })

    return jsonify({
        "speaker": "咨询师",
        "dialogue": last_counselor_message,
        "node_info": {
            "id": current_node_id,
            "goal": next_node.get('goal')
        }
    })

@app.route('/generate_client_response', methods=['POST'])
def generate_client_response():
    """根据咨询师的话，生成咨询者的回复"""
    global current_node_id
    if not model:
        return jsonify({"error": "AI model not initialized"}), 500

    node = dialogue_data.get(current_node_id)
    if not node:
        return jsonify({"error": "Invalid node ID"}), 400

    prompt = build_client_prompt(last_counselor_message, node.get('goal'), node.get('examples', []))
    try:
        response = model.generate_content(prompt)
        ai_response = response.text.strip()
        
        # 推进节点
        current_node_id = get_next_node_id(node)
        next_node = dialogue_data.get(current_node_id)

        return jsonify({
            "speaker": "咨询者",
            "dialogue": ai_response,
            "node_info": {
                "id": current_node_id,
                "goal": next_node.get('goal') if next_node else "对话结束",
                "options": next_node.get('examples', []) if next_node else []
            }
        })
    except Exception as e:
        return jsonify({"error": f"API call failed: {e}"}), 500

@app.route('/counselor_turn', methods=['POST'])
def counselor_turn():
    """处理咨询师的选择，并推进到下一个节点"""
    global current_node_id, last_counselor_message
    
    data = request.json
    selected_option = data.get('dialogue')
    
    if not selected_option:
        return jsonify({"error": "No dialogue provided"}), 400
        
    last_counselor_message = selected_option
    
    # 推进节点
    node = dialogue_data.get(current_node_id)
    current_node_id = get_next_node_id(node)
    next_node = dialogue_data.get(current_node_id)

    return jsonify({
        "speaker": "咨询师",
        "dialogue": last_counselor_message,
        "node_info": {
            "id": current_node_id,
            "goal": next_node.get('goal') if next_node else "对话结束"
        }
    })

@app.route('/ask_client_custom_question', methods=['POST'])
def ask_client_custom_question():
    """处理用户向咨询者（AI）提出的自定义问题，并返回原始选项。"""
    if not model:
        return jsonify({"error": "AI model not initialized"}), 500

    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({"error": "No question provided"}), 400

    # 获取当前节点，以便后续恢复选项
    current_node = dialogue_data.get(current_node_id)
    if not current_node:
        return jsonify({"error": "Invalid current node ID"}), 400

    # 构建对话历史，给AI更多上下文
    dialogue_history = f"咨询师：{last_counselor_message}"
    
    # 使用为李森定制的Prompt函数
    prompt = build_client_custom_response_prompt(question, dialogue_history)
    
    try:
        response = model.generate_content(prompt)
        ai_answer = response.text.strip()
        
        # 关键：不改变 current_node_id，对话流停在原地
        
        return jsonify({
            "speaker": "咨询者", 
            "dialogue": ai_answer,
            "is_custom": True, # 告诉前端这是个临时回答
            "options_to_restore": current_node.get('examples', []) # 返回原始选项
        })
    except Exception as e:
        return jsonify({"error": f"API call failed: {e}"}), 500

# Vercel需要这个函数作为入口点
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    # 获取端口号，支持环境变量设置
    port = int(os.environ.get('PORT', 5001))
    # 在生产环境中关闭debug模式
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
