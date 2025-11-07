"""Orchestrator for Multi-Agent System with Human-in-the-Loop"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
import asyncio
import logging
from enum import Enum

from .base_agent import BaseAgent, Message, AgentResponse
from .memory import ContextualMemory

logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """Status of workflow execution"""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Represents a step in a workflow"""
    agent_name: str
    task: str
    requires_approval: bool = False
    dependencies: List[str] = None
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[AgentResponse] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class Orchestrator:
    """
    Orchestrates multi-agent workflows with human-in-the-loop capabilities.

    Features:
    - Agent coordination
    - Human approval for critical actions
    - Workflow management
    - Context sharing between agents
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        human_approval_callback: Optional[Callable] = None,
        shared_memory: Optional[ContextualMemory] = None
    ):
        self.agents = {agent.name: agent for agent in agents}
        self.human_approval_callback = human_approval_callback or self._default_approval
        self.shared_memory = shared_memory or ContextualMemory()
        self.workflow_history: List[Dict[str, Any]] = []
        self.current_workflow: Optional[List[WorkflowStep]] = None

        logger.info(f"Orchestrator initialized with {len(self.agents)} agents")

    async def _default_approval(self, message: str, context: Dict[str, Any]) -> bool:
        """Default approval function (auto-approve for testing)"""
        logger.warning("Using default auto-approval - implement custom approval callback!")
        print(f"\n[APPROVAL REQUIRED]")
        print(f"Action: {message}")
        print(f"Context: {context}")

        # In a real system, this would wait for human input
        # For demo purposes, auto-approve
        return True

    async def execute_workflow(self, workflow: List[WorkflowStep]) -> Dict[str, Any]:
        """
        Execute a multi-agent workflow.

        Args:
            workflow: List of workflow steps to execute

        Returns:
            Dictionary with workflow results
        """
        self.current_workflow = workflow
        results = []

        logger.info(f"Starting workflow with {len(workflow)} steps")

        for step in workflow:
            logger.info(f"Executing step: {step.agent_name} - {step.task}")

            # Check dependencies
            if not await self._check_dependencies(step, results):
                logger.error(f"Dependencies not met for step: {step.task}")
                step.status = WorkflowStatus.FAILED
                continue

            step.status = WorkflowStatus.RUNNING

            # Get agent
            agent = self.agents.get(step.agent_name)
            if not agent:
                logger.error(f"Agent not found: {step.agent_name}")
                step.status = WorkflowStatus.FAILED
                continue

            # Create message
            message = Message(
                role='system',
                content=step.task,
                sender='orchestrator',
                requires_human_approval=step.requires_approval
            )

            # Request human approval if needed
            if step.requires_approval:
                step.status = WorkflowStatus.WAITING_APPROVAL
                approved = await self.human_approval_callback(
                    f"{step.agent_name} wants to: {step.task}",
                    {'agent': step.agent_name, 'task': step.task}
                )

                if not approved:
                    logger.info(f"Step rejected by human: {step.task}")
                    step.status = WorkflowStatus.CANCELLED
                    continue

            # Execute step
            try:
                response = await agent.process_message(message)
                step.result = response
                step.status = WorkflowStatus.COMPLETED if response.success else WorkflowStatus.FAILED

                # Add to shared memory
                self.shared_memory.add_short_term(
                    content=f"{step.agent_name}: {response.content}",
                    metadata={'step': step.task, 'agent': step.agent_name},
                    importance=0.7 if response.success else 0.5
                )

                results.append({
                    'step': step.task,
                    'agent': step.agent_name,
                    'status': step.status.value,
                    'response': response.content,
                    'success': response.success
                })

                logger.info(f"Step completed: {step.task} - Status: {step.status.value}")

            except Exception as e:
                logger.error(f"Error executing step: {str(e)}")
                step.status = WorkflowStatus.FAILED
                results.append({
                    'step': step.task,
                    'agent': step.agent_name,
                    'status': step.status.value,
                    'error': str(e),
                    'success': False
                })

        # Store workflow history
        workflow_summary = {
            'steps': results,
            'total_steps': len(workflow),
            'completed': sum(1 for s in workflow if s.status == WorkflowStatus.COMPLETED),
            'failed': sum(1 for s in workflow if s.status == WorkflowStatus.FAILED),
            'cancelled': sum(1 for s in workflow if s.status == WorkflowStatus.CANCELLED)
        }

        self.workflow_history.append(workflow_summary)

        return workflow_summary

    async def _check_dependencies(self, step: WorkflowStep, completed_results: List[Dict]) -> bool:
        """Check if step dependencies are met"""
        if not step.dependencies:
            return True

        completed_steps = {r['step'] for r in completed_results if r.get('success', False)}
        return all(dep in completed_steps for dep in step.dependencies)

    async def coordinate_agents(
        self,
        task: str,
        agent_names: List[str],
        max_rounds: int = 5
    ) -> List[AgentResponse]:
        """
        Coordinate multiple agents in a round-robin fashion.

        Args:
            task: The task to accomplish
            agent_names: Names of agents to involve
            max_rounds: Maximum number of conversation rounds

        Returns:
            List of agent responses
        """
        responses = []
        current_message = Message(role='user', content=task, sender='orchestrator')

        logger.info(f"Starting agent coordination for task: {task}")

        for round_num in range(max_rounds):
            logger.info(f"Round {round_num + 1}/{max_rounds}")

            for agent_name in agent_names:
                agent = self.agents.get(agent_name)
                if not agent:
                    logger.warning(f"Agent not found: {agent_name}")
                    continue

                # Process message
                response = await agent.process_message(current_message)
                responses.append(response)

                # Update shared context
                self.shared_memory.add_short_term(
                    content=f"{agent_name}: {response.content}",
                    metadata={'round': round_num, 'agent': agent_name}
                )

                # Create next message
                current_message = Message(
                    role='agent',
                    content=response.content,
                    sender=agent_name
                )

                # Check if task is complete
                if self._is_task_complete(response):
                    logger.info("Task completed by agents")
                    return responses

        logger.info("Max rounds reached")
        return responses

    def _is_task_complete(self, response: AgentResponse) -> bool:
        """Check if response indicates task completion"""
        completion_indicators = ['FINISH', 'COMPLETE', 'DONE', 'task completed']
        return any(indicator in response.content.upper() for indicator in completion_indicators)

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        return {
            name: agent.get_capabilities()
            for name, agent in self.agents.items()
        }

    def add_agent(self, agent: BaseAgent):
        """Add a new agent to the orchestrator"""
        self.agents[agent.name] = agent
        logger.info(f"Added agent: {agent.name}")

    def remove_agent(self, agent_name: str):
        """Remove an agent from the orchestrator"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Removed agent: {agent_name}")

    def get_shared_context(self, max_items: int = 10) -> str:
        """Get shared context summary"""
        return self.shared_memory.get_context_summary(max_items)
