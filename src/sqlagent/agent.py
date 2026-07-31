"""
LangChain AI Agent 核心模块。

封装 LLM + Tools + AgentExecutor，提供统一的查询接口。
"""

from collections.abc import Iterator
from typing import Any, Dict, Optional

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from rich.console import Console

from .config import config
from .database import DatabaseManager
from .prompts import SQL_AGENT_SYSTEM_PROMPT
from .tools import create_tools

console = Console()


class SQLAgent:
    """AI SQL Agent — 将自然语言转为 MySQL 查询并执行。

    使用方式:
        agent = SQLAgent()
        result = agent.run("查询销售额最高的10个产品")
        # result = {"output": "...", "sql": "SELECT ...", "data": {...}}
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        read_only: bool = True,
    ):
        self.database_url = database_url or config.mysql.url
        self.model = model or config.llm.model
        self.api_key = api_key or config.llm.api_key
        self.base_url = base_url or config.llm.base_url
        self.read_only = read_only

        # 初始化数据库和 LLM
        self._db = DatabaseManager(self.database_url)
        self._llm = self._create_llm()
        self._tools = create_tools(self._db)
        self._executor = self._create_executor()

    @property
    def db(self) -> DatabaseManager:
        """数据库管理器。"""
        return self._db

    # ── LLM ────────────────────────────────────────────

    def _create_llm(self) -> ChatOpenAI:
        """创建 OpenAI 兼容的 LLM 实例。"""
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0,
            streaming=True,
        )

    # ── Agent Executor ─────────────────────────────────

    def _create_executor(self) -> AgentExecutor:
        """创建 LangChain Agent 执行器。"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", SQL_AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self._llm, self._tools, prompt)

        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

        return AgentExecutor(
            agent=agent,
            tools=self._tools,
            memory=memory,
            verbose=config.log_level == "DEBUG",
            handle_parsing_errors=True,
            max_iterations=15,
        )

    # ── 查询接口 ───────────────────────────────────────

    def run(self, question: str) -> Dict[str, Any]:
        """执行自然语言查询。

        Args:
            question: 用户的自然语言问题

        Returns:
            {"output": str, "intermediate_steps": [...]}
        """
        try:
            result = self._executor.invoke({"input": question})
            return {
                "success": True,
                "output": result.get("output", ""),
                "intermediate_steps": result.get("intermediate_steps", []),
            }
        except Exception as e:
            console.print(f"[red]Agent 执行错误: {e}[/red]")
            return {
                "success": False,
                "output": f"执行出错: {e}",
                "error": str(e),
            }

    def stream(self, question: str) -> Iterator[Dict[str, Any]]:
        """流式执行查询。

        Args:
            question: 用户问题

        Yields:
            每个步骤的事件字典
        """
        try:
            for event in self._executor.stream({"input": question}):
                yield event
        except Exception as e:
            yield {"error": str(e)}

    def clear_memory(self) -> None:
        """清除对话记忆。"""
        memory = self._executor.memory
        if memory:
            memory.clear()

    # ── 诊断 ───────────────────────────────────────────

    def test_connections(self) -> Dict[str, Any]:
        """测试数据库和 LLM 连接状态。"""
        results: Dict[str, Any] = {
            "database": self._db.test_connection(),
            "llm": False,
        }

        try:
            from langchain_core.messages import HumanMessage
            resp = self._llm.invoke([HumanMessage(content="Hi")])
            results["llm"] = bool(resp.content)
        except Exception:
            pass

        results["status"] = "healthy" if all(results.values()) else "unhealthy"
        return results
