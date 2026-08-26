"""
LangGraph Swarm 模式 Demo

Swarm 模式的核心特点：
- 没有中央 Supervisor，每个 Agent 自主决定是否将控制权移交给其他 Agent
- Agent 之间通过 handoff 工具直接互相交接，形成扁平的去中心化拓扑
- 每个 Agent 专注于自己的领域，完成工作后可以交给下一个 Agent 或直接返回结果

场景：旅行规划助手 Swarm
- travel_agent：旅行规划助手（入口 Agent），负责整体行程规划
- weather_agent：天气查询助手，负责提供目的地天气信息
- budget_agent：预算管理助手，负责估算旅行费用
- Agent 之间可以自由 handoff：travel → weather → budget → travel ...

工作流示例：
  用户："我想去北京旅游，帮我了解一下天气和预算"
  → travel_agent 接收，规划行程后 handoff 给 weather_agent
  → weather_agent 查询天气后 handoff 给 budget_agent
  → budget_agent 估算费用后 handoff 回 travel_agent
  → travel_agent 整合所有信息，输出最终方案
"""

import os
import sys
from typing import Annotated

# Windows 下设置 stdout 编码为 UTF-8，避免 emoji 等字符输出报错
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from langchain_core.tools import tool, InjectedToolCallId
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import InjectedState
from langgraph.types import Command

# ============================================================
# 1. 初始化 LLM
# ============================================================

load_dotenv()

# 使用智谱 GLM-4.7（OpenAI 兼容接口）
llm = ChatOpenAI(
    model="glm-4.7",
    api_key=os.getenv("GLM_API_KEY"),
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    temperature=0,
)


# ============================================================
# 2. Handoff 工具：实现 Agent 之间的直接移交
# ============================================================

