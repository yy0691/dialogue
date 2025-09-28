import sys
import os

# 将项目根目录添加到sys.path，以便正确导入config
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, jsonify, session, Response, has_request_context
import json
import google.generativeai as genai
import textwrap
from config import get_google_api_key, get_api_config, get_available_providers, set_custom_siliconflow_config
# 移除了持久化存储，改为会话级别状态管理
import time
import re
import requests
from openai import OpenAI

# 显式指定模板和静态文件夹的路径
app = Flask(__name__, template_folder='./templates', static_folder='./static')
# 设置密钥以启用session。在生产环境中，应使用更安全的方式（如环境变量）管理密钥。
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_secure_development_secret_key')


# 全局变量仅用于存储不会改变的对话数据和AI模型实例
dialogue_data = {}
model = None
# 移除了持久化存储实例

class APIClient:
    """API客户端抽象类，支持多种API提供商"""
    
    def __init__(self, provider="gemini", api_key=None, custom_config=None):
        self.provider = provider
        self.api_key = api_key
        self.custom_config = custom_config or {}
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化API客户端"""
        try:
            if self.provider == "gemini":
                if self.api_key:
                    genai.configure(api_key=self.api_key)
                    self.client = genai.GenerativeModel('gemini-1.5-flash')
                else:
                    raise Exception("Gemini API密钥未提供")
            elif self.provider == "siliconflow":
                if self.api_key:
                    base_url = self.custom_config.get('base_url', 'https://api.siliconflow.cn/v1')
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url=base_url
                    )
                else:
                    raise Exception("硅基流动API密钥未提供")
            elif self.provider == "custom":
                if self.api_key:
                    base_url = self.custom_config.get('base_url', 'https://api.openai.com/v1')
                    self.client = OpenAI(
                        api_key=self.api_key,
                        base_url=base_url
                    )
                else:
                    raise Exception("自定义API密钥未提供")
            else:
                raise Exception(f"不支持的API提供商: {self.provider}")
        except Exception as e:
            print(f"API客户端初始化失败: {e}")
            self.client = None
            raise
    
    def generate_content(self, prompt, stream=False):
        """生成内容的统一接口"""
        if not self.client:
            raise Exception("API客户端未初始化")
        
        if self.provider == "gemini":
            return self.client.generate_content(prompt, stream=stream)
        elif self.provider in ["siliconflow", "custom"]:
            if self.provider == "siliconflow":
                model_name = self.custom_config.get('model', 'qwen/Qwen2.5-7B-Instruct')
            else:  # custom
                model_name = self.custom_config.get('model', 'gpt-3.5-turbo')
            
            messages = [{"role": "user", "content": prompt}]
            
            if stream:
                return self._openai_compatible_stream(messages, model_name)
            else:
                try:
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        temperature=0.7,
                        max_tokens=2000
                    )
                    
                    # 检查响应是否有效
                    if hasattr(response, 'choices') and len(response.choices) > 0:
                        # 创建一个类似Gemini响应的对象
                        class OpenAICompatibleResponse:
                            def __init__(self, text):
                                self.text = text
                        
                        return OpenAICompatibleResponse(response.choices[0].message.content)
                    else:
                        raise Exception(f"无效的API响应格式: {response}")
                        
                except Exception as e:
                    error_msg = str(e)
                    # 检查是否返回了HTML页面
                    if "<!doctype html>" in error_msg.lower() or "<html" in error_msg.lower():
                        raise Exception("API地址错误：服务器返回了网页而不是API响应。请检查API地址是否正确。")
                    elif "unauthorized" in error_msg.lower() or "401" in error_msg:
                        raise Exception("API密钥无效或已过期")
                    elif "not found" in error_msg.lower() or "404" in error_msg:
                        raise Exception("API地址不存在，请检查URL是否正确")
                    elif "forbidden" in error_msg.lower() or "403" in error_msg:
                        raise Exception("API访问被拒绝，请检查密钥权限")
                    else:
                        raise Exception(f"API调用失败: {error_msg}")
    
    def _openai_compatible_stream(self, messages, model_name):
        """OpenAI兼容API流式响应处理"""
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            # 创建一个生成器来模拟Gemini的流式响应
            class OpenAICompatibleStreamResponse:
                def __init__(self, stream_response):
                    self.stream_response = stream_response
                
                def __iter__(self):
                    try:
                        for chunk in self.stream_response:
                            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                                if chunk.choices[0].delta.content:
                                    # 创建一个类似Gemini chunk的对象
                                    class OpenAICompatibleChunk:
                                        def __init__(self, text):
                                            self.text = text
                                    yield OpenAICompatibleChunk(chunk.choices[0].delta.content)
                    except Exception as e:
                        print(f"流式响应处理错误: {e}")
            return OpenAICompatibleStreamResponse(response)
        except Exception as e:
            raise Exception(f"流式API调用失败: {str(e)}")

def load_dialogue_data(filename="dialogue_output_2.json"):
    """加载对话JSON数据，如果尚未加载。"""
    global dialogue_data
    if not dialogue_data:
        try:
            # 尝试多个可能的文件路径
            possible_paths = [
                os.path.join(os.path.dirname(__file__), filename),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), filename),
                filename
            ]
            
            for file_path in possible_paths:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        dialogue_data = json.load(f)
                    print(f"成功加载对话数据: {file_path}")
                    return
            # 如果所有路径都失败，创建一个基本的数据结构
            print("警告: 无法找到对话数据文件，使用默认数据")
            dialogue_data = {
                "M1-01": {
                    "character": "咨询师",
                    "goal": "开始对话",
                    "examples": ["你好，请坐。"],
                    "choices": [{"nextNode": "END"}]
                }
            }
        except Exception as e:
            print("错误: 加载对话文件失败: " + str(e))
            dialogue_data = {}

def get_api_key():
    """从环境变量中获取Google API密钥。"""
    try:
        return get_google_api_key()
    except ValueError as e:
        print("错误: " + str(e))
        raise

def get_model_for_session():
    """获取当前会话的AI模型实例，支持动态API密钥和多种提供商"""
    global model
    
    # 检查是否在请求上下文中
    if not has_request_context():
        # 如果不在请求上下文中，直接返回默认模型
        return model
    
    # 检查会话中是否有自定义配置
    try:
        session_provider = session.get('api_provider', 'gemini')
        session_api_key = session.get('api_key')
        session_config = session.get('api_config', {})
        
        if session_api_key:
            try:
                # 使用会话中的配置创建临时模型
                api_client = APIClient(
                    provider=session_provider,
                    api_key=session_api_key,
                    custom_config=session_config
                )
                return api_client
            except Exception as e:
                print(f"使用会话API配置失败: {e}")
                # 如果会话API配置失败，回退到默认模型
    except RuntimeError as e:
        # 处理会话访问错误
        print(f"会话访问失败: {e}")
    
    # 使用默认模型
    return model

def initialize_ai():
    """初始化AI模型"""
    global model
    try:
        api_key = get_api_key()
        if api_key:
            print(f"正在使用API密钥: {api_key[:10]}...")  # 只显示前10个字符
            model = APIClient(provider="gemini", api_key=api_key)
            print("AI模型初始化成功")
        else:
            print("警告: 未找到API密钥，将在运行时初始化")
            model = None
    except Exception as e:
        print("AI初始化失败: " + str(e))
        print(f"错误类型: {type(e).__name__}")
        model = None

# 延迟初始化，避免在导入时就执行
def ensure_initialized():
    """确保数据和AI已初始化"""
    global dialogue_data, model
    if not dialogue_data:
        load_dialogue_data()
    if model is None:
        try:
            initialize_ai()
        except:
            pass  # 静默处理初始化失败

# 在应用启动时加载数据
load_dialogue_data()

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

def recognize_counselor_intent(counselor_question, node_goal, history_context, model_instance):
    """识别咨询师问题的意图类型"""
    if not model_instance:
        return "RAPPORT_BUILDING"  # 默认返回
    
    intent_prompt = f"""
    # 任务说明
    你是一个专业的对话意图识别系统。请分析咨询师提出的问题，判断其意图类型。
    
    # 当前对话目标
    {node_goal}
    
    # 对话历史上下文
    {history_context}
    
    # 咨询师的问题
    "{counselor_question}"
    
    # 意图分类标准
    请根据以下标准判断咨询师问题的意图类型：
    
    1. GOAL_ACHIEVED - 目标达成：
       - 咨询师的问题直接针对当前对话目标
       - 问题有助于推进对话进程
       - 符合当前阶段的咨询重点
    
    2. PARTIAL_ACHIEVEMENT - 部分达成：
       - 咨询师的问题与目标相关但不够深入
       - 需要进一步细化或补充
       - 方向正确但可以更具体
    
    3. RAPPORT_BUILDING - 关系建立：
       - 咨询师关注咨询者的情感状态
       - 试图建立信任和理解
       - 表达共情或提供情感支持
    
    4. OFF_TOPIC - 偏离主题：
       - 咨询师的问题与当前对话目标无关
       - 转向了其他不相关的话题
       - 可能会分散注意力或偏离咨询重点
    
    # 输出要求
    请只输出以下四个选项中的一个：GOAL_ACHIEVED、PARTIAL_ACHIEVEMENT、RAPPORT_BUILDING、OFF_TOPIC
    不要包含任何其他解释或文字。
    """
    
    try:
        response = model_instance.generate_content(intent_prompt.strip())
        if response.text:
            intent = response.text.strip().upper()
            if intent in ["GOAL_ACHIEVED", "PARTIAL_ACHIEVEMENT", "RAPPORT_BUILDING", "OFF_TOPIC"]:
                return intent
    except Exception as e:
        print(f"意图识别失败: {e}")
    
    return "RAPPORT_BUILDING"  # 默认返回

def generate_system_feedback(intent, counselor_question, client_response, node_goal, current_node, model_instance):
    """根据咨询师问题的意图和咨询者回复，生成针对咨询师的系统指导反馈"""
    if not model_instance:
        return {
            "intent": intent,
            "feedback": "系统反馈暂不可用",
            "suggestion": "",
            "should_advance": False
        }
    
    # 根据意图类型构建不同的反馈提示词
    if intent == "GOAL_ACHIEVED":
        feedback_prompt = f"""
        # 情况分析
        咨询师的问题很好地针对了当前对话目标："{node_goal}"
        
        咨询师问题："{counselor_question}"
        咨询者回复："{client_response}"
        
        # 任务要求
        请为咨询师提供针对咨询者回复的指导建议，包括：
        1. 分析咨询者回复的关键信息和情感状态
        2. 评价这个问题如何有效推进了咨询进程
        3. 建议如何更好地跟进和深化咨询者的回答
        4. 下一步的咨询策略建议
        
        # 输出格式
        反馈：[对咨询者回复的分析和问题效果的评价]
        建议：[如何跟进咨询者回复的具体策略]
        """
        should_advance = False
        
    elif intent == "PARTIAL_ACHIEVEMENT":
        feedback_prompt = f"""
        # 情况分析
        咨询师的问题与目标相关但可以更深入。当前目标："{node_goal}"
        
        咨询师问题："{counselor_question}"
        咨询者回复："{client_response}"
        
        # 任务要求
        请为咨询师提供针对咨询者回复的改进指导，包括：
        1. 分析咨询者回复透露的信息
        2. 指出当前问题的积极方面和不足
        3. 建议如何基于咨询者的回复提出更深入的问题
        4. 如何更好地聚焦核心议题
        
        # 输出格式
        反馈：[对咨询者回复的分析和问题效果的评价]
        建议：[基于回复内容的深化提问策略]
        """
        should_advance = False
        
    elif intent == "RAPPORT_BUILDING":
        feedback_prompt = f"""
        # 情况分析
        咨询师正在关注咨询者的情感状态，建立关系。当前目标："{node_goal}"
        
        咨询师问题："{counselor_question}"
        咨询者回复："{client_response}"
        
        # 任务要求
        请为咨询师提供关系建立的指导，包括：
        1. 分析咨询者回复中的情感线索和信任度
        2. 评价关系建立的效果
        3. 建议如何在建立关系的基础上逐步推进咨询目标
        4. 平衡情感支持和专业咨询的策略
        
        # 输出格式
        反馈：[对咨询者情感状态和关系建立效果的分析]
        建议：[如何基于当前关系状态推进咨询的策略]
        """
        should_advance = False
        
    else:  # OFF_TOPIC
        feedback_prompt = f"""
        # 情况分析
        咨询师的问题偏离了当前对话目标："{node_goal}"
        
        咨询师问题："{counselor_question}"
        咨询者回复："{client_response}"
        
        # 任务要求
        请为咨询师提供重新聚焦的建议，包括：
        1. 分析咨询者回复的内容和态度
        2. 温和地指出问题与目标的偏离及其影响
        3. 建议如何利用咨询者的回复重新引导到咨询重点
        4. 提供更符合目标的后续问题建议
        
        # 输出格式
        反馈：[对偏离影响和咨询者回复的分析]
        建议：[基于回复内容重新聚焦的具体策略]
        """
        should_advance = False
    
    try:
        response = model_instance.generate_content(feedback_prompt.strip())
        if response.text:
            feedback_text = response.text.strip()
            print(f"AI生成的原始反馈文本: {feedback_text}")  # 调试信息
            
            # 尝试解析反馈和建议
            lines = feedback_text.split('\n')
            feedback = ""
            suggestion = ""
            
            for line in lines:
                if line.startswith('反馈：'):
                    feedback = line.replace('反馈：', '').strip()
                elif line.startswith('建议：'):
                    suggestion = line.replace('建议：', '').strip()
            
            print(f"解析后的反馈: {feedback}")  # 调试信息
            print(f"解析后的建议: {suggestion}")  # 调试信息
            
            if not feedback:
                feedback = feedback_text[:100] + "..." if len(feedback_text) > 100 else feedback_text
            
            # 如果建议为空，使用整个文本作为建议
            if not suggestion and feedback_text:
                suggestion = "请参考以上分析调整咨询策略"
            
            return {
                "intent": intent,
                "feedback": feedback,
                "suggestion": suggestion,
                "should_advance": should_advance
            }
    except Exception as e:
        print(f"系统反馈生成失败: {e}")
    
    # 默认反馈
    return {
        "intent": intent,
        "feedback": "正在分析咨询师的问题和咨询者的回复...",
        "suggestion": "请根据对话情况灵活调整提问策略",
        "should_advance": False
    }

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

@app.route('/sessions')
def sessions():
    """渲染会话管理页面"""
    return render_template('sessions.html')

# 移除了会话列表API，改为会话级别状态管理

@app.route('/start', methods=['POST'])
def start_dialogue():
    """开始或切换对话阶段。如果阶段已存在，则恢复；否则，创建新阶段。"""
    data = request.json or {}
    start_node_id = data.get('node_id', 'M1-01')
    stage = get_stage_from_node_id(start_node_id)
    
    # 设置当前活跃阶段
    session['active_stage'] = stage
    
    if 'dialogue_states' not in session:
        session['dialogue_states'] = {}
    
    states = session.get('dialogue_states', {})
    
    if stage not in states:
        # --- 初始化新阶段 ---
        node = dialogue_data.get(start_node_id)
        if not node:
            return jsonify({"error": "Start node " + start_node_id + " not found."}), 404

        # 检查第一个节点的角色
        character = node.get('character', '')
        message = node.get('examples', ["你好，请坐。"])[0]
        next_node_id = get_next_node_id(node)
        
        if character == '咨询师':
            # 咨询师节点：显示选项让用户选择
            states[stage] = {
                "current_node_id": start_node_id,
                "last_counselor_message": "",  # 还没有咨询师消息
                "history": []
            }
            session['dialogue_states'] = states
            session.modified = True
            
            return jsonify({
                "session_id": "session_" + str(id(session)),
                "node_info": {
                    "id": start_node_id,
                    "goal": node.get('goal', ''),
                    "options": node.get('examples', [])
                }
            })
        else:
            # 咨询者节点：直接显示咨询者的话
            states[stage] = {
                "current_node_id": next_node_id,
                "last_counselor_message": "",
                "history": [{"speaker": "咨询者", "dialogue": message}]
            }
            session['dialogue_states'] = states
            session.modified = True
            
            next_node = dialogue_data.get(next_node_id)
            return jsonify({
                "speaker": "咨询者",
                "dialogue": message,
                "session_id": "session_" + str(id(session)),
                "node_info": {
                    "id": next_node_id,
                    "goal": next_node.get('goal') if next_node else "对话结束",
                    "options": next_node.get('examples', []) if next_node else []
                }
            })
    else:
        # --- 恢复现有阶段 ---
        state = states[stage]
        current_node_id = state['current_node_id']
        node = dialogue_data.get(current_node_id)
        
        return jsonify({
            "resuming": True,
            "session_id": "session_" + str(id(session)),  # 简单的会话标识
            "history": state.get('history', []),
            "node_info": {
                "id": current_node_id,
                "goal": node.get('goal') if node else "对话结束",
                "options": node.get('examples', []) if node else []
            }
        })

@app.route('/generate_client_response', methods=['POST'])
def generate_client_response():
    """根据咨询师的话，使用AI生成咨询者的回复。"""
    current_model = get_model_for_session()
    if not current_model:
        return jsonify({"error": "AI model not initialized"}), 500

    active_stage = session.get('active_stage')
    if not active_stage or 'dialogue_states' not in session or active_stage not in session['dialogue_states']:
        return jsonify({"error": "No active dialogue session."}, 400)
    
    state = session['dialogue_states'][active_stage]
    current_node_id = state['current_node_id']
    last_counselor_message = state['last_counselor_message']
    current_node = dialogue_data.get(current_node_id)
    if not current_node:
        return jsonify({"error": "Invalid node ID"}), 400

    # 获取下一个节点（应该是咨询者节点）
    next_node_id = get_next_node_id(current_node)
    next_node = dialogue_data.get(next_node_id)
    if not next_node:
        return jsonify({"error": "Next node not found"}), 400

    # 检查下一个节点是否是咨询者节点
    if next_node.get('character') != '咨询者':
        return jsonify({"error": "Next node is not a client node"}), 400
        
    # 如果没有咨询师消息，使用当前节点的示例
    if not last_counselor_message:
        last_counselor_message = current_node.get('examples', ["你好"])[0]

    # 使用AI生成咨询者回复，参考JSON中的目标和示例
    prompt = build_client_prompt(last_counselor_message, next_node.get('goal'), next_node.get('examples', []))
    
    try:
        response = current_model.generate_content(prompt)
        if not response.text:
            return jsonify({"error": "AI返回了空响应"}), 500
            
        ai_response = response.text.strip()
        
        # 推进到咨询者节点后的下一个节点
        client_next_node_id = get_next_node_id(next_node)
        client_next_node = dialogue_data.get(client_next_node_id)

        # 更新状态
        state['current_node_id'] = client_next_node_id
        state['history'].append({"speaker": "咨询者", "dialogue": ai_response})
        session.modified = True

        return jsonify({
            "speaker": "咨询者",
            "dialogue": ai_response,
            "session_id": "session_" + str(id(session)),
            "node_info": {
                "id": client_next_node_id,
                "goal": client_next_node.get('goal') if client_next_node else "对话结束",
                "options": client_next_node.get('examples', []) if client_next_node else []
            }
        })
    except Exception as e:
        return jsonify({"error": "API call failed: " + str(e)}), 500

@app.route('/generate_client_response_stream', methods=['POST'])
def generate_client_response_stream():
    """流式生成咨询者的回复，并提供系统指导反馈。"""
    current_model = get_model_for_session()
    if not current_model:
        return jsonify({"error": "AI model not initialized"}), 500

    active_stage = session.get('active_stage')
    if not active_stage or 'dialogue_states' not in session or active_stage not in session['dialogue_states']:
        return jsonify({"error": "No active dialogue session."}), 400
    
    state = session['dialogue_states'][active_stage]
    current_node_id = state['current_node_id']
    last_counselor_message = state['last_counselor_message']
    current_node = dialogue_data.get(current_node_id)
    if not current_node:
        return jsonify({"error": "Invalid node ID"}), 400
    
    # 获取下一个节点（应该是咨询者节点）
    next_node_id = get_next_node_id(current_node)
    next_node = dialogue_data.get(next_node_id)
    if not next_node:
        return jsonify({"error": "Next node not found"}), 400
        
    # 检查下一个节点是否是咨询者节点
    if next_node.get('character') != '咨询者':
        return jsonify({"error": "Next node is not a client node"}), 400
        
    # 如果没有咨询师消息，使用当前节点的示例
    if not last_counselor_message:
        last_counselor_message = current_node.get('examples', ["你好"])[0]

    def generate_stream():
        try:
            # 使用下一个节点（咨询者节点）的目标和示例
            prompt = build_client_prompt(last_counselor_message, next_node.get('goal'), next_node.get('examples', []))
            print(f"生成的流式提示词: {prompt[:200]}...")
            
            # 使用流式生成
            response = current_model.generate_content(prompt, stream=True)
            
            full_response = ""
            
            # 发送开始事件
            yield f"data: {json.dumps({'type': 'start', 'speaker': '咨询者'})}\n\n"
            
            # 流式发送AI回复
            for chunk in response:
                if chunk.text:
                    chunk_text = chunk.text
                    full_response += chunk_text
                    
                    # 发送文本块
                    yield f"data: {json.dumps({'type': 'chunk', 'text': chunk_text})}\n\n"
                    
                    # 添加一点延迟，让打字效果更自然
                    time.sleep(0.05)
            
            print(f"流式AI响应完成: {full_response[:100]}...")
            
            # 推进到咨询者回复节点后的下一个节点
            client_next_node_id = get_next_node_id(next_node)
            client_next_node = dialogue_data.get(client_next_node_id)
            
            # 在应用上下文中更新状态
            with app.app_context():
                # 检查是否有请求上下文
                if has_request_context():
                    # 更新状态
                    state['current_node_id'] = client_next_node_id
                    state['history'].append({"speaker": "咨询者", "dialogue": full_response})
                    session.modified = True
                else:
                    print("警告: 流式生成器中没有请求上下文，无法更新会话状态")
            
            # 发送完成事件，包含节点信息（不包含系统反馈）
            completion_data = {
                'type': 'complete',
                'full_text': full_response,
                'session_id': f"session_{int(time.time())}",  # 使用时间戳作为会话标识
                'node_info': {
                    'id': client_next_node_id,
                    'goal': client_next_node.get('goal') if client_next_node else "对话结束",
                    'options': client_next_node.get('examples', []) if client_next_node else []
                }
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            print(f"流式API调用失败: {str(e)}")
            error_data = {'type': 'error', 'message': f"API call failed: {str(e)}"}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )

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
    # 保持在当前节点，等待生成咨询者回复
    # state['current_node_id'] = next_node_id  # 暂时不推进
    session.modified = True

    # 会话级别状态已自动保存在Flask session中

    return jsonify({
        "speaker": "咨询师",
        "dialogue": selected_option,
        "session_id": "session_" + str(id(session)),  # 简单的会话标识
        "node_info": {
            "id": current_node_id,  # 返回当前节点信息
            "goal": node.get('goal') if node else "对话结束",
            "trigger_client_response": True  # 标记需要生成咨询者回复
        }
    })

@app.route('/get_api_providers', methods=['GET'])
def get_api_providers():
    """获取所有可用的API提供商"""
    try:
        providers = get_available_providers()
        provider_info = {}
        
        for provider in providers:
            config = get_api_config(provider)
            provider_info[provider] = {
                "name": config["name"],
                "default_model": config["default_model"]
            }
        
        return jsonify({
            "success": True,
            "providers": provider_info,
            "current_provider": session.get('api_provider', 'gemini')
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取提供商信息失败: {str(e)}"
        })

@app.route('/test_api_key', methods=['POST'])
def test_api_key():
    """测试API密钥是否有效"""
    try:
        data = request.json or {}
        api_key = data.get('api_key', '').strip()
        provider = data.get('provider', 'gemini')
        custom_config = data.get('custom_config', {})
        
        if not api_key:
            return jsonify({"success": False, "message": "API密钥不能为空"}), 400
        
        # 创建测试客户端
        try:
            test_client = APIClient(
                provider=provider,
                api_key=api_key,
                custom_config=custom_config
            )
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"客户端初始化失败: {str(e)}"
            })
        
        # 发送一个简单的测试请求
        try:
            test_prompt = "请回复'测试成功'"
            response = test_client.generate_content(test_prompt)
            
            if response and hasattr(response, 'text') and response.text:
                return jsonify({
                    "success": True, 
                    "message": f"{provider} API密钥有效，连接成功！"
                })
            else:
                return jsonify({
                    "success": False, 
                    "message": "API响应为空或格式错误"
                })
        except Exception as e:
            error_msg = str(e)
            print(f"API测试失败详细信息: {error_msg}")  # 服务器日志
            return jsonify({
                "success": False, 
                "message": f"API测试失败: {error_msg}"
            })
            
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "invalid" in error_msg.lower():
            return jsonify({
                "success": False, 
                "message": "API密钥无效"
            })
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            return jsonify({
                "success": False, 
                "message": "API配额已用完或达到限制"
            })
        else:
            return jsonify({
                "success": False, 
                "message": f"测试失败: {error_msg}"
            })

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    """设置当前会话的API密钥和提供商"""
    try:
        data = request.json or {}
        api_key = data.get('api_key', '').strip()
        provider = data.get('provider', 'gemini')
        custom_config = data.get('custom_config', {})
        
        if not api_key:
            return jsonify({"success": False, "message": "API密钥不能为空"}), 400
        
        # 将API配置存储在会话中
        session['api_key'] = api_key
        session['api_provider'] = provider
        session['api_config'] = custom_config
        session.modified = True
        
        # 如果是硅基流动，更新全局配置
        if provider == 'siliconflow':
            set_custom_siliconflow_config(
                api_key=api_key,
                base_url=custom_config.get('base_url'),
                model=custom_config.get('model')
            )
        
        return jsonify({
            "success": True, 
            "message": f"{provider} API配置已设置"
        })
        
    except Exception as e:
        return jsonify({
            "success": False, 
            "message": f"设置失败: {str(e)}"
        }), 500

@app.route('/ask_client_custom_question', methods=['POST'])
def ask_client_custom_question():
    """处理用户向咨询者（AI）提出的自定义问题，并提供意图识别和系统反馈。"""
    current_model = get_model_for_session()
    if not current_model:
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

    # 生成AI咨询者的回答
    history_str = "\n".join([f"{item['speaker']}: {item['dialogue']}" for item in state.get('history', [])])
    prompt = build_client_custom_response_prompt(question, history_str)
    
    try:
        print(f"自定义问题提示词: {prompt[:200]}...")
        print("正在调用Google API处理自定义问题...")
        response = current_model.generate_content(prompt)
        print(f"自定义问题API响应状态: {response}")
        
        if not response.text:
            print("警告: 自定义问题API返回了空响应")
            return jsonify({"error": "AI返回了空响应"}), 500
            
        ai_answer = response.text.strip()
        print(f"自定义问题AI响应: {ai_answer[:100]}...")
        
        # === 对咨询师问题进行意图识别 ===
        intent = recognize_counselor_intent(question, current_node.get('goal', ''), history_str, current_model)
        print(f"咨询师问题意图识别: {intent}")
        
        # === 生成针对咨询师的系统指导反馈（基于问题意图和咨询者回复）===
        system_feedback = generate_system_feedback(intent, question, ai_answer, current_node.get('goal', ''), current_node, current_model)
        print(f"系统反馈: {system_feedback}")
        
        # === 返回AI回答和系统反馈 ===
        return jsonify({
            "speaker": "咨询者", 
            "dialogue": ai_answer,  # 咨询者（李森）的回复
            "system_feedback": system_feedback,  # 给咨询师的指导反馈
            "is_custom": True,
            "options_to_restore": current_node.get('examples', [])
        })
    except Exception as e:
        print(f"自定义问题API调用失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "API call failed: " + str(e)}), 500

@app.route('/debug_api', methods=['POST'])
def debug_api():
    """调试API配置"""
    try:
        data = request.json or {}
        provider = data.get('provider', 'gemini')
        api_key = data.get('api_key', '').strip()
        custom_config = data.get('custom_config', {})
        
        debug_info = {
            "provider": provider,
            "api_key_length": len(api_key) if api_key else 0,
            "custom_config": custom_config,
            "openai_available": False,
            "genai_available": False
        }
        
        # 检查依赖
        try:
            import openai
            debug_info["openai_available"] = True
            debug_info["openai_version"] = openai.__version__
        except ImportError as e:
            debug_info["openai_error"] = str(e)
        
        try:
            import google.generativeai as genai
            debug_info["genai_available"] = True
        except ImportError as e:
            debug_info["genai_error"] = str(e)
        
        # 测试客户端创建
        try:
            if provider in ["siliconflow", "custom"] and not debug_info["openai_available"]:
                raise Exception("OpenAI库未安装，无法使用硅基流动或自定义供应商")
            
            test_client = APIClient(
                provider=provider,
                api_key=api_key,
                custom_config=custom_config
            )
            debug_info["client_created"] = True
            debug_info["client_type"] = type(test_client.client).__name__
            
        except Exception as e:
            debug_info["client_created"] = False
            debug_info["client_error"] = str(e)
        
        return jsonify({
            "success": True,
            "debug_info": debug_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

# 本地开发时运行
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)