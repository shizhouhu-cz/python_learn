from base_tool import BaseTool


class MockSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "查询实时信息、天气、新闻、常识等外部知识"

    @property
    def parameters(self) -> dict[str, any]:
        return {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "检索关键字"}},
        }

    def run(self, query: str) -> str:
        # mock_data = {
        #     "上海今天最高气温": "2026-08-17 上海天气：晴，26-33℃，微风",
        #     "上海今日最高气温": "2026-08-17 上海天气：晴，26-33℃，微风",
        #     "北京今天天气": "2026-08-17 北京天气：多云，24-30℃",
        # }
        # return mock_data.get(query, f"未检索到{query}的相关信息")
        return "2026-08-17 上海天气：晴，26-33℃，微风"
