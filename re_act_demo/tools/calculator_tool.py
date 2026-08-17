from base_tool import BaseTool


class CalculatorTool(BaseTool):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "执行数据计算，支持加减乘除和括号运算"

    @property
    def parameters(self) -> dict[str, any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "合法的数学表达式，例如'123 * 456'、 '(10 + 20) * 5'",
                }
            },
            "required": ["expression"],
        }

    def run(self, expression: str) -> str:
        try:
            result = eval(expression)
            return str(result)
        except Exception as e:  # noqa: BLE001
            return f"计算失败:{e}"
