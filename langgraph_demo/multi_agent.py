import getpass
import os


def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")


_set_env("OPENAI_API_KEY")

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState, START, END
from typing import Literal

# 定义 3 个专业 Agent
llm = ChatOpenAI(model="gpt-5-nano")


def researcher(state: MessagesState):
    """研究员：负责信息收集"""
    system_msg = "你是资深研究员，擅长收集和分析行业信息。请提供数据和趋势分析。"
    messages = [{"role": "system", "content": system_msg}] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def chart_analyst(state: MessagesState):
    """图表分析师：负责数据可视化建议"""
    system_msg = (
        "你是数据可视化专家，擅长将数据转化为图表建议。请推荐合适的图表类型和关键指标。"
    )
    messages = [{"role": "system", "content": system_msg}] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def report_writer(state: MessagesState):
    """报告撰写员：整合信息并生成最终报告"""
    system_msg = "你是专业报告撰写员，擅长将研究结果和图表建议整合成结构清晰的报告。"
    messages = [{"role": "system", "content": system_msg}] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


# Supervisor：决定下一步调用哪个 Agent
def supervisor(
    state: MessagesState,
) -> Literal["researcher", "chart_analyst", "report_writer", "end"]:
    """管理者：协调各个 Agent 的工作流程"""
    messages = state["messages"]

    # 简单的状态机逻辑
    user_message = messages[0].content if messages else ""
    response_count = len([m for m in messages if hasattr(m, "response_metadata")])

    if response_count == 0:
        return "researcher"  # 第一步：研究
    elif response_count == 1:
        return "chart_analyst"  # 第二步：图表分析
    elif response_count == 2:
        return "report_writer"  # 第三步：报告撰写
    else:
        return "end"  # 完成


# 构建图
graph = StateGraph(MessagesState)

# 添加节点
graph.add_node("researcher", researcher)
graph.add_node("chart_analyst", chart_analyst)
graph.add_node("report_writer", report_writer)

# 添加边（串行工作流）
graph.add_edge(START, "researcher")
graph.add_edge("researcher", "chart_analyst")
graph.add_edge("chart_analyst", "report_writer")
graph.add_edge("report_writer", END)

app = graph.compile()

# 测试
response = app.invoke(
    {
        "messages": [
            ("user", "请帮我分析一下 2024 年生成式 AI 市场的发展趋势，并给出报告")
        ]
    }
)

# 打印每个 Agent 的输出
print("=== 研究员输出 ===")
print(response["messages"][1].content[:200] + "...\n")

print("=== 图表分析师输出 ===")
print(response["messages"][2].content[:200] + "...\n")

print("=== 最终报告 ===")
print(response["messages"][3].content)
