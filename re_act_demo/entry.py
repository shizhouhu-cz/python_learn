from base_tool import ToolRegistry
from llm_client import FunctionCallingReActAgent, LLMClient
from tools.calculator_tool import CalculatorTool
from tools.search_tool import MockSearchTool

if __name__ == "__main__":
    API_KEY = "d1de7475090740ebb6c887167a6a8b98.2WUSfYbmgQwYLKF4"
    BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    MODEL = "glm-4.7"

    tools = [CalculatorTool(), MockSearchTool()]
    tool_registry = ToolRegistry(tools)

    llm = LLMClient(api_key=API_KEY, base_url=BASE_URL, model=MODEL)

    agent = FunctionCallingReActAgent(
        llm=llm, tool_registry=tool_registry, max_iterations=10
    )

    query = "上海今天的最高气温乘以3等于多少"
    print(f"用户问题：{query}")

    answer = agent.run(query)

    print("\n" + "=" * 50)
    print(f"最终答案：{answer}")
