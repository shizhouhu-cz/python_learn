from abc import ABC, abstractmethod


class BaseTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，必须是英文、数字、下划线，符合函数命名规范"""

    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能描述，告诉模型什么时候用、干什么用"""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, any]:
        """
        工具参数的json schema 定义
        格式示例：
        {
            "type":"object",
            "property":{
                "query":{"type":"string", "description":"搜索关键字"}
            },
            "required":["query"]
        }
        """

    @abstractmethod
    def run(self, **kwargs) -> str:
        """工具执行入口，接收关键字参数，返回字符串结果"""

    def to_open_ai_schema(self) -> dict[str, any]:
        """转换成openAI function calling 标准格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self, tools: list[BaseTool]):
        self._tools = {tool.name: tool for tool in tools}

    def get_tool(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def get_openai_schemas(self) -> list[dict[str, any]]:
        """获取所有工具的openai 格式schema列表"""
        return [tool.to_open_ai_schema() for tool in self._tools.values()]
