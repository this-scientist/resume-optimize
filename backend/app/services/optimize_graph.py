from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.services.chat_models import complete_chat


class OptimizeState(TypedDict, total=False):
    """LangGraph 编排状态：四阶段产物依次写入，对用户仅暴露最终简历。"""

    jd_text: str
    resume_md: str
    retrieved_context: str
    extra_instructions: str | None

    jd_analysis: str
    gap_analysis: str
    resume_draft: str
    final_resume: str


SYS_DECODE_JD = """你是资深招聘与人才 Mapping 顾问。将岗位 JD 转化为「简历筛选视角」的结构化要点。
输出 Markdown，必须包含以下小节（若 JD 未提及则写「未提及」）：
## 硬性门槛
## 核心能力关键词（Top5）
## 业务场景
## 隐性偏好（从措辞与团队描述合理推断）
## 6 个月内成果期待"""


SYS_GAP = """你是职业顾问。根据「JD 结构化分析」与「候选人简历」做人岗差距扫描。
输出 Markdown，包含一张表格，列：维度 | 简历现状 | JD 要求 | 匹配结论 | 简要理由。
匹配结论仅限：完全匹配 / 需强化表达 / 缺失可迁移 / 可忽略。
不得编造候选人未出现的经历或项目。"""


SYS_REWRITE = """你是中文简历优化专家。综合 JD 原文、JD 分析、差距分析、面试知识摘录与候选人原始简历，
输出一版完整、可直接投递的简历正文（Markdown）。
要求：关键词自然对齐（忌堆砌）、能量化尽量量化、结构优先展示与 JD 最相关的经历、事实一致勿虚构。"""


SYS_HOOKS = """你是面试辅导顾问。在给定的简历正文基础上，结合面试知识/面经摘录，在恰当位置补充简短「可展开钩子」
（一两句话，便于面试官顺势追问；勿写成长段落）。保持事实真实；输出仍为完整简历 Markdown 正文。"""


def _build_optimize_graph(
    *,
    api_key: str,
    base_url: str | None,
    model: str,
):
    def decode_jd(state: OptimizeState) -> dict[str, str]:
        user = f"请分析下列岗位 JD：\n\n{state['jd_text'].strip()}"
        text = complete_chat(
            system=SYS_DECODE_JD,
            user=user,
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        return {"jd_analysis": text}

    def gap_analysis(state: OptimizeState) -> dict[str, str]:
        user_parts = [
            "## JD 结构化分析\n",
            state.get("jd_analysis", "").strip(),
            "\n\n## 候选人简历（Markdown）\n",
            state.get("resume_md", "").strip(),
        ]
        text = complete_chat(
            system=SYS_GAP,
            user="".join(user_parts),
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        return {"gap_analysis": text}

    def rewrite_resume(state: OptimizeState) -> dict[str, str]:
        parts = [
            "## 岗位 JD\n",
            state["jd_text"].strip(),
            "\n\n## JD 结构化分析\n",
            state.get("jd_analysis", "").strip(),
            "\n\n## 差距分析\n",
            state.get("gap_analysis", "").strip(),
            "\n\n## 检索到的面试相关知识（节选）\n",
            (state.get("retrieved_context") or "").strip() or "（无）",
            "\n\n## 当前简历（Markdown）\n",
            state.get("resume_md", "").strip(),
        ]
        extra = state.get("extra_instructions")
        if extra and str(extra).strip():
            parts.extend(["\n\n## 额外要求\n", str(extra).strip()])
        parts.append("\n\n请输出完整优化后的简历 Markdown 正文。")
        text = complete_chat(
            system=SYS_REWRITE,
            user="".join(parts),
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        return {"resume_draft": text}

    def embed_hooks(state: OptimizeState) -> dict[str, str]:
        parts = [
            "## 差距分析（摘要线索）\n",
            state.get("gap_analysis", "").strip(),
            "\n\n## 面试知识摘录\n",
            (state.get("retrieved_context") or "").strip() or "（无）",
            "\n\n## 待植入钩子的简历正文（Markdown）\n",
            state.get("resume_draft", "").strip(),
            "\n\n请在保持事实一致的前提下输出修订后的完整简历 Markdown。",
        ]
        text = complete_chat(
            system=SYS_HOOKS,
            user="".join(parts),
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        return {"final_resume": text}

    g = StateGraph(OptimizeState)
    g.add_node("decode_jd", decode_jd)
    g.add_node("gap_analysis", gap_analysis)
    g.add_node("rewrite_resume", rewrite_resume)
    g.add_node("embed_hooks", embed_hooks)
    g.add_edge(START, "decode_jd")
    g.add_edge("decode_jd", "gap_analysis")
    g.add_edge("gap_analysis", "rewrite_resume")
    g.add_edge("rewrite_resume", "embed_hooks")
    g.add_edge("embed_hooks", END)
    return g.compile()


def run_optimize_graph(
    *,
    jd_text: str,
    resume_md: str,
    retrieved_context: str,
    extra_instructions: str | None,
    api_key: str,
    base_url: str | None,
    model: str,
) -> str:
    """执行四阶段 LangGraph 流水线，返回最终简历 Markdown。"""
    graph = _build_optimize_graph(api_key=api_key, base_url=base_url, model=model)
    out: OptimizeState = graph.invoke(
        {
            "jd_text": jd_text,
            "resume_md": resume_md,
            "retrieved_context": retrieved_context,
            "extra_instructions": extra_instructions,
        },
    )
    final = (out.get("final_resume") or "").strip()
    if not final:
        raise ValueError("optimize graph produced empty resume")
    return final
