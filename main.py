import json
import os
import google.generativeai as genai
import textwrap

def load_dialogue_data(filename="dialogue_output.json"):
    """加载并返回对话JSON数据。"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误: 未找到对话文件 {filename} 。")
        print("请确保已将 'dialogue_source.csv' 转换为 'dialogue_output.json' 。")
        exit()
    except json.JSONDecodeError:
        print(f"错误: {filename} 文件格式不正确，无法解析。")
        exit()

def get_api_key():
    """从环境变量中获取Google API密钥。"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("错误: 环境变量 GOOGLE_API_KEY 未设置。")
        print("请设置您的Google API密钥后重试。")
        exit()
    return api_key

def build_client_prompt(counselor_message, client_goal):
    """为AI构建扮演咨询者的提示词。"""
    persona = "你叫李森，你的舅舅可能患有遗传病（肯尼迪病），你现在非常担心，正在向遗传咨询师咨询。你的风格是有些焦虑，但很有礼貌，希望弄清楚所有问题。"
    
    context = f"咨询师刚刚对你说了：'{counselor_message}'"
    
    goal = client_goal
    
    constraints = "请只输出你作为咨询者（李森）的回答，语言要自然、口语化，不要包含任何额外的解释或标签，例如不要说“咨询者：”或使用Markdown。"

    prompt = f"""
    # 角色设定 (Persona)
    {persona}

    # 对话上下文 (Context)
    {context}

    # 本轮对话核心任务 (Goal)
    {goal}

    # 输出要求 (Constraints)
    {constraints}
    """
    return textwrap.dedent(prompt).strip()

def main():
    """主对话循环。"""
    # 配置API
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # 加载数据并初始化
    dialogue_data = load_dialogue_data()
    current_node_id = "M1-01"
    last_counselor_message = "你好，请坐。需要什么帮助吗？" # 初始问候语

    print("--- SBMA 遗传咨询 AI 对话仿真系统 ---")
    print("对话开始...")
    print(f"咨询师: {last_counselor_message}")


    while current_node_id and current_node_id.upper() != "END":
        if current_node_id not in dialogue_data:
            print(f"错误: 找不到ID为 '{current_node_id}' 的对话节点。对话终止。")
            break

        node = dialogue_data[current_node_id]
        character = node.get("character")

        print("\n" + "="*50)
        print(f"当前节点: {current_node_id} | 角色: {character}")
        print(f"节点目标: {node.get('goal')}")
        print("="*50)

        # 1. 判断角色并执行相应操作
        if character == "咨询师":
            options = node.get('examples', [])
            if not options:
                print("该咨询师节点没有预设回复，请输入自定义内容。")
                last_counselor_message = input("请输入咨询师的回复 > ")
            else:
                print("\n请为咨询师选择一个回复或输入自定义内容：")
                for i, option in enumerate(options):
                    print(f"  {i + 1}: {option}")
                print(f"  {len(options) + 1}: 输入自定义内容")

                # 获取用户选择
                selected_index = -1
                while True:
                    try:
                        user_input = input("请选择 > ")
                        selected_index = int(user_input) - 1
                        if 0 <= selected_index < len(options):
                            last_counselor_message = options[selected_index]
                            break
                        elif selected_index == len(options):
                            last_counselor_message = input("请输入您的回复 > ")
                            break
                        else:
                            print(f"无效选择。请输入 1 到 {len(options) + 1} 之间的数字。")
                    except ValueError:
                        print("无效输入。请输入一个数字。")
            
            print(f"\n咨询师 (您已选择/输入): {last_counselor_message}")

        elif character == "咨询者":
            prompt = build_client_prompt(last_counselor_message, node.get('goal'))
            try:
                print("\n[AI正在生成咨询者的回复...]")
                response = model.generate_content(prompt)
                ai_response = response.text.strip()
                print(f"咨询者 (AI): {ai_response}")
            except Exception as e:
                print(f"\n调用API时出错: {e}")
                print("将使用预设的第一个示例作为备用回答。")
                ai_response = node.get('examples', ["无法生成回答，请检查API设置。"])[0]
                print(f"咨询者 (备用): {ai_response}")
        
        else: # 系统信息等
            system_message = node.get('examples', ["..."])[0]
            print(f"系统: {system_message}")

        # 2. 推进到下一个节点
        # 在这个线性对话流中，我们总是自动前进到nextNode
        choices = node.get("choices", [])
        if choices and 'nextNode' in choices[0]:
            current_node_id = choices[0]['nextNode']
        else:
            print("未定义后续走向，对话结束。")
            break

    print("\n--- 对话已结束，感谢使用 ---")

if __name__ == "__main__":
    main()
