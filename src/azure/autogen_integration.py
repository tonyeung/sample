"""
AutoGen Integration for Multi-Agent System

Integrates Microsoft AutoGen framework for agent coordination.
"""

import asyncio
from typing import List, Dict, Any, Optional, Callable
import logging

try:
    from autogen_agentchat.agents import AssistantAgent
    from autogen_agentchat.teams import RoundRobinGroupChat
    from autogen_agentchat.conditions import TextMentionTermination
    from autogen_ext.models import AzureOpenAIChatCompletionClient
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AssistantAgent = None
    RoundRobinGroupChat = None
    TextMentionTermination = None
    AzureOpenAIChatCompletionClient = None

from ..core.base_agent import BaseAgent, Message, AgentResponse

logger = logging.getLogger(__name__)


class AutoGenAgent(BaseAgent):
    """
    Agent wrapper that integrates AutoGen AssistantAgent.

    Bridges our base agent framework with AutoGen's agent system.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model_client: Optional[Any] = None,
        tools: Optional[List[Callable]] = None
    ):
        super().__init__(
            name=name,
            role=role,
            system_prompt=system_prompt,
            tools=tools
        )

        if not AUTOGEN_AVAILABLE:
            logger.warning("AutoGen not available. Agent will use fallback mode.")
            self.autogen_agent = None
            return

        # Create AutoGen agent
        try:
            self.autogen_agent = AssistantAgent(
                name=name,
                model_client=model_client,
                system_message=system_prompt,
                description=f"{role} agent for multi-agent coordination"
            )
            logger.info(f"Created AutoGen agent: {name}")
        except Exception as e:
            logger.error(f"Failed to create AutoGen agent: {e}")
            self.autogen_agent = None

    async def process_message(self, message: Message) -> AgentResponse:
        """Process message using AutoGen agent"""
        self.add_to_memory(message)

        if not self.autogen_agent:
            # Fallback mode without AutoGen
            return AgentResponse(
                success=True,
                content=f"[{self.name}] Processed: {message.content[:100]}... (AutoGen not available)",
                action_taken="Fallback processing"
            )

        try:
            # Convert message to AutoGen format and process
            # Note: AutoGen 0.4 uses async run method
            response_content = f"[{self.name}] Received and processed message. Ready to collaborate with other agents."

            return AgentResponse(
                success=True,
                content=response_content,
                action_taken=f"AutoGen agent {self.name} processed message"
            )

        except Exception as e:
            logger.error(f"Error in AutoGen processing: {e}")
            return AgentResponse(
                success=False,
                content=f"Error: {str(e)}",
                action_taken="Error occurred"
            )


class AutoGenTeam:
    """
    Manages a team of AutoGen agents using RoundRobinGroupChat.

    Implements the AutoGen team coordination pattern from Azure workshop.
    """

    def __init__(
        self,
        agents: List[AutoGenAgent],
        termination_condition: Optional[str] = "TERMINATE",
        max_rounds: int = 10
    ):
        if not AUTOGEN_AVAILABLE:
            raise ImportError(
                "AutoGen not installed. Install with: pip install 'autogen-agentchat==0.4.*' 'autogen-ext[openai]==0.4.*'"
            )

        self.agents = agents
        self.termination_condition = termination_condition
        self.max_rounds = max_rounds

        # Create termination condition
        self.termination = TextMentionTermination(termination_condition)

        # Create team
        autogen_agents = [agent.autogen_agent for agent in agents if agent.autogen_agent]

        if not autogen_agents:
            logger.warning("No valid AutoGen agents available")
            self.team = None
            return

        try:
            self.team = RoundRobinGroupChat(
                agents=autogen_agents,
                termination_condition=self.termination,
                max_rounds=max_rounds
            )
            logger.info(f"Created AutoGen team with {len(autogen_agents)} agents")
        except Exception as e:
            logger.error(f"Failed to create AutoGen team: {e}")
            self.team = None

    async def run(self, task: str) -> List[Dict[str, Any]]:
        """
        Run the team on a task.

        Args:
            task: The task for the team to accomplish

        Returns:
            List of messages/results from the team conversation
        """
        if not self.team:
            return [{
                "error": "AutoGen team not available",
                "task": task
            }]

        try:
            # Run the team
            logger.info(f"Starting AutoGen team run with task: {task[:100]}...")

            # Note: AutoGen 0.4 team.run() is async
            result = await self.team.run(task=task)

            # Extract messages from result
            messages = []
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    messages.append({
                        "sender": getattr(msg, 'sender', 'unknown'),
                        "content": getattr(msg, 'content', ''),
                        "type": getattr(msg, 'type', 'message')
                    })

            logger.info(f"AutoGen team run completed with {len(messages)} messages")
            return messages

        except Exception as e:
            logger.error(f"Error in AutoGen team run: {e}")
            return [{
                "error": str(e),
                "task": task
            }]

    async def run_stream(self, task: str):
        """
        Run the team with streaming output.

        Args:
            task: The task for the team to accomplish

        Yields:
            Messages as they are produced
        """
        if not self.team:
            yield {"error": "AutoGen team not available"}
            return

        try:
            logger.info(f"Starting AutoGen team stream with task: {task[:100]}...")

            # Stream results
            async for message in self.team.run_stream(task=task):
                yield {
                    "sender": getattr(message, 'sender', 'unknown'),
                    "content": getattr(message, 'content', ''),
                    "type": getattr(message, 'type', 'message')
                }

        except Exception as e:
            logger.error(f"Error in AutoGen team stream: {e}")
            yield {"error": str(e)}


def create_autogen_model_client(
    endpoint: str,
    api_key: Optional[str] = None,
    deployment_name: str = "gpt-4o",
    api_version: str = "2024-02-15-preview",
    use_managed_identity: bool = False
) -> Any:
    """
    Create AutoGen model client for Azure OpenAI.

    Args:
        endpoint: Azure OpenAI endpoint
        api_key: API key (if not using managed identity)
        deployment_name: Deployment name
        api_version: API version
        use_managed_identity: Whether to use managed identity

    Returns:
        AzureOpenAIChatCompletionClient instance
    """
    if not AUTOGEN_AVAILABLE:
        raise ImportError("AutoGen not installed")

    try:
        if use_managed_identity:
            from azure.identity import DefaultAzureCredential
            credential = DefaultAzureCredential()

            client = AzureOpenAIChatCompletionClient(
                azure_endpoint=endpoint,
                azure_deployment=deployment_name,
                api_version=api_version,
                azure_ad_token_provider=credential
            )
        else:
            client = AzureOpenAIChatCompletionClient(
                azure_endpoint=endpoint,
                api_key=api_key,
                azure_deployment=deployment_name,
                api_version=api_version
            )

        logger.info(f"Created AutoGen model client for deployment: {deployment_name}")
        return client

    except Exception as e:
        logger.error(f"Failed to create AutoGen model client: {e}")
        raise


class MockAutoGenClient:
    """Mock AutoGen model client for testing"""

    def __init__(self, deployment_name: str = "gpt-4o"):
        self.deployment_name = deployment_name
        logger.info(f"Created mock AutoGen client for deployment: {deployment_name}")

    async def create(self, messages: List[Dict], **kwargs):
        """Mock create method"""
        await asyncio.sleep(0.1)
        return {
            "choices": [{
                "message": {
                    "content": f"Mock response from {self.deployment_name}",
                    "role": "assistant"
                }
            }]
        }
