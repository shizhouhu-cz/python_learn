# from langchain_core.prompts import FewShotChatMessagePromptTemplate
# from langchain_core.prompts import ChatPromptTemplate

# # 定义示例
# examples = [
#     {"input": "开心", "output": "😊"},
#     {"input": "难过", "output": "😢"},
#     {"input": "愤怒", "output": "😠"},
# ]

# # 创建 Few-Shot 模板
# example_prompt = ChatPromptTemplate.from_messages(
#     [
#         ("human", "{input}"),
#         ("ai", "{output}"),
#     ]
# )

# few_shot_prompt = FewShotChatMessagePromptTemplate(
#     example_prompt=example_prompt,
#     examples=examples,
# )

# # 完整提示词
# final_prompt = ChatPromptTemplate.from_messages(
#     [
#         ("system", "你需要将情绪词转换为对应的 emoji"),
#         few_shot_prompt,
#         ("human", "{input}"),
#     ]
# )

# chain = final_prompt | llm
# response = chain.invoke({"input": "兴奋"})
# print(response.content)


from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model

# 安装：pip install deepagents
model = init_chat_model(
    api_key="d1de7475090740ebb6c887167a6a8b98.2WUSfYbmgQwYLKF4",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    model="glm-4.7",
    model_provider="openai",
)
agent = create_deep_agent(model=model)

# Deep Agent 会自动规划和拆分复杂任务
result = agent.invoke(
    {"messages": [{"role": "user", "content": "研究并撰写一份关于量子计算的报告"}]}
)

print(result)
