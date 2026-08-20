import os

from IPython.display import Image, display
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph

# 在导入tiktoken/langchain_openai之前设置！
os.environ["TIKTOKEN_NO_DOWNLOAD"] = "1"


# glm 4.7客户端
def create_glm_client() -> ChatOpenAI:
    return ChatOpenAI(
        api_key="d1de7475090740ebb6c887167a6a8b98.2WUSfYbmgQwYLKF4",
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        model="glm-4.7",
    )


glm_client = create_glm_client()


# 创建node
def chat_model(state: MessagesState):
    messages = [("user", "介绍下langgraph")] + state["messages"]
    return {"messages": [glm_client.invoke(messages)]}


# 创建图
graph = StateGraph(MessagesState)
graph.add_node("chat", chat_model)

graph.add_edge(START, "chat")
graph.add_edge("chat", END)

# 构建运行时图
app = graph.compile()

display(Image(app.get_graph().draw_mermaid_png()))