def create_handoff_tool(*, agent_name: str, description: str | None = None):
    """
    创建 handoff 工具，用于将控制权直接移交给另一个 Agent。

    Swarm 模式的关键：Agent 自主调用此工具，直接跳转到目标 Agent，
    不需要经过中央 Supervisor 调度。

    使用 InjectedState 和 InjectedToolCallId 这两个「魔法」注解：
    - InjectedState：框架自动注入当前 state，不需要 LLM 填充
    - InjectedToolCallId：框架自动注入当前 tool_call_id，不需要 LLM 填充
    """
    name = f"transfer_to_{agent_name}"
    description = description or f"将任务移交给 {agent_name} 处理。"

    @tool(name, description=description)
    def handoff_tool(
        state: Annotated[MessagesState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        # 构造一条 ToolMessage，告知移交成功
        tool_message = {
            "role": "tool",
            "content": f"已成功移交给 {agent_name}",
            "name": name,
            "tool_call_id": tool_call_id,
        }
        # 返回 Command，直接导航到目标 Agent 节点
        return Command(
            goto=agent_name,
            update={**state, "messages": state["messages"] + [tool_message]},
            graph=Command.PARENT,  # 在父图（Swarm 图）中导航
        )

    return handoff_tool


# 创建各 Agent 之间的 handoff 工具
transfer_to_travel = create_handoff_tool(
    agent_name="travel_agent",
    description="将任务移交给旅行规划助手，用于整体行程规划和信息汇总。",
)

transfer_to_weather = create_handoff_tool(
    agent_name="weather_agent",
    description="将任务移交给天气查询助手，用于获取目的地天气信息。",
)

transfer_to_budget = create_handoff_tool(
    agent_name="budget_agent",
    description="将任务移交给预算管理助手，用于估算旅行费用。",
)


# ============================================================
# 3. 各 Agent 的业务工具
# ============================================================

@tool
def get_weather(city: str) -> str:
    """查询指定城市的天气信息。"""
    # 模拟天气查询
    weather_db = {
        "北京": "晴，气温 15~28°C，北风 2 级，空气质量优",
        "上海": "多云转晴，气温 18~25°C，东南风 3 级",
        "广州": "阵雨，气温 22~30°C，南风 2 级",
        "成都": "阴，气温 16~24°C，微风",
        "杭州": "晴转多云，气温 17~26°C，东风 2 级",
    }
    return weather_db.get(city, f"{city}：暂无天气数据，建议出发前查看实时天气")


@tool
def estimate_budget(city: str, days: int) -> dict:
    """估算指定城市的旅行费用。"""
    # 模拟预算估算
    budget_db = {
        "北京": {"住宿": 500, "餐饮": 200, "交通": 100, "门票": 150},
        "上海": {"住宿": 600, "餐饮": 250, "交通": 80, "门票": 120},
        "广州": {"住宿": 450, "餐饮": 220, "交通": 60, "门票": 80},
        "成都": {"住宿": 350, "餐饮": 180, "交通": 50, "门票": 100},
        "杭州": {"住宿": 400, "餐饮": 200, "交通": 60, "门票": 130},
    }
    costs = budget_db.get(
        city,
        {"住宿": 400, "餐饮": 200, "交通": 80, "门票": 100},
    )
    daily_total = sum(costs.values())
    grand_total = daily_total * days
    return {
        "city": city,
        "days": days,
        "daily_breakdown": costs,
        "daily_total": daily_total,
        "grand_total": grand_total,
    }


# ============================================================
# 4. 创建各专业 Agent
# ============================================================
from langchain.agents import create_agent

# --- 旅行规划 Agent（入口 Agent） ---
travel_agent = create_agent(
    model=llm,
    tools=[transfer_to_weather, transfer_to_budget],
    system_prompt=(
        "你是一个旅行规划助手，负责帮助用户规划行程。\n\n"
        "INSTRUCTIONS:\n"
        "- 了解用户的目的地、出行天数等需求\n"
        "- 如果你需要天气信息，请调用 transfer_to_weather 移交给天气助手\n"
        "- 如果你需要预算估算，请调用 transfer_to_budget 移交给预算助手\n"
        "- 当你收到其他助手返回的信息后，整合所有信息给出完整旅行方案\n"
        "- 回答时使用中文，格式清晰"
    ),
    name="travel_agent",
)

# --- 天气查询 Agent ---
weather_agent = create_agent(
    model=llm,
    tools=[get_weather, transfer_to_travel, transfer_to_budget],
    system_prompt=(
        "你是一个天气查询助手，负责提供目的地天气信息。\n\n"
        "INSTRUCTIONS:\n"
        "- 使用 get_weather 工具查询天气\n"
        "- 查询完成后，如果需要继续规划行程，调用 transfer_to_travel 移交给旅行助手\n"
        "- 如果需要预算估算，调用 transfer_to_budget 移交给预算助手\n"
        "- 只提供天气相关回答，不要越界"
    ),
    name="weather_agent",
)

# --- 预算管理 Agent ---
budget_agent = create_agent(
    model=llm,
    tools=[estimate_budget, transfer_to_travel, transfer_to_weather],
    system_prompt=(
        "你是一个预算管理助手，负责估算旅行费用。\n\n"
        "INSTRUCTIONS:\n"
        "- 使用 estimate_budget 工具估算费用\n"
        "- 估算完成后，如果需要继续规划行程，调用 transfer_to_travel 移交给旅行助手\n"
        "- 如果需要天气信息，调用 transfer_to_weather 移交给天气助手\n"
        "- 只提供预算相关回答，不要越界"
    ),
    name="budget_agent",
)


# ============================================================
# 5. 构建 Swarm 图
# ============================================================

def build_swarm() -> StateGraph:
    """
    构建 Swarm 图。

    与 Supervisor 模式不同：
    - Supervisor 模式：worker → supervisor → worker（所有 Agent 通过 supervisor 中转）
    - Swarm 模式：agent → agent → agent（Agent 之间直接 handoff，扁平拓扑）

    每个 Agent 作为独立节点添加到图中，通过 handoff 工具中的 Command(goto=...)
    实现互相跳转，不需要显式定义条件边。
    """
    swarm = (
        StateGraph(MessagesState)
        # 添加所有 Agent 节点
        .add_node(travel_agent, destinations=["travel_agent", "weather_agent", "budget_agent", END])
        .add_node(weather_agent, destinations=["travel_agent", "weather_agent", "budget_agent", END])
        .add_node(budget_agent, destinations=["travel_agent", "weather_agent", "budget_agent", END])
        # 入口边：START → travel_agent
        .add_edge(START, "travel_agent")
        .compile()
    )
    return swarm


# ============================================================
# 6. 运行示例
# ============================================================

if __name__ == "__main__":
    # 构建 Swarm 图
    swarm_graph = build_swarm()

    # 打印图结构
    print("=" * 60)
    print("🐝 Swarm 图结构（Mermaid）")
    print("=" * 60)
    print(swarm_graph.get_graph().draw_mermaid())

    # 测试场景 1：需要天气 + 预算的完整旅行规划
    print("\n" + "=" * 60)
    print("🚀 测试场景：北京三日游（天气 + 预算）")
    print("=" * 60 + "\n")

    user_input = "我想去北京旅游3天，帮我了解一下天气情况和大概需要多少预算"

    print(f"👤 用户：{user_input}\n")
    print("-" * 60)

    # 使用 stream 方式运行，观察各 Agent 的交接过程
    for chunk in swarm_graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        subgraphs=True,
    ):
        # chunk 格式: (namespace, data)
        namespace, data = chunk
        if namespace:  # 子图输出（Agent 内部执行）
            for node_name, node_output in data.items():
                if "messages" in node_output:
                    last_msg = node_output["messages"][-1]
                    # 获取消息内容
                    content = ""
                    if hasattr(last_msg, "content"):
                        content = last_msg.content
                    elif isinstance(last_msg, dict):
                        content = last_msg.get("content", "")
                    # 只打印有实际内容的消息
                    if content and len(content) > 0:
                        # 截取前 200 字预览
                        preview = content[:200] + ("..." if len(content) > 200 else "")
                        print(f"  [{node_name}] {preview}")
        else:  # 顶层图输出
            for node_name, node_output in data.items():
                if "messages" in node_output:
                    last_msg = node_output["messages"][-1]
                    content = ""
                    if hasattr(last_msg, "content"):
                        content = last_msg.content
                    elif isinstance(last_msg, dict):
                        content = last_msg.get("content", "")
                    if content:
                        preview = content[:200] + ("..." if len(content) > 200 else "")
                        print(f"  [顶层:{node_name}] {preview}")

    # 测试场景 2：只查询天气（简单场景，不需要 handoff）
    print("\n" + "=" * 60)
    print("🚀 测试场景：上海天气查询（简单场景）")
    print("=" * 60 + "\n")

    user_input_2 = "帮我查一下上海的天气"
    print(f"👤 用户：{user_input_2}\n")
    print("-" * 60)

    result = swarm_graph.invoke(
        {"messages": [{"role": "user", "content": user_input_2}]}
    )

    # 打印最终结果的所有消息
    print("\n📋 最终对话记录：")
    print("-" * 60)
    for msg in result["messages"]:
        role = getattr(msg, "type", msg.get("role", "unknown")) if isinstance(msg, dict) else getattr(msg, "type", "unknown")
        content = getattr(msg, "content", msg.get("content", "")) if isinstance(msg, dict) else getattr(msg, "content", "")
        if content:
            print(f"\n[{role}]")
            print(content)
