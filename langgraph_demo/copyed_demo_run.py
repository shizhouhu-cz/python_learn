"""
LangGraph 子图（Sub-graph）完整示例
演示状态隔离、output_schema 和并行子图

场景：日志分析系统
- 子图1：失败分析 - 分析错误日志，生成错误摘要
- 子图2：性能分析 - 分析慢请求，生成性能报告
- 主图：整合两个子图的结果
"""

from typing_extensions import TypedDict
from typing import List, Optional, Annotated
from operator import add
from langgraph.graph import StateGraph, START, END

# ========== 1. 数据模型定义 ==========


class Log(TypedDict):
    """日志数据模型"""

    id: str  # 日志 ID
    question: str  # 用户问题
    answer: str  # 系统回答
    status: str  # 状态: success / error
    latency: int  # 响应时间（毫秒）
    error_type: Optional[str]  # 错误类型（可选）


# ========== 2. 子图1：失败分析 ==========


# 子图内部状态（完整状态）
class FailureAnalysisState(TypedDict):
    cleaned_logs: List[Log]  # 输入：清洗后的日志
    failures: List[Log]  # 中间变量：失败的日志
    fa_summary: str  # 输出：失败分析摘要
    processed_logs: List[str]  # 输出：处理过的日志 ID


# 子图输出状态（只返回需要的字段）
class FailureAnalysisOutputState(TypedDict):
    fa_summary: str  # 只输出摘要
    processed_logs: List[str]  # 只输出处理记录


def get_failures(state: FailureAnalysisState):
    """获取失败的日志"""
    cleaned_logs = state["cleaned_logs"]

    # 筛选出状态为 error 的日志
    failures = [log for log in cleaned_logs if log.get("status") == "error"]

    print(f"🔍 失败分析：找到 {len(failures)} 条错误日志")
    return {"failures": failures}


def generate_failure_summary(state: FailureAnalysisState):
    """生成失败分析摘要"""
    failures = state["failures"]

    if not failures:
        summary = "没有发现错误日志"
    else:
        # 统计错误类型
        error_types = {}
        for log in failures:
            error_type = log.get("error_type", "unknown")
            error_types[error_type] = error_types.get(error_type, 0) + 1

        # 生成摘要
        summary = f"发现 {len(failures)} 个错误。"
        summary += f" 错误类型分布: {error_types}"

    # 记录处理过的日志 ID
    processed_logs = [
        f"failure-analysis-on-log-{failure['id']}" for failure in failures
    ]

    print(f"📝 失败分析摘要生成完成")
    return {"fa_summary": summary, "processed_logs": processed_logs}


# 构建失败分析子图
fa_builder = StateGraph(
    state_schema=FailureAnalysisState,
    output_schema=FailureAnalysisOutputState,  # ⭐ 只返回指定字段
)

fa_builder.add_node("get_failures", get_failures)
fa_builder.add_node("generate_summary", generate_failure_summary)

fa_builder.add_edge(START, "get_failures")
fa_builder.add_edge("get_failures", "generate_summary")
fa_builder.add_edge("generate_summary", END)

# ========== 3. 子图2：性能分析 ==========


# 子图内部状态（完整状态）
class PerformanceAnalysisState(TypedDict):
    cleaned_logs: List[Log]  # 输入
    slow_logs: List[Log]  # 中间变量：慢请求
    latency_stats: dict  # 中间变量：延迟统计
    perf_report: str  # 输出：性能报告
    processed_logs: List[str]  # 输出：处理记录


# 子图输出状态
class PerformanceAnalysisOutputState(TypedDict):
    perf_report: str  # 只输出报告
    processed_logs: List[str]  # 只输出处理记录


def get_slow_logs(state: PerformanceAnalysisState):
    """获取慢请求日志（延迟 > 1000ms）"""
    cleaned_logs = state["cleaned_logs"]

    slow_logs = [log for log in cleaned_logs if log.get("latency", 0) > 1000]

    print(f"🐢 性能分析：找到 {len(slow_logs)} 条慢请求")
    return {"slow_logs": slow_logs}


def calculate_stats(state: PerformanceAnalysisState):
    """计算延迟统计"""
    slow_logs = state["slow_logs"]

    if slow_logs:
        latencies = [log["latency"] for log in slow_logs]
        stats = {
            "count": len(latencies),
            "avg": sum(latencies) / len(latencies),
            "max": max(latencies),
            "min": min(latencies),
        }
    else:
        stats = {"count": 0, "avg": 0, "max": 0, "min": 0}

    return {"latency_stats": stats}


def generate_performance_report(state: PerformanceAnalysisState):
    """生成性能报告"""
    stats = state["latency_stats"]
    slow_logs = state["slow_logs"]

    report = f"性能报告：\n"
    report += f"- 慢请求数量: {stats['count']}\n"
    report += f"- 平均延迟: {stats['avg']:.0f}ms\n"
    report += f"- 最大延迟: {stats['max']}ms\n"
    report += f"- 最小延迟: {stats['min']}ms"

    # 记录处理的日志
    processed_logs = [f"performance-analysis-on-log-{log['id']}" for log in slow_logs]

    print(f"📊 性能报告生成完成")
    return {"perf_report": report, "processed_logs": processed_logs}


