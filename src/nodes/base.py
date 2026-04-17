"""节点基类

所有工作流节点应继承自 BaseNode
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, TypeVar, Callable
from langgraph.runtime import Runtime

from agent.state import WorkflowState, WorkflowContext

# 类型别名
NodeFunc = Callable[[WorkflowState, Runtime[WorkflowContext]], Dict[str, Any]]


class BaseNode(ABC):
    """节点基类

    所有业务节点应继承此类并实现 call 方法
    """

    @abstractmethod
    async def call(self, state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        """处理状态并返回更新

        Args:
            state: 当前工作流状态
            runtime: 运行时上下文

        Returns:
            需要更新到状态的字典
        """
        pass


class SimpleNode(BaseNode):
    """简单节点实现

    用于快速创建同步节点
    """

    def __init__(self, handler: Callable[[WorkflowState], Dict[str, Any]]):
        self.handler = handler

    async def call(self, state: WorkflowState, runtime: Runtime[WorkflowContext]) -> Dict[str, Any]:
        return self.handler(state)
