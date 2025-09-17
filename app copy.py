import streamlit as st
import json
import random
import google.generativeai as genai

# --- 1. 常量管理 ---
# 将配置信息作为常量放在开头，方便管理
JSON_DATA_PATH = 'dialogue_output.json'
INITIAL_NODE_ID = 'M1-01'

# --- 2. 核心功能函数 ---

@st.cache_data
def load_dialogue_data(file_path: str) -> dict:
    """从JSON文件加载对话数据，并使用Streamlit缓存。"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"错误：找不到数据文件 {file_path}。请确保文件存在于正确的位置。")
        return {}

def initialize_state():
    """初始化或维持会话状态。"""
    if 'dialogue_id' not in st.session_state:
        st.session_state.dialogue_id = INITIAL_NODE_ID
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'feedback' not in st.session_state:
        st.session_state.feedback = None

def generate_counselor_response(node_data: dict, history: list) -> str:
    """根据节点数据和历史记录，调用AI生成咨询师的回复。"""
    # 此函数逻辑不变，保持原样
    formatted_examples = "\n- ".join(node_data.get('alternativePhrasings', []))
    prompt = f"""
# 角色与背景
你是一位资深的遗传咨询培训AI导师...（省略部分Prompt）
# 待评判内容
实习咨询师的自定义回复：“{history[-1]['content'] if history else '开始对话'}”
# 你的任务
...
# 输出格式
...
"""
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"调用AI API时发生错误: {e}")
        return "抱歉，AI服务暂时无法连接。"

def display_history():
    """遍历并显示当前的对话历史。"""
    for message in st.session_state.history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_choice(choice: dict):
    """处理用户的选择，更新历史和状态，并触发重运行。"""
    st.session_state.history.append({"role": "user", "content": choice["text"]})
    st.session_state.dialogue_id = choice["nextNode"]
    st.session_state.feedback = None # 清除上一轮的反馈
    st.rerun()

def display_choices(choices: list):
    """在界面上渲染并处理选项按钮的点击逻辑。"""
    if not choices:
        st.info("对话已结束。")
        return

    # 使用列来布局按钮，避免过长
    cols = st.columns(len(choices))
    for i, choice in enumerate(choices):
        with cols[i]:
            if st.button(choice["text"], key=f"choice_{i}"):
                handle_user_choice(choice)

# --- 3. 两种核心回合的处理函数 ---

def handle_training_turn(node_data: dict):
    """处理一个训练节点：显示选项、接收用户选择、给出反馈。"""
    st.markdown("---")
    st.info("**训练环节**：请您扮演咨询师，选择一个最合适的回答。")
    
    # 准备并打乱选项
    correct_choice = {
        "text": node_data.get("CorrectChoice_Text"),
        "is_correct": True,
        "nextNode": node_data.get("CorrectChoice_nextNode")
    }
    
    incorrect_choices = []
    for i in range(1, 3): # 假设最多2个错误选项
        if text := node_data.get(f"IncorrectChoice{i}_Text"):
            incorrect_choices.append({
                "text": text,
                "is_correct": False,
                "feedback": node_data.get(f"IncorrectChoice{i}_Feedback")
            })
            
    all_choices = [correct_choice] + incorrect_choices
    random.shuffle(all_choices)

    # 显示反馈信息（如果存在）
    if st.session_state.feedback:
        st.error(f"**指导建议：** {st.session_state.feedback}")

    # 显示并处理选项按钮
    for choice in all_choices:
        if st.button(choice["text"], key=choice["text"]):
            if choice["is_correct"]:
                st.session_state.history.append({"role": "assistant", "content": choice["text"]})
                handle_user_choice({"text": "（选择正确）", "nextNode": choice["nextNode"]})
            else:
                st.session_state.feedback = choice["feedback"]
                st.rerun()

def handle_ai_turn(node_data: dict):
    """处理一个AI回合：生成AI回复，然后显示用户的固定选项。"""
    with st.chat_message("assistant"):
        with st.spinner("AI正在思考..."):
            ai_response = generate_counselor_response(node_data, st.session_state.history)
        st.markdown(ai_response)
    
    st.session_state.history.append({"role": "assistant", "content": ai_response})
    
    # AI说完后，显示用户的选择
    user_choices = node_data.get("choices", [])
    display_choices(user_choices)

# --- 4. 主程序入口 ---

def main():
    """主应用函数。"""
    st.set_page_config(page_title="SBMA 遗传咨询模拟", layout="centered")
    st.title("SBMA 遗传咨询 AI 对话仿真系统")

    # 初始化
    dialogue_data = load_dialogue_data(JSON_DATA_PATH)
    if not dialogue_data:
        st.stop()
    initialize_state()

    # 获取当前节点数据
    current_id = st.session_state.dialogue_id
    node_data = dialogue_data.get(current_id)

    if not node_data:
        st.error(f"错误：在数据中找不到ID为 '{current_id}' 的对话节点。")
        st.stop()

    # 显示对话历史
    display_history()

    # 根据节点类型，决定是进入训练模式还是AI对话模式
    if node_data.get("IsTrainingNode") == "TRUE":
        handle_training_turn(node_data)
    else:
        # 在这个应用中，AI扮演的是咨询者，所以这里应该是用户的回合
        # 但根据您之前的需求，咨询师是由AI扮演的，所以我们调用handle_ai_turn
        # 这里假设`Character`列决定了谁说话
        if node_data.get("character") == "咨询师":
             handle_ai_turn(node_data)
        else: # 如果是咨询者的节点，直接显示他的选项
             user_choices = node_data.get("choices", [])
             display_choices(user_choices)


if __name__ == "__main__":
    main()