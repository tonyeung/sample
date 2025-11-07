"""
Advanced Agent Coordination Example

This example demonstrates:
1. Round-robin agent coordination
2. Complex agent interactions
3. Context sharing between agents
4. Dynamic workflow adaptation
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import ResearchAgent, DataAnalystAgent, CodeExecutorAgent
from src.core import Orchestrator, ContextualMemory, Message
from src.data import HybridSearchKnowledgeBase, DataIngestionPipeline


async def main():
    """Advanced coordination demonstration"""

    print("=" * 60)
    print("Multi-Agent System - Advanced Coordination")
    print("=" * 60)

    # Initialize knowledge base with sample data
    print("\n📚 Initializing Knowledge Base...")
    knowledge_base = HybridSearchKnowledgeBase()
    ingestion = DataIngestionPipeline(knowledge_base)

    # Ingest technical documentation
    tech_docs = [
        {
            'content': '''
            Asynchronous programming in Python allows you to write concurrent code using
            the async/await syntax. This is particularly useful for I/O-bound operations
            where you want to avoid blocking the main thread while waiting for responses.
            ''',
            'metadata': {'topic': 'Python', 'subtopic': 'Async'}
        },
        {
            'content': '''
            Data preprocessing is a crucial step in machine learning. It involves cleaning
            data, handling missing values, normalizing features, and encoding categorical
            variables. Proper preprocessing can significantly improve model performance.
            ''',
            'metadata': {'topic': 'ML', 'subtopic': 'Preprocessing'}
        },
        {
            'content': '''
            Statistical analysis helps in understanding data distributions, correlations,
            and relationships. Common techniques include hypothesis testing, regression
            analysis, and ANOVA. These methods provide insights into data patterns.
            ''',
            'metadata': {'topic': 'Statistics', 'subtopic': 'Analysis'}
        }
    ]

    await ingestion.ingest_batch(tech_docs)
    print(f"   ✓ Ingested {len(tech_docs)} technical documents")

    # Initialize agents
    print("\n🤖 Initializing Specialized Agents...")
    research_agent = ResearchAgent(name="TechResearcher", knowledge_base=knowledge_base)
    analyst_agent = DataAnalystAgent(name="DataExpert")
    code_agent = CodeExecutorAgent(name="CodeRunner")

    # Setup orchestrator with shared memory
    shared_memory = ContextualMemory()
    orchestrator = Orchestrator(
        agents=[research_agent, analyst_agent, code_agent],
        shared_memory=shared_memory
    )

    print("   ✓ Agents initialized and ready")

    # Example 1: Research and Analysis Coordination
    print("\n" + "=" * 60)
    print("Example 1: Research → Analysis Coordination")
    print("=" * 60)

    task1 = "Research best practices for data preprocessing in machine learning"

    print(f"\n📋 Task: {task1}")
    print("\n🔄 Coordinating agents...")

    responses = await orchestrator.coordinate_agents(
        task=task1,
        agent_names=["TechResearcher", "DataExpert"],
        max_rounds=2
    )

    print(f"\n✅ Received {len(responses)} responses")
    for i, response in enumerate(responses, 1):
        print(f"\nResponse {i}:")
        print(f"  Success: {response.success}")
        print(f"  Preview: {response.content[:150]}...")

    # Example 2: Multi-Agent Collaboration with Code Execution
    print("\n" + "=" * 60)
    print("Example 2: Research → Code → Analysis Pipeline")
    print("=" * 60)

    # Research phase
    print("\n📊 Phase 1: Research")
    research_message = Message(
        role='user',
        content='Find information about statistical analysis methods',
        sender='coordinator'
    )
    research_response = await research_agent.process_message(research_message)
    print(f"   ✓ Research completed: {research_response.success}")

    # Add to shared memory
    shared_memory.add_long_term(
        content=f"Research findings: {research_response.content[:200]}",
        metadata={'phase': 'research', 'agent': 'TechResearcher'},
        importance=0.8
    )

    # Code execution phase
    print("\n💻 Phase 2: Code Execution")
    code_message = Message(
        role='user',
        content='''
import statistics

# Sample data
data = [23, 45, 67, 89, 12, 34, 56, 78, 90, 21]

# Calculate statistics
mean_val = statistics.mean(data)
median_val = statistics.median(data)
stdev_val = statistics.stdev(data)

result = {
    'mean': mean_val,
    'median': median_val,
    'stdev': stdev_val,
    'sample_size': len(data)
}

print(f"Statistics: {result}")
''',
        sender='coordinator'
    )
    code_response = await code_agent.process_message(code_message)
    print(f"   ✓ Code executed: {code_response.success}")

    # Add to shared memory
    shared_memory.add_long_term(
        content=f"Code execution: {code_response.content[:200]}",
        metadata={'phase': 'execution', 'agent': 'CodeRunner'},
        importance=0.9
    )

    # Analysis phase
    print("\n📈 Phase 3: Data Analysis")
    analysis_message = Message(
        role='user',
        content='Analyze the statistical results and provide insights',
        sender='coordinator'
    )
    analysis_response = await analyst_agent.process_message(analysis_message)
    print(f"   ✓ Analysis completed: {analysis_response.success}")

    # Example 3: Context-Aware Coordination
    print("\n" + "=" * 60)
    print("Example 3: Context-Aware Agent Coordination")
    print("=" * 60)

    # Learn a pattern
    shared_memory.learn_pattern(
        'data_pipeline',
        {
            'steps': ['research', 'code_execution', 'analysis'],
            'coordination': 'sequential',
            'success_rate': 0.95
        }
    )

    # Track entities
    shared_memory.track_entity('Python', 'Used for async programming')
    shared_memory.track_entity('Python', 'Popular for data science')
    shared_memory.track_entity('Statistics', 'Used for data analysis')

    print("\n🧠 Contextual Memory State:")
    print(f"   Short-term memories: {len(shared_memory.short_term_memory)}")
    print(f"   Long-term memories: {len(shared_memory.long_term_memory)}")
    print(f"   Learned patterns: {len(shared_memory.learned_patterns)}")
    print(f"   Tracked entities: {len(shared_memory.entity_memory)}")

    # Search memory
    print("\n🔍 Memory Search: 'statistical analysis'")
    relevant_memories = shared_memory.search_memory('statistical analysis', top_k=3)
    for i, memory in enumerate(relevant_memories, 1):
        print(f"\n   {i}. {memory.content[:100]}...")
        print(f"      Importance: {memory.importance:.2f}")

    # Display learned patterns
    print("\n📚 Learned Patterns:")
    data_pipeline = shared_memory.recall_pattern('data_pipeline')
    if data_pipeline:
        print(f"   Pattern: data_pipeline")
        print(f"   Steps: {data_pipeline['steps']}")
        print(f"   Coordination: {data_pipeline['coordination']}")
        print(f"   Success Rate: {data_pipeline['success_rate']}")

    # Display entity knowledge
    print("\n🏷️  Entity Knowledge:")
    for entity in ['Python', 'Statistics']:
        info = shared_memory.get_entity_info(entity)
        print(f"\n   {entity}:")
        for fact in info:
            print(f"     - {fact}")

    # Example 4: Hybrid Search Demonstration
    print("\n" + "=" * 60)
    print("Example 4: Hybrid Search Capabilities")
    print("=" * 60)

    search_queries = [
        ("async programming", "vector"),
        ("data preprocessing", "keyword"),
        ("statistical methods", "hybrid")
    ]

    for query, search_type in search_queries:
        print(f"\n🔎 Query: '{query}' (Type: {search_type})")
        results = await knowledge_base.search(query, top_k=2, search_type=search_type)

        for i, result in enumerate(results, 1):
            print(f"\n   {i}. Score: {result.score:.3f}")
            print(f"      Type: {result.match_type}")
            print(f"      Content: {result.document.content[:80].strip()}...")
            if result.matched_terms:
                print(f"      Matched: {', '.join(result.matched_terms[:3])}")

    # Final Statistics
    print("\n" + "=" * 60)
    print("📊 Final Statistics")
    print("=" * 60)

    kb_stats = knowledge_base.get_stats()
    print(f"\nKnowledge Base:")
    print(f"   Total Documents: {kb_stats['total_documents']}")
    print(f"   Total Searches: {kb_stats['total_searches']}")
    print(f"   Index Size: {kb_stats['vector_index_size']}")

    research_summary = research_agent.get_research_summary()
    print(f"\nResearch Agent:")
    print(f"   Total Queries: {research_summary['total_queries']}")
    print(f"   Memory Entries: {research_summary['memory_entries']}")

    analyst_summary = analyst_agent.get_analysis_summary()
    print(f"\nData Analyst Agent:")
    print(f"   Total Analyses: {analyst_summary['total_analyses']}")
    print(f"   Datasets Loaded: {analyst_summary['datasets_loaded']}")

    code_summary = code_agent.get_execution_summary()
    print(f"\nCode Executor Agent:")
    print(f"   Total Executions: {code_summary['total_executions']}")
    print(f"   Successful: {code_summary['successful']}")
    print(f"   Failed: {code_summary['failed']}")

    print("\n" + "=" * 60)
    print("✅ Advanced Coordination Demo Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
