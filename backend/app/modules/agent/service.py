from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class AgentState(TypedDict):
    question: str
    tool: str
    result: str


@dataclass
class AgentDecision:
    tool: Literal["retrieve_knowledge", "read_file", "save_document"]
    reason: str


class AgentService:
    def decide(self, question: str) -> AgentDecision:
        text = question.lower()
        if "保存" in question or "save" in text:
            return AgentDecision(tool="save_document", reason="检测到保存意图")
        if "文件" in question or "read" in text:
            return AgentDecision(tool="read_file", reason="检测到文件读取意图")
        return AgentDecision(tool="retrieve_knowledge", reason="默认走检索增强路径")

    def build_graph(self):
        graph = StateGraph(AgentState)

        def route(state: AgentState) -> AgentState:
            decision = self.decide(state["question"])
            state["tool"] = decision.tool
            state["result"] = decision.reason
            return state

        graph.add_node("route", route)
        graph.add_edge(START, "route")
        graph.add_edge("route", END)
        return graph.compile()
