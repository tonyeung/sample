# Multi-Agent System

A comprehensive multi-agent system built with Python, featuring autonomous agents, hybrid search, contextual learning, and MCP integration.

## 🌟 Features

### ✅ All Requirements Met

1. **Multiple Specialized Agents** (3+ agents)
   - 🔬 **ResearchAgent**: Information gathering and analysis
   - 📊 **DataAnalystAgent**: Data processing and insights generation
   - 💻 **CodeExecutorAgent**: Safe code execution and function calling

2. **Human-in-the-Loop**
   - Approval workflows for critical operations
   - Customizable approval callbacks
   - Risk assessment for agent actions

3. **Data Ingestion with Hybrid Search**
   - Vector-based semantic search
   - Keyword-based search
   - Hybrid search combining both approaches
   - Support for multiple file formats (TXT, JSON, MD)

4. **Contextual Learning**
   - Short-term and long-term memory
   - Pattern learning and recall
   - Entity tracking
   - Memory consolidation

5. **Code Execution & Function Calling**
   - Safe Python code execution
   - Syntax validation
   - Error handling
   - Execution timeout protection

6. **MCP Integration** (Model Context Protocol)
   - Tool registry and management
   - Context providers
   - Resource management
   - Session tracking

## 🏗️ Architecture

```
src/
├── core/               # Core framework
│   ├── base_agent.py   # Base agent class
│   ├── memory.py       # Contextual memory system
│   └── orchestrator.py # Agent orchestration
├── agents/             # Specialized agents
│   ├── research_agent.py
│   ├── data_analyst_agent.py
│   └── code_executor_agent.py
├── data/               # Data management
│   ├── knowledge_base.py  # Hybrid search
│   └── ingestion.py       # Data ingestion
├── mcp/                # MCP integration
│   └── protocol.py     # MCP server & tools
└── tools/              # Utility tools

examples/               # Usage examples
├── basic_workflow.py
└── advanced_coordination.py
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd sample

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
import asyncio
from src.agents import ResearchAgent, DataAnalystAgent
from src.core import Orchestrator, WorkflowStep
from src.data import HybridSearchKnowledgeBase

async def main():
    # Initialize knowledge base
    kb = HybridSearchKnowledgeBase()

    # Create agents
    research = ResearchAgent(knowledge_base=kb)
    analyst = DataAnalystAgent()

    # Setup orchestrator
    orchestrator = Orchestrator(agents=[research, analyst])

    # Create workflow
    workflow = [
        WorkflowStep(
            agent_name="ResearchAgent",
            task="Research machine learning trends"
        ),
        WorkflowStep(
            agent_name="DataAnalystAgent",
            task="Analyze the research findings",
            dependencies=["Research machine learning trends"]
        )
    ]

    # Execute
    results = await orchestrator.execute_workflow(workflow)
    print(results)

asyncio.run(main())
```

## 📚 Examples

### Basic Workflow
Demonstrates core features:
```bash
python examples/basic_workflow.py
```

Features shown:
- Agent initialization
- Data ingestion
- Workflow execution with human-in-the-loop
- Hybrid search
- Shared memory

### Advanced Coordination
Shows complex agent interactions:
```bash
python examples/advanced_coordination.py
```

Features shown:
- Round-robin coordination
- Multi-phase pipelines
- Context-aware coordination
- Memory search and pattern learning
- Entity tracking

## 🔧 Configuration

### Human Approval Callback

Customize the approval process:

```python
async def custom_approval(message: str, context: dict) -> bool:
    print(f"Approval needed: {message}")
    response = input("Approve? (y/n): ")
    return response.lower() == 'y'

orchestrator = Orchestrator(
    agents=agents,
    human_approval_callback=custom_approval
)
```

### Knowledge Base Configuration

```python
knowledge_base = HybridSearchKnowledgeBase(
    embedding_dim=384,      # Embedding dimensions
    index_name="my_index"   # Index name
)
```

### Agent Configuration

```python
research_agent = ResearchAgent(
    name="MyResearcher",
    knowledge_base=kb
)

code_agent = CodeExecutorAgent(
    name="MyExecutor",
    max_execution_time=60,  # seconds
    allowed_imports=['math', 'statistics']
)
```

## 🎯 Core Concepts

### 1. Agents

Agents are autonomous entities that process messages and perform tasks:

