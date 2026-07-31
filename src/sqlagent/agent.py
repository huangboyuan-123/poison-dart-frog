"""
AI Agent 核心模块 — 创建和管理 LLM 驱动的 SQL Agent。
"""

from typing import Any, AsyncIterator, Iterator

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from rich.console import Console

from .config import config
from .database import DatabaseManager
from .prompts import SQL_AGENT_SYSTEM_PROMPT
from .tools import create_tools

console = Console()


class SQLAgent:
    """AI SQL Agent — 自然语言到 SQL 的智能代理。

    使用方式:
        agent = SQLAgent()
        result = agent.run("查询销售额最高的10个产品")
        print(result)
    """

    def __init__(
        self,
        database_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        read_only: bool = True,
    ):
        """
        初始化 SQLAgent。

        Args:
            database_url: 数据库连接 URL，默认使用 .env 中的配置
            model: LLM 模型名称，默认使用 .env 中的配置
            api_key: API Key，默认使用 .env 中的配置
            base_url: API Base URL，默认使用 .env 中的配置
            read_only: 是否只读模式
        """
        self.database_url = database_url or config.database.url
        self.model = model or config.llm.model
        self.api_key = api_key or config.llm.api_key
        self.base_url = base_url or config.llm.base_url
        self.read_only = read_only

        # 初始化组件
        self._db_manager = DatabaseManager(self.database_url)
        self._llm = self._create_llm()
        self._tools = create_tools(self._db_manager)
        self._agent_executor = self._create_agent()

    def _create_llm(self) -> BaseChatModel:
        """创建 LLM 实例。"""
        return ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0,
            streaming=True,
        )

    def _create_agent(self) -> AgentExecutor:
        """创建 LangChain Agent 执行器。"""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SQL_AGENT_SYSTEM_PROMPT),
                MessagesPlaceholder(variable_name="chat_history", optional=True),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

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
            max_iterations=10,
        )

    def run(self, question: str) -> str:
        """执行自然语言查询。

        Args:
            question: 用户的自然语言问题

        Returns:
            Agent 的回答文本
        """
        try:
            result = self._agent_executor.invoke({"input": question})
            return result.get("output", "未能获取回答。")
        except Exception as e:
            return f"执行出错: {e}"

    def stream(self, question: str) -> Iterator[dict[str, Any]]:
        """流式执行查询，返回中间步骤。

        Args:
            question: 用户的自然语言问题

        Yields:
            每个中间步骤的结果字典
        """
        try:
            for event in self._agent_executor.stream({"input": question}):
                yield event
        except Exception as e:
            yield {"error": str(e)}

    def chat(self, message: str, history: list[dict] | None = None) -> str:
        """多轮对话模式。

        Args:
            message: 用户消息
            history: 历史对话记录 [{"role": "user/assistant", "content": "..."}]

        Returns:
            Agent 的回复
        """
        return self.run(message)

    def clear_memory(self) -> None:
        """清除 Agent 的对话记忆。"""
        self._agent_executor.memory.clear()

    @property
    def db(self) -> DatabaseManager:
        """获取数据库管理器。"""
        return self._db_manager

    def test_connection(self) -> dict[str, Any]:
        """测试所有连接是否正常。"""
        results = {
            "database": self._db_manager.test_connection(),
            "llm": False,
        }

        # 测试 LLM 连接
        try:
            response = self._llm.invoke([HumanMessage(content="Hi")])
            results["llm"] = bool(response.content)
        except Exception:
            results["llm"] = False

        return results
