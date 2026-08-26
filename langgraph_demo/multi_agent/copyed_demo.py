from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_stream_writer
from langgraph.constants import START, END
from langgraph.graph.message import add_messages
from operator import add
from langgraph.graph import StateGraph


# 初始化 LLM
llm = ChatOpenAI(model="gpt-4o-mini")


# -----------------------------------------------------
# 工具函数
# -----------------------------------------------------
def extract_content(msg):
    """
    抽取 message 内容并统一格式为 string。
    支持: str, HumanMessage/AIMessage, dict
    """
    if isinstance(msg, BaseMessage):
        return msg.content
    if isinstance(msg, dict) and "content" in msg:
        return msg["content"]
    return str(msg)


def ensure_human_message(msg):
    """将任何类型消息安全转换为 HumanMessage。"""
    content = extract_content(msg)
    return HumanMessage(content=content)


# -----------------------------------------------------
# 定义状态
# -----------------------------------------------------
class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    type: str


# -----------------------------------------------------
# 节点定义
# -----------------------------------------------------
def supervisor_node(state: State):
    """Supervisor 节点：分析用户意图并路由到对应 Agent"""
    writer = get_stream_writer()
    writer({"node": "supervisor_node"})

    # 如果已经分好类，结束流程
    if state.get("type") and state["type"] != "":
        return {"type": "__end__"}

    # 获取用户输入
    user_msg = extract_content(state["messages"][0])

    # 分类 prompt
    system_prompt = """
你是一个专业的客服助手，请将用户的问题分类为以下几类之一：
travel / joke / couplet / other
不要返回其他内容。
    """

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]
    )

    type_result = extract_content(response)
    writer({"supervisor_result": type_result})

    return {"type": type_result}


def joke_node(state: State):
    """笑话 Agent：根据用户请求生成笑话"""
    writer = get_stream_writer()
    writer({"node": "joke_node"})

    user_msg = extract_content(state["messages"][0])

    system_prompt = "你是一个笑话大师，根据用户的问题，写一个不超过100个字的笑话。"

    response = llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]
    )

    joke_result = extract_content(response)
    writer({"joke_result": joke_result})

    return {"messages": [HumanMessage(content=joke_result)], "type": "joke"}


def travel_node(state: State):
    """旅行 Agent：提供旅行建议"""
    writer = get_stream_writer()
    writer({"node": "travel_node"})
    return {"messages": [HumanMessage(content="我推荐你去北京")], "type": "travel"}


def couplet_node(state: State):
    """对联 Agent：生成对联"""
    writer = get_stream_writer()
    writer({"node": "couplet_node"})
    return {
        "messages": [HumanMessage(content="上联：春风得意马蹄疾")],
        "type": "couplet",
    }


def other_node(state: State):
    """兜底 Agent：处理无法识别的请求"""
    writer = get_stream_writer()
    writer({"node": "other_node"})
    return {"messages": [HumanMessage(content="暂时无法回答你的问题")], "type": "other"}


# -----------------------------------------------------
# 路由函数
# -----------------------------------------------------
def routing_func(state: State):
    """根据分类结果决定下一个节点"""
    t = state["type"]

    if t in ("travel", "joke", "couplet", "other"):
        return t
    elif t == "__end__":
        return "__end__"
    else:
        return "other"


# -----------------------------------------------------
# 构建 Graph
# -----------------------------------------------------
builder = StateGraph(State)

# 添加节点
builder.add_node("supervisor_node", supervisor_node)
builder.add_node("joke_node", joke_node)
builder.add_node("travel_node", travel_node)
builder.add_node("couplet_node", couplet_node)
builder.add_node("other_node", other_node)

# 添加边：START → supervisor
builder.add_edge(START, "supervisor_node")

# 添加条件边：supervisor → 各 worker 或 END
builder.add_conditional_edges(
    "supervisor_node",
    routing_func,
    {
        "joke": "joke_node",
        "travel": "travel_node",
        "couplet": "couplet_node",
        "other": "other_node",
        "__end__": END,
    },
)

# 添加边：各 worker → supervisor（形成循环）
builder.add_edge("joke_node", "supervisor_node")
builder.add_edge("travel_node", "supervisor_node")
builder.add_edge("couplet_node", "supervisor_node")
builder.add_edge("other_node", "supervisor_node")

# -----------------------------------------------------
# 编译并运行
# -----------------------------------------------------
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)


# 运行示例
if __name__ == "__main__":
    config = {"configurable": {"thread_id": "1"}}

    for chunk in graph.stream(
        {"messages": ["讲个5个字以内的笑话"]}, config, stream_mode="custom"
    ):
        print(chunk)
