from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1. 准备知识库
documents = [
    Document(page_content="LangGraph 支持循环和条件分支"),
    Document(page_content="使用 StateGraph 可以定义状态图"),
    Document(page_content="ToolNode 用于自动执行工具调用"),
    Document(page_content="MemorySaver 可以保存对话历史"),
]

vectorstore = FAISS.from_documents(
    documents,
    OpenAIEmbeddings(
        # api_key="d1de7475090740ebb6c887167a6a8b98.2WUSfYbmgQwYLKF4",
        # base_url="https://open.bigmodel.cn/api/paas/v4/",
        # model="glm-4.7",
    ),
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 2. 创建 RAG 链
template = """请根据以下上下文回答问题。

上下文：
{context}

问题：{question}

回答："""

prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(
    api_key="d1de7475090740ebb6c887167a6a8b98.2WUSfYbmgQwYLKF4",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    model="glm-4.7",
)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# LCEL 构建链
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 3. 查询
question = "如何在 LangGraph 中保存对话历史？"
answer = rag_chain.invoke(question)

print(f"问题：{question}\n")
print(f"回答：{answer}")
