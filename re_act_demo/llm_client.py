import json

from base_tool import ToolRegistry
from openai import OpenAI

REACT_SYSTEM_PROMPT = """
你是一个擅长推理和使用工具的 AI 助手。

## 工作方式
1. 先思考当前问题和已有信息，分析下一步应该做什么
2. 如果需要外部信息或执行操作，可以调用提供的工具
3. 调用工具后根据返回结果继续思考
4. 当信息足够回答问题时，直接给出最终答案

## 要求
- 不要编造信息，不确定就调用工具查询
- 思考过程要清晰，一步一步来
- 最终答案要简洁准确，直接回应用户问题
"""


class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def chat_with_tools(
        self, messages: list[dict[str, any]], tools: None | list[dict[str, any]] = None
    ):
        """
        带工具调用能力的聊天窗口
        返回完整的message对象，包含content和tool_calls
        """

        kwargs = {"model": self.model, "messages": messages, "temperature": 0}

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)

        return response.choices[0].message


class FunctionCallingReActAgent:
    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        max_iterations: int = 10,
    ):
        self.llm = llm
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.system_prompt = REACT_SYSTEM_PROMPT

    def run(self, user_query: str) -> str:

        # 初始化消息历史
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query},
        ]

        iteration = 0
        # 把工具转成json schema描述，让模型知道有哪些工具能调用
        tool_schemas = self.tool_registry.get_openai_schemas()
        print(tool_schemas)

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n======第{iteration}轮思考======")

            # invoke llm 给模型消息列表和工具描述
            message = self.llm.chat_with_tools(messages, tools=tool_schemas)

            print(message)

            # print thought process
            if message.content:
                print("Thought:", message.content)

            messages.append(message.model_dump())

            # if no tool call -> return answer
            if not message.tool_calls:
                print("\n mission complete")
                return message.content or "no output"

            # need call tool -> call tools in order
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name

                # analyze parameter
                try:
                    tool_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}
                    print(f"工具参数解析失败:{tool_call.function.arguments}")

                print(f"\n 调用工具：{tool_name}, 参数:{tool_args}")

                # find and execute tool
                tool = self.tool_registry.get_tool(tool_name)
                if not tool:
                    observation = f"error：tool not found {tool_name}"
                else:
                    try:
                        observation = tool.run(**tool_args)
                    except Exception as e:  # noqa: BLE001
                        observation = f"工具执行一场:{e}"

                print(f"工具返回：{observation}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": observation,
                    }
                )
        return "超过最大思考伦茨，任务未完成"
