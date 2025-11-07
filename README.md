# Multi-Agent System

A comprehensive multi-agent system built with Python, featuring autonomous agents, hybrid search, contextual learning, and MCP integration.

**Powered by Microsoft Azure Stack:**
- 🔷 Azure OpenAI (GPT-4o)
- 🤖 AutoGen 0.4 Framework
- ☁️ Azure AI Services
- 🔐 Enterprise Security

> 📘 **New!** See [EXECUTION_FLOW.md](EXECUTION_FLOW.md) for a detailed explanation of code execution from prompt to response.
>
> 🔧 **New!** See [AZURE_SETUP.md](AZURE_SETUP.md) for complete Azure deployment guide.

## 🚀 Quick Start Options

### Option 1: Azure Integration (Recommended)
Uses Microsoft Azure OpenAI and AutoGen for production-ready multi-agent coordination.

```bash
# Setup
cp .env.example .env
# Edit .env with your Azure credentials
pip install -r requirements.txt

# Run
python examples/azure_basic_workflow.py
```

**See [AZURE_SETUP.md](AZURE_SETUP.md) for detailed Azure setup instructions.**

### Option 2: Standalone Mode
Run without Azure using mock clients for testing.

```bash
pip install numpy pandas aiofiles
python examples/basic_workflow.py
```

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
├── azure/              # 🆕 Azure integration
│   ├── azure_client.py     # Azure OpenAI client
│   └── autogen_integration.py  # AutoGen framework
└── tools/              # Utility tools

examples/               # Usage examples
├── basic_workflow.py
├── advanced_coordination.py
└── azure_basic_workflow.py  # 🆕 Azure integration example
```

## 📖 Documentation

- **[EXECUTION_FLOW.md](EXECUTION_FLOW.md)**: Detailed code execution flow from prompt to response
- **[AZURE_SETUP.md](AZURE_SETUP.md)**: Complete Azure deployment and configuration guide
- **[README.md](README.md)**: This file - overview and quick start

## 💻 Installation

### Prerequisites

- Python 3.9 or higher
- (Optional) Azure OpenAI Service with GPT-4o deployment
- (Optional) Azure subscription for full features

### Install Dependencies

```bash
# Full installation (with Azure support)
pip install -r requirements.txt

# Minimal installation (standalone mode)
pip install numpy pandas aiofiles
```

### Configure Azure (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit with your Azure credentials
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_API_KEY=your-key-here
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
```

See [AZURE_SETUP.md](AZURE_SETUP.md) for complete setup instructions.

## 🎯 Usage Examples

### Example 1: Azure-Integrated Workflow

```python
import asyncio
from src.azure import get_azure_client, AutoGenTeam, AutoGenAgent, create_autogen_model_client

async def main():
    # Initialize Azure OpenAI client
    azure_client = get_azure_client()

    # Create AutoGen model client
    model_client = create_autogen_model_client(
        endpoint="https://your-resource.openai.azure.com/",
        api_key="your-key",
        deployment_name="gpt-4o"
    )

    # Create AutoGen agents
    researcher = AutoGenAgent(
        name="Researcher",
        role="research",
        system_prompt="You are a research specialist.",
        model_client=model_client
    )

    analyst = AutoGenAgent(
        name="Analyst",
        role="analyst",
        system_prompt="You are a data analyst.",
        model_client=model_client
    )

    # Create team for coordination
    team = AutoGenTeam(
        agents=[researcher, analyst],
        max_rounds=10
    )

    # Execute collaborative task
    result = await team.run("Research AI trends and provide analysis")
    print(result)

asyncio.run(main())
```

**Run the example:**
```bash
python examples/azure_basic_workflow.py
```

### Example 2: Standalone Workflow

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

**Run the example:**
```bash
python examples/basic_workflow.py
```

## 📚 Examples

### Azure Integration Example
**File**: `examples/azure_basic_workflow.py`

Demonstrates Microsoft Azure stack integration:
```bash
python examples/azure_basic_workflow.py
```

Features shown:
- Azure OpenAI client setup
- AutoGen multi-agent coordination
- Azure embeddings for semantic search
- Managed identity support
- Enterprise-grade security

### Basic Workflow
**File**: `examples/basic_workflow.py`

Demonstrates core features in standalone mode:
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
**File**: `examples/advanced_coordination.py`

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

## 🔍 Execution Flow

Understanding how a prompt flows through the system:

```
User Prompt → Orchestrator → Agent Selection → Azure OpenAI (optional)
    ↓              ↓              ↓                    ↓
Workflow → Dependencies → Message → Knowledge Base → Embeddings
    ↓              ↓              ↓                    ↓
Results ← Memory Update ← Processing ← Hybrid Search ← Response
```

**Detailed flow documentation**: See [EXECUTION_FLOW.md](EXECUTION_FLOW.md)

Key components in the flow:
1. **Orchestrator** (`src/core/orchestrator.py:45`) - Manages workflow
2. **Agent Processing** (`src/agents/*.py`) - Specialized task handling
3. **Hybrid Search** (`src/data/knowledge_base.py:151`) - Vector + keyword search
4. **Azure OpenAI** (`src/azure/azure_client.py:90`) - LLM inference
5. **Memory** (`src/core/memory.py`) - Contextual learning
6. **Response Assembly** - Aggregates and returns results

## 📖 References

This implementation is inspired by the [Azure Multi-Agent Workshop](https://github.com/Azure-Samples/multi-agent-workshop) and implements modern multi-agent patterns including:

- **Microsoft Azure Stack**: Azure OpenAI, AutoGen 0.4, Azure AI Foundry
- **Agent Coordination**: RoundRobinGroupChat, termination conditions
- **Human-in-the-Loop**: Approval workflows and safety checks
- **Contextual Learning**: Short/long-term memory with consolidation
- **Hybrid Search**: Vector embeddings + keyword matching
- **Model Context Protocol**: MCP tool and context management
- **Enterprise Security**: Managed identity, key rotation, network security

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 📧 Contact

For questions or support, please open an issue in the repository.

---

Built with ❤️ using Python and inspired by Azure Multi-Agent Workshop
