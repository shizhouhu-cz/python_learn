from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    foo: int


def node_1(state):
    print("---Node 1---")
    return {"foo": state["foo"] + 1}


def node_2(state):
    print("---Node 2---")
    return {"foo": state["foo"] + 1}


def node_3(state):
    print("---Node 3---")
    return {"foo": state["foo"] + 1}


# 构建图
builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

# 关键：node_1 分支到 node_2 和 node_3（并行执行）
builder.add_edge(START, "node_1")
builder.add_edge("node_1", "node_2")
builder.add_edge("node_1", "node_3")
builder.add_edge("node_2", END)  # noqa: F821
builder.add_edge("node_3", END)

graph = builder.compile()

# # 🎨 可视化图结构
# from IPython.display import Image, display

# display(Image(graph.get_graph().draw_mermaid_png()))

# # 执行会报错！
# from langgraph.errors import InvalidUpdateError

# try:
#     graph.invoke({"foo": 1})
# except InvalidUpdateError as e:
#     print(f"InvalidUpdateError occurred: {e}")
