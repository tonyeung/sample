"""
Azure OpenAI Client Configuration and Utilities
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

try:
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    AzureOpenAI = None
    DefaultAzureCredential = None

logger = logging.getLogger(__name__)


@dataclass
class AzureConfig:
    """Azure OpenAI Configuration"""
    endpoint: str
    api_key: Optional[str] = None
    deployment_name: str = "gpt-4o"
    api_version: str = "2024-02-15-preview"
    embedding_deployment: str = "text-embedding-ada-002"
    use_managed_identity: bool = False
    max_tokens: int = 4096
    temperature: float = 0.7

    @classmethod
    def from_env(cls) -> "AzureConfig":
        """Load configuration from environment variables"""
        return cls(
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            embedding_deployment=os.getenv("EMBEDDING_DEPLOYMENT_NAME", "text-embedding-ada-002"),
            use_managed_identity=os.getenv("USE_MANAGED_IDENTITY", "false").lower() == "true",
            max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("MODEL_TEMPERATURE", "0.7"))
        )

    def validate(self) -> bool:
        """Validate configuration"""
        if not self.endpoint:
            logger.error("AZURE_OPENAI_ENDPOINT is required")
            return False

        if not self.use_managed_identity and not self.api_key:
            logger.error("AZURE_OPENAI_API_KEY is required when not using managed identity")
            return False

        return True


class AzureOpenAIClient:
    """
    Wrapper for Azure OpenAI client with support for:
    - API key authentication
    - Managed identity authentication
    - Chat completions
    - Embeddings generation
    """

    def __init__(self, config: Optional[AzureConfig] = None):
        if not AZURE_AVAILABLE:
            raise ImportError(
                "Azure OpenAI packages not installed. "
                "Install with: pip install openai azure-identity"
            )

        self.config = config or AzureConfig.from_env()

        if not self.config.validate():
            raise ValueError("Invalid Azure configuration")

        # Initialize client
        if self.config.use_managed_identity:
            credential = DefaultAzureCredential()
            token_provider = get_bearer_token_provider(
                credential,
                "https://cognitiveservices.azure.com/.default"
            )
            self.client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                azure_ad_token_provider=token_provider,
                api_version=self.config.api_version
            )
        else:
            self.client = AzureOpenAI(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.api_key,
                api_version=self.config.api_version
            )

        logger.info(f"Initialized Azure OpenAI client with endpoint: {self.config.endpoint}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion using Azure OpenAI

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters for the API

        Returns:
            Response dictionary with completion
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.deployment_name,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=stream,
                **kwargs
            )

            if stream:
                return {"stream": response}

            return {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model
            }

        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            raise

    async def generate_embedding(
        self,
        text: str,
        deployment: Optional[str] = None
    ) -> List[float]:
        """
        Generate embedding for text using Azure OpenAI

        Args:
            text: Text to embed
            deployment: Embedding deployment name (defaults to config)

        Returns:
            List of floats representing the embedding
        """
        try:
            response = self.client.embeddings.create(
                model=deployment or self.config.embedding_deployment,
                input=text
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        deployment: Optional[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed
            deployment: Embedding deployment name

        Returns:
            List of embeddings
        """
        try:
            response = self.client.embeddings.create(
                model=deployment or self.config.embedding_deployment,
                input=texts
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            raise


class MockAzureOpenAIClient:
    """
    Mock client for testing without Azure credentials.
    Simulates Azure OpenAI responses.
    """

    def __init__(self, config: Optional[AzureConfig] = None):
        self.config = config or AzureConfig(
            endpoint="https://mock.openai.azure.com/",
            api_key="mock-key"
        )
        logger.warning("Using MockAzureOpenAIClient - responses will be simulated")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Simulate chat completion"""
        import asyncio
        await asyncio.sleep(0.1)  # Simulate API latency

        # Extract last user message
        user_messages = [m for m in messages if m.get("role") == "user"]
        last_message = user_messages[-1]["content"] if user_messages else ""

        # Generate mock response
        mock_response = f"""I understand you want to know about: {last_message[:100]}

As an AI assistant powered by Azure OpenAI (GPT-4o), I'm here to help. This is a simulated response for testing purposes.

Key points:
- Your request has been processed
- The system is working correctly
- Real Azure OpenAI integration is available when credentials are configured

To use real Azure OpenAI, configure your .env file with valid credentials."""

        return {
            "content": mock_response,
            "role": "assistant",
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": sum(len(m["content"].split()) for m in messages),
                "completion_tokens": len(mock_response.split()),
                "total_tokens": sum(len(m["content"].split()) for m in messages) + len(mock_response.split())
            },
            "model": self.config.deployment_name
        }

    async def generate_embedding(self, text: str, deployment: Optional[str] = None) -> List[float]:
        """Simulate embedding generation"""
        import hashlib
        import math

        # Create deterministic pseudo-embedding from text
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert to 1536-dimensional vector (standard for text-embedding-ada-002)
        embedding = []
        for i in range(1536):
            idx = i % len(hash_bytes)
            val = hash_bytes[idx] / 255.0
            embedding.append(val)

        # Normalize
        norm = math.sqrt(sum(x * x for x in embedding))
        if norm > 0:
            embedding = [x / norm for x in embedding]

        return embedding

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        deployment: Optional[str] = None
    ) -> List[List[float]]:
        """Simulate batch embedding generation"""
        return [await self.generate_embedding(text, deployment) for text in texts]


def get_azure_client(use_mock: bool = False) -> AzureOpenAIClient:
    """
    Get Azure OpenAI client (real or mock)

    Args:
        use_mock: If True, return mock client for testing

    Returns:
        AzureOpenAIClient or MockAzureOpenAIClient
    """
    if use_mock or not AZURE_AVAILABLE:
        return MockAzureOpenAIClient()

    try:
        return AzureOpenAIClient()
    except Exception as e:
        logger.warning(f"Failed to initialize Azure client: {e}. Using mock client.")
        return MockAzureOpenAIClient()