```python
class MyAgent(BaseAgent):
    async def process_message(self, message: Message) -> AgentResponse:
        # Process the message
        return AgentResponse(
            success=True,
            content="Task completed"
        )
```

### 2. Orchestrator

Coordinates multiple agents with workflow management:

```python
# Sequential workflow
workflow = [
    WorkflowStep(agent_name="Agent1", task="Task 1"),
    WorkflowStep(
        agent_name="Agent2",
        task="Task 2",
        dependencies=["Task 1"]
    )
]

# Round-robin coordination
responses = await orchestrator.coordinate_agents(
    task="Collaborative task",
    agent_names=["Agent1", "Agent2"],
    max_rounds=3
)
```

### 3. Hybrid Search

Combines vector and keyword search:

```python
# Vector search (semantic)
results = await kb.search(
    query="machine learning",
    search_type="vector",
    top_k=5
)

# Keyword search
results = await kb.search(
    query="data preprocessing",
    search_type="keyword"
)

# Hybrid search (best of both)
results = await kb.search(
    query="AI trends",
    search_type="hybrid"
)
```

### 4. Memory & Context

Agents maintain context and learn from interactions:

```python
# Add to memory
memory.add_short_term("Important fact", importance=0.8)
memory.add_long_term("Critical knowledge", importance=0.9)

# Search memory
relevant = memory.search_memory("AI", top_k=5)

# Learn patterns
memory.learn_pattern("workflow_pattern", {
    'steps': ['research', 'analyze', 'execute']
})

# Track entities
memory.track_entity("Python", "Used for AI")
```

### 5. MCP Integration

Register and use tools:

```python
# Register a tool
mcp_server.tool_registry.register_tool(
    name="calculate",
    description="Perform calculations",
    tool_type=ToolType.FUNCTION,
    parameters=[
        ToolParameter("x", "float", "First number"),
        ToolParameter("y", "float", "Second number")
    ],
    handler=lambda x, y: x + y
)

# Execute tool
result = await mcp_server.handle_tool_call(
    ToolCall(
        tool_name="calculate",
        arguments={"x": 5, "y": 3},
        call_id="call_001"
    )
)
```

## 🧪 Testing

Run the examples to test the system:

```bash
# Basic workflow
python examples/basic_workflow.py

# Advanced features
python examples/advanced_coordination.py
```

## 📊 System Statistics

The system provides detailed statistics:

```python
# Knowledge base stats
kb_stats = knowledge_base.get_stats()

# Agent stats
research_summary = research_agent.get_research_summary()
code_summary = code_agent.get_execution_summary()

# Orchestrator stats
agent_status = orchestrator.get_agent_status()

# MCP stats
mcp_stats = mcp_server.get_server_stats()
```

## 🔒 Safety Features

### Code Execution Safety

- Syntax validation before execution
- Restricted imports
- Execution timeouts
- Error handling and recovery
- Human approval for dangerous operations

### Dangerous Operation Detection

```python
# These operations require approval:
- File system access (open, delete)
- System commands (os.system, subprocess)
- Dynamic code execution (eval, exec)
- Network operations
```

## 🎨 Extending the System

### Add a New Agent

```python
class CustomAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(
            name=name,
            role="custom",
            system_prompt="Your custom prompt"
        )

    async def process_message(self, message: Message) -> AgentResponse:
        # Your custom logic
        return AgentResponse(
            success=True,
            content="Custom response"
        )
```

### Register Custom Tools

```python
def my_tool(param1: str, param2: int) -> dict:
    """Custom tool logic"""
    return {"result": f"{param1} * {param2}"}

mcp_server.tool_registry.register_tool(
    name="my_tool",
    description="My custom tool",
    tool_type=ToolType.CUSTOM,
    parameters=[...],
    handler=my_tool
)
```

## 📖 References

This implementation is inspired by the [Azure Multi-Agent Workshop](https://github.com/Azure-Samples/multi-agent-workshop) and implements modern multi-agent patterns including:

- Agent coordination and orchestration
- Human-in-the-loop workflows
- Contextual memory and learning
- Hybrid search capabilities
- Model Context Protocol (MCP)

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 📧 Contact

For questions or support, please open an issue in the repository.

---

Built with ❤️ using Python and inspired by Azure Multi-Agent Workshop