# 构建性能分析子图
pa_builder = StateGraph(
    PerformanceAnalysisState, output_schema=PerformanceAnalysisOutputState
)

pa_builder.add_node("get_slow_logs", get_slow_logs)
pa_builder.add_node("calculate_stats", calculate_stats)
pa_builder.add_node("generate_report", generate_performance_report)

pa_builder.add_edge(START, "get_slow_logs")
pa_builder.add_edge("get_slow_logs", "calculate_stats")
pa_builder.add_edge("calculate_stats", "generate_report")
pa_builder.add_edge("generate_report", END)

# ========== 4. 主图：整合子图 ==========


class MainGraphState(TypedDict):
    raw_logs: List[Log]  # 输入：原始日志
    cleaned_logs: List[Log]  # 清洗后的日志
    fa_summary: str  # 来自失败分析子图
    perf_report: str  # 来自性能分析子图
    processed_logs: Annotated[List[str], add]  # 来自两个子图，需要合并
    final_output: str  # 最终输出


def clean_logs(state: MainGraphState):
    """清洗日志"""
    raw_logs = state["raw_logs"]

    # 简单清洗：过滤无效日志
    cleaned_logs = [log for log in raw_logs if log.get("id")]

    print(f"🧹 日志清洗完成：{len(raw_logs)} → {len(cleaned_logs)} 条")
    return {"cleaned_logs": cleaned_logs}


def finalize_report(state: MainGraphState):
    """生成最终报告"""
    fa_summary = state.get("fa_summary", "无")
    perf_report = state.get("perf_report", "无")
    processed_logs = state.get("processed_logs", [])

    final_output = f"""
{"=" * 50}
📋 日志分析最终报告
{"=" * 50}

【失败分析】
{fa_summary}

【性能分析】
{perf_report}

【处理记录】
共处理 {len(processed_logs)} 条日志:
{chr(10).join(["  - " + log for log in processed_logs])}
{"=" * 50}
"""

    print("✅ 最终报告生成完成")
    return {"final_output": final_output}


# 构建主图
def build_main_graph():
    """构建主图"""
    main_builder = StateGraph(MainGraphState)

    # 添加常规节点
    main_builder.add_node("clean_logs", clean_logs)

    # ⭐ 将编译后的子图作为节点添加
    main_builder.add_node("failure_analysis", fa_builder.compile())
    main_builder.add_node("performance_analysis", pa_builder.compile())

    # 添加最终处理节点
    main_builder.add_node("finalize", finalize_report)

    # 定义执行流程
    main_builder.add_edge(START, "clean_logs")

    # 并行执行两个子图
    main_builder.add_edge("clean_logs", "failure_analysis")
    main_builder.add_edge("clean_logs", "performance_analysis")

    # 汇聚到最终节点
    main_builder.add_edge("failure_analysis", "finalize")
    main_builder.add_edge("performance_analysis", "finalize")
    main_builder.add_edge("finalize", END)

    return main_builder.compile()


# ========== 5. 主程序 ==========

if __name__ == "__main__":
    # 构建图
    graph = build_main_graph()

    # 可视化图结构
    print("=" * 50)
    print("📊 图结构可视化")
    print("=" * 50)

    try:
        from IPython.display import Image, display

        # 展开子图内部结构
        display(Image(graph.get_graph(xray=1).draw_mermaid_png()))
    except Exception:
        print(graph.get_graph().draw_mermaid())

    # 准备测试数据
    test_logs: List[Log] = [
        {
            "id": "1",
            "question": "How to use LangGraph?",
            "answer": "LangGraph is a framework for building AI applications.",
            "status": "success",
            "latency": 500,
            "error_type": None,
        },
        {
            "id": "2",
            "question": "How to use Chroma?",
            "answer": "Error: Connection timeout",
            "status": "error",
            "latency": 5000,
            "error_type": "timeout",
        },
        {
            "id": "3",
            "question": "What is RAG?",
            "answer": "RAG stands for Retrieval Augmented Generation.",
            "status": "success",
            "latency": 300,
            "error_type": None,
        },
        {
            "id": "4",
            "question": "How to build agents?",
            "answer": "Error: Rate limit exceeded",
            "status": "error",
            "latency": 2000,
            "error_type": "rate_limit",
        },
        {
            "id": "5",
            "question": "Explain state management",
            "answer": "State management in LangGraph uses TypedDict...",
            "status": "success",
            "latency": 1500,
            "error_type": None,
        },
    ]

    # 执行图
    print("\n" + "=" * 50)
    print("🚀 执行日志分析")
    print("=" * 50 + "\n")

    result = graph.invoke({"raw_logs": test_logs})

    # 输出最终报告
    print(result["final_output"])

    # 验证状态隔离
    print("\n📝 状态隔离验证:")
    print(f"  - 主图状态中的字段: {list(result.keys())}")
    print(f"  - 子图中间变量 'failures' 在主图中: {'failures' in result}")
    print(f"  - 子图中间变量 'slow_logs' 在主图中: {'slow_logs' in result}")
