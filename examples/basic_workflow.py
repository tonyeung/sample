"""
Basic Workflow Example

This example demonstrates:
1. Setting up multiple agents
2. Creating a workflow with human-in-the-loop
3. Data ingestion and hybrid search
4. Agent coordination
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import ResearchAgent, DataAnalystAgent, CodeExecutorAgent
from src.core import Orchestrator, WorkflowStep, WorkflowStatus, ContextualMemory
from src.data import HybridSearchKnowledgeBase, DataIngestionPipeline
from src.mcp import MCPServer, MCPToolRegistry, ToolType, ToolParameter


async def human_approval_callback(message: str, context: dict) -> bool:
    """
    Human-in-the-loop approval callback.
    In a real system, this would prompt the user for input.
    """
    print("\n" + "=" * 60)
    print("🔔 HUMAN APPROVAL REQUIRED")
    print("=" * 60)
    print(f"Action: {message}")
    print(f"Context: {context}")
    print("=" * 60)

    # For demo purposes, auto-approve
    # In production, you would:
    # response = input("Approve? (y/n): ")
    # return response.lower() == 'y'

    print("✓ Auto-approved for demo\n")
    return True


async def main():
    """Main workflow demonstration"""

    print("=" * 60)
    print("Multi-Agent System - Basic Workflow Example")
    print("=" * 60)

    # Step 1: Initialize Knowledge Base
    print("\n1️⃣  Initializing Knowledge Base...")
    knowledge_base = HybridSearchKnowledgeBase(
        embedding_dim=384,
        index_name="demo_index"
    )

    # Step 2: Ingest Sample Data
    print("2️⃣  Ingesting Sample Data...")
    ingestion_pipeline = DataIngestionPipeline(knowledge_base)

    sample_documents = [
        {
            'content': 'Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience.',
            'metadata': {'topic': 'AI', 'category': 'education'}
        },
        {
            'content': 'Python is a versatile programming language widely used in data science, web development, and automation.',
            'metadata': {'topic': 'Programming', 'category': 'education'}
        },
        {
            'content': 'Data analysis involves inspecting, cleaning, and modeling data to discover useful information and support decision-making.',
            'metadata': {'topic': 'Data Science', 'category': 'education'}
        }
    ]

    doc_ids = await ingestion_pipeline.ingest_batch(sample_documents)
    print(f"   ✓ Ingested {len(doc_ids)} documents")

    # Step 3: Initialize Agents
    print("\n3️⃣  Initializing Agents...")

    research_agent = ResearchAgent(
        name="ResearchAgent",
        knowledge_base=knowledge_base
    )
    print("   ✓ ResearchAgent initialized")

    data_analyst = DataAnalystAgent(name="DataAnalystAgent")
    print("   ✓ DataAnalystAgent initialized")

    code_executor = CodeExecutorAgent(
        name="CodeExecutorAgent",
        max_execution_time=30
    )
    print("   ✓ CodeExecutorAgent initialized")

    # Step 4: Setup MCP Server
    print("\n4️⃣  Setting up MCP Server...")
    mcp_server = MCPServer()

    # Register a sample tool
    def calculate_statistics(numbers: list) -> dict:
        """Calculate basic statistics for a list of numbers"""
        if not numbers:
            return {'error': 'Empty list'}

        return {
            'count': len(numbers),
            'sum': sum(numbers),
            'mean': sum(numbers) / len(numbers),
            'min': min(numbers),
            'max': max(numbers)
        }

    mcp_server.tool_registry.register_tool(
        name="calculate_statistics",
        description="Calculate basic statistics for a list of numbers",
        tool_type=ToolType.FUNCTION,
        parameters=[
            ToolParameter(
                name="numbers",
                type="list",
                description="List of numbers to analyze",
                required=True
            )
        ],
        handler=calculate_statistics
    )
    print("   ✓ MCP Server configured with tools")

    # Step 5: Initialize Orchestrator with Shared Memory
    print("\n5️⃣  Initializing Orchestrator...")
    shared_memory = ContextualMemory()

    orchestrator = Orchestrator(
        agents=[research_agent, data_analyst, code_executor],
        human_approval_callback=human_approval_callback,
        shared_memory=shared_memory
    )
    print("   ✓ Orchestrator initialized with shared memory")

    # Step 6: Create and Execute Workflow
    print("\n6️⃣  Creating Workflow...")
    workflow = [
        WorkflowStep(
            agent_name="ResearchAgent",
            task="Search the knowledge base for information about machine learning",
            requires_approval=False
        ),
        WorkflowStep(
            agent_name="DataAnalystAgent",
            task="Analyze the research findings and identify key trends",
            requires_approval=False,
            dependencies=["Search the knowledge base for information about machine learning"]
        ),
        WorkflowStep(
            agent_name="CodeExecutorAgent",
            task="Execute Python code to calculate statistics: numbers = [1, 2, 3, 4, 5]",
            requires_approval=True  # Code execution requires approval
        )
    ]

    print(f"   ✓ Created workflow with {len(workflow)} steps")

    # Step 7: Execute Workflow
    print("\n7️⃣  Executing Workflow...\n")
    results = await orchestrator.execute_workflow(workflow)

    # Step 8: Display Results
    print("\n8️⃣  Workflow Results:")
    print("=" * 60)
    print(f"Total Steps: {results['total_steps']}")
    print(f"Completed: {results['completed']}")
    print(f"Failed: {results['failed']}")
    print(f"Cancelled: {results['cancelled']}")
    print("=" * 60)

    for i, step_result in enumerate(results['steps'], 1):
        print(f"\nStep {i}: {step_result['step']}")
        print(f"Agent: {step_result['agent']}")
        print(f"Status: {step_result['status']}")
        print(f"Success: {step_result['success']}")
        if 'response' in step_result:
            print(f"Response Preview: {step_result['response'][:200]}...")

    # Step 9: Test Hybrid Search
    print("\n9️⃣  Testing Hybrid Search...")
    search_results = await knowledge_base.search(
        query="What is machine learning?",
        top_k=3,
        search_type="hybrid"
    )

    print(f"\nFound {len(search_results)} results:")
    for i, result in enumerate(search_results, 1):
        print(f"\n{i}. Score: {result.score:.3f} (Type: {result.match_type})")
        print(f"   Content: {result.document.content[:100]}...")
        if result.matched_terms:
            print(f"   Matched Terms: {', '.join(result.matched_terms)}")

    # Step 10: Display Memory State
    print("\n🔟 Shared Memory State:")
    print("=" * 60)
    print(shared_memory.get_context_summary(max_items=5))
    print("=" * 60)

    # Step 11: Agent Status
    print("\n1️⃣1️⃣  Agent Status:")
    agent_status = orchestrator.get_agent_status()
    for agent_name, capabilities in agent_status.items():
        print(f"\n{agent_name}:")
        print(f"  Role: {capabilities['role']}")
        print(f"  Tools: {len(capabilities['tools'])}")
        print(f"  Memory Enabled: {capabilities['memory_enabled']}")

    # Step 12: MCP Server Stats
    print("\n1️⃣2️⃣  MCP Server Statistics:")
    mcp_stats = mcp_server.get_server_stats()
    for key, value in mcp_stats.items():
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("✅ Workflow Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
