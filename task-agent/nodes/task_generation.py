"""
nodes/task_generation.py
任务生成节点：调用 SEA-LION 对话模型生成温暖、有人文关怀的任务描述
"""
from state.task_state import TaskAgentState
from utils.llm_factory import call_sealion


CARING_TONE_SYSTEM_PROMPT = """你是一位温暖、善良的健康伙伴，像好朋友一样和用户说话。
你的任务是为糖尿病患者的每日健康任务生成温暖的、有人文关怀的提示语。

关键原则：
1. 像朋友聊天，不要像医生命令
2. 用正面、鼓励的话语
3. 降低启动门槛（"就走10分钟就好"）
4. 强调即时好处（"这样做明天早上血糖会更稳"）
5. 适当用小 emoji 但不要过多
6. 结合新加坡本地语境（hawker centre, kopitiam, 本地食物）
7. 不超过50个字

只输出提示语文本，不要输出任何其他内容。"""


def task_generation_node(state: TaskAgentState) -> dict:
    """
    增强任务描述：如果任务缺少 caring_message，用 LLM 生成
    """
    tasks = state.get("generated_tasks", []) or []
    enhanced_tasks = []

    for task in tasks:
        # 如果已有 caring_message 且长度足够，保留原始的
        if task.get("caring_message") and len(task["caring_message"]) > 10:
            enhanced_tasks.append(task)
            continue

        # 用 LLM 为没有温暖话术的任务生成
        try:
            user_msg = (
                f"请为以下糖尿病管理任务生成温暖的提示语：\n"
                f"任务：{task.get('title', '')}\n"
                f"说明：{task.get('description', '')}\n"
                f"类别：{task.get('category', '')}"
            )
            caring_msg = call_sealion(
                system_prompt=CARING_TONE_SYSTEM_PROMPT,
                user_message=user_msg,
                reasoning=False,  # 对话模型，生成温暖文本
            )
            task["caring_message"] = caring_msg.strip()
        except Exception as e:
            print(f"[TaskGen] 话术生成失败: {e}")
            # 使用默认温暖话术
            task["caring_message"] = task.get("caring_message", "每一小步都是进步，加油！💪")

        enhanced_tasks.append(task)

    print(f"[TaskGen] 增强了 {len(enhanced_tasks)} 个任务的温暖话术")
    return {"generated_tasks": enhanced_tasks}
