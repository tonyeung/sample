"""
Azure Integration for Multi-Agent System

Provides integration with Microsoft Azure services:
- Azure OpenAI for LLM inference
- AutoGen for multi-agent coordination
- Azure AI Foundry for deployment
"""

from .azure_client import (
    AzureOpenAIClient,
    MockAzureOpenAIClient,
    AzureConfig,
    get_azure_client
)

try:
    from .autogen_integration import (
        AutoGenAgent,
        AutoGenTeam,
        create_autogen_model_client,
        MockAutoGenClient
    )
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    AutoGenAgent = None
    AutoGenTeam = None
    create_autogen_model_client = None
    MockAutoGenClient = None

__all__ = [
    'AzureOpenAIClient',
    'MockAzureOpenAIClient',
    'AzureConfig',
    'get_azure_client',
    'AutoGenAgent',
    'AutoGenTeam',
    'create_autogen_model_client',
    'MockAutoGenClient',
    'AUTOGEN_AVAILABLE'
]
