"""
Azure-Integrated Basic Workflow Example

Demonstrates multi-agent system using Microsoft Azure stack:
- Azure OpenAI for LLM inference
- AutoGen for agent coordination
- Azure embeddings for semantic search
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables only.")
    pass

from src.agents import ResearchAgent, DataAnalystAgent, CodeExecutorAgent
from src.core import Orchestrator, WorkflowStep, ContextualMemory
from src.data import HybridSearchKnowledgeBase, DataIngestionPipeline

# Azure imports
try:
    from src.azure import (
        AzureOpenAIClient,
        AzureConfig,
        get_azure_client,
        AutoGenAgent,
        AutoGenTeam,
        create_autogen_model_client,
        AUTOGEN_AVAILABLE
    )
    azure_available = True
except ImportError:
    azure_available = False
    print("⚠️  Azure modules not available. Install with: pip install openai azure-identity")


async def human_approval_callback(message: str, context: dict) -> bool:
    """Human-in-the-loop approval"""
    print("\n" + "=" * 60)
    print("🔔 HUMAN APPROVAL REQUIRED")
    print("=" * 60)
    print(f"Action: {message}")
    print(f"Context: {context}")
    print("=" * 60)
    print("✓ Auto-approved for demo\n")
    return True


async def main():
    """Main Azure-integrated workflow"""

    print("=" * 60)
    print("Multi-Agent System - Azure Integration Demo")
    print("=" * 60)

    # Check Azure configuration
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_key = os.getenv("AZURE_OPENAI_API_KEY")

    if not azure_endpoint:
        print("\n⚠️  Azure OpenAI not configured. Using mock mode.")
        print("To use real Azure OpenAI:")
        print("1. Copy .env.example to .env")
        print("2. Fill in your Azure OpenAI credentials")
        print("3. Run again\n")
        use_azure = False
    else:
        print(f"\n✓ Azure OpenAI configured: {azure_endpoint}")
        use_azure = True

    # Step 1: Initialize Azure OpenAI Client
    print("\n1️⃣  Initializing Azure OpenAI Client...")
    azure_client = get_azure_client(use_mock=not use_azure)

    if use_azure:
        print(f"   ✓ Connected to Azure OpenAI")
        print(f"   Endpoint: {azure_endpoint}")
        print(f"   Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')}")
    else:
        print("   ✓ Using mock client (for testing without Azure)")

    # Step 2: Test Azure OpenAI Connection
    print("\n2️⃣  Testing Azure OpenAI Connection...")
    try:
        test_response = await azure_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Azure OpenAI is working!' in one sentence."}
            ],
            max_tokens=50
        )
        print(f"   ✓ Response: {test_response['content'][:100]}")
        if use_azure:
            print(f"   Tokens used: {test_response['usage']['total_tokens']}")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")
        print("   Continuing with standard agents...")

    # Step 3: Initialize Knowledge Base with Azure Embeddings
    print("\n3️⃣  Initializing Knowledge Base...")
    knowledge_base = HybridSearchKnowledgeBase(
        embedding_dim=1536 if use_azure else 384  # Azure uses 1536-dim embeddings
    )
    print("   ✓ Knowledge Base initialized")

    # Step 4: Ingest Sample Data
    print("\n4️⃣  Ingesting Sample Data...")
    ingestion = DataIngestionPipeline(knowledge_base)

    sample_documents = [
        {
            'content': '''Azure OpenAI Service provides REST API access to OpenAI's powerful language models
            including GPT-4, GPT-3.5-Turbo, and Embeddings. The service offers enterprise-grade security,
            compliance, and regional availability.''',
            'metadata': {'topic': 'Azure', 'category': 'AI Services'}
        },
        {
            'content': '''AutoGen is a Microsoft framework for building multi-agent applications. It enables
            developers to create agents that can collaborate, use tools, and accomplish complex tasks through
            natural conversation.''',
            'metadata': {'topic': 'AutoGen', 'category': 'Framework'}
        },
        {
            'content': '''Multi-agent systems allow autonomous agents to work together on complex problems.
            Each agent specializes in specific tasks and communicates with others to achieve shared goals.''',
            'metadata': {'topic': 'Multi-Agent Systems', 'category': 'AI Architecture'}
        }
    ]

    # Generate embeddings using Azure if available
    if use_azure:
        print("   Generating embeddings with Azure OpenAI...")
        for doc in sample_documents:
            try:
                embedding = await azure_client.generate_embedding(doc['content'])
                doc['embedding'] = embedding
            except Exception as e:
                print(f"   ⚠️  Embedding error: {e}")

    doc_ids = await ingestion.ingest_batch(sample_documents)
    print(f"   ✓ Ingested {len(doc_ids)} documents")

    # Step 5: Initialize Standard Agents
    print("\n5️⃣  Initializing Agents...")
    research_agent = ResearchAgent(name="AzureResearcher", knowledge_base=knowledge_base)
    analyst_agent = DataAnalystAgent(name="AzureAnalyst")
    code_agent = CodeExecutorAgent(name="AzureExecutor")
    print("   ✓ Standard agents initialized")

    # Step 6: Optional AutoGen Integration
    if AUTOGEN_AVAILABLE and use_azure:
        print("\n6️⃣  Setting up AutoGen Integration...")
        try:
            # Create AutoGen model client
            model_client = create_autogen_model_client(
                endpoint=azure_endpoint,
                api_key=azure_key,
                deployment_name=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o')
            )

            # Create AutoGen agents
            autogen_researcher = AutoGenAgent(
                name="AutoGenResearcher",
                role="research",
                system_prompt="You are a research specialist focused on Azure and AI technologies.",
                model_client=model_client
            )

            autogen_analyst = AutoGenAgent(
                name="AutoGenAnalyst",
                role="analyst",
                system_prompt="You are a data analyst who provides insights on technology trends.",
                model_client=model_client
            )

            # Create AutoGen team
            autogen_team = AutoGenTeam(
                agents=[autogen_researcher, autogen_analyst],
                termination_condition="TERMINATE",
                max_rounds=5
            )

            print("   ✓ AutoGen team created")
            use_autogen = True

        except Exception as e:
            print(f"   ⚠️  AutoGen setup failed: {e}")
            use_autogen = False
    else:
        print("\n6️⃣  Skipping AutoGen (not available or Azure not configured)")
        use_autogen = False

    # Step 7: Initialize Orchestrator
    print("\n7️⃣  Initializing Orchestrator...")
    shared_memory = ContextualMemory()
    orchestrator = Orchestrator(
        agents=[research_agent, analyst_agent, code_agent],
        human_approval_callback=human_approval_callback,
        shared_memory=shared_memory
    )
    print("   ✓ Orchestrator ready")

    # Step 8: Execute Standard Workflow
    print("\n8️⃣  Executing Standard Workflow...")
    workflow = [
        WorkflowStep(
            agent_name="AzureResearcher",
            task="Search for information about Azure OpenAI Service",
            requires_approval=False
        ),
        WorkflowStep(
            agent_name="AzureAnalyst",
            task="Analyze the Azure OpenAI features and benefits",
            requires_approval=False,
            dependencies=["Search for information about Azure OpenAI Service"]
        ),
        WorkflowStep(
            agent_name="AzureExecutor",
            task="Generate sample code for Azure OpenAI integration",
            requires_approval=True
        )
    ]

    print(f"\n   Workflow: {len(workflow)} steps")
    results = await orchestrator.execute_workflow(workflow)

    print("\n   Results:")
    print(f"   ✓ Completed: {results['completed']}/{results['total_steps']}")
    print(f"   ✓ Failed: {results['failed']}")

    for i, step in enumerate(results['steps'], 1):
        print(f"\n   Step {i}: {step['agent']}")
        print(f"   Status: {step['status']}")
        if 'response' in step:
            print(f"   Preview: {step['response'][:150]}...")

    # Step 9: AutoGen Team Execution (if available)
    if use_autogen:
        print("\n9️⃣  Executing AutoGen Team Coordination...")
        try:
            autogen_task = "Discuss the benefits of using Azure OpenAI with AutoGen for multi-agent systems"
            print(f"   Task: {autogen_task}")

            autogen_results = await autogen_team.run(autogen_task)

            print(f"\n   ✓ AutoGen team completed")
            print(f"   Messages exchanged: {len(autogen_results)}")

            for i, msg in enumerate(autogen_results[:3], 1):  # Show first 3
                print(f"\n   Message {i}:")
                print(f"   From: {msg.get('sender', 'unknown')}")
                print(f"   Content: {msg.get('content', '')[:150]}...")

        except Exception as e:
            print(f"   ⚠️  AutoGen execution error: {e}")

    # Step 10: Test Hybrid Search with Azure Embeddings
    print("\n🔟 Testing Hybrid Search...")
    search_query = "What is Azure OpenAI?"

    if use_azure:
        try:
            # Generate query embedding with Azure
            query_embedding = await azure_client.generate_embedding(search_query)
            print("   ✓ Generated query embedding with Azure")
        except Exception as e:
            print(f"   ⚠️  Embedding error: {e}")

    search_results = await knowledge_base.search(
        query=search_query,
        top_k=3,
        search_type="hybrid"
    )

    print(f"\n   Found {len(search_results)} results:")
    for i, result in enumerate(search_results, 1):
        print(f"\n   {i}. Score: {result.score:.3f}")
        print(f"      Content: {result.document.content[:100]}...")

    # Step 11: Display Statistics
    print("\n1️⃣1️⃣  System Statistics:")
    print("=" * 60)

    kb_stats = knowledge_base.get_stats()
    print(f"\nKnowledge Base:")
    print(f"   Documents: {kb_stats['total_documents']}")
    print(f"   Searches: {kb_stats['total_searches']}")

    print(f"\nShared Memory:")
    print(f"   Short-term: {len(shared_memory.short_term_memory)} entries")
    print(f"   Long-term: {len(shared_memory.long_term_memory)} entries")

    if use_azure:
        print(f"\nAzure Integration:")
        print(f"   ✓ Azure OpenAI: Connected")
        print(f"   ✓ Embeddings: Azure-generated")
        if use_autogen:
            print(f"   ✓ AutoGen: Active")

    print("\n" + "=" * 60)
    print("✅ Azure Integration Demo Complete!")
    print("=" * 60)

    # Tips for production use
    if not use_azure:
        print("\n💡 Tips for Production:")
        print("1. Configure Azure OpenAI in .env file")
        print("2. Use managed identity for authentication")
        print("3. Enable AutoGen for advanced coordination")
        print("4. Consider Azure Container Apps for code execution")


if __name__ == "__main__":
    asyncio.run(main())
