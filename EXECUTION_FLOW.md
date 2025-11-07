# Multi-Agent System Execution Flow

This document explains the complete code execution flow from a user prompt to the final response in the multi-agent system.

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Detailed Execution Flow](#detailed-execution-flow)
4. [Component Interactions](#component-interactions)
5. [Azure Integration Flow](#azure-integration-flow)
6. [Examples](#examples)

---

## Overview

The multi-agent system processes user prompts through multiple layers, coordinating specialized agents to accomplish complex tasks. The system integrates with Azure OpenAI and AutoGen for intelligent agent coordination.

### High-Level Flow

```
User Prompt → Orchestrator → Agent Selection → Azure OpenAI → Processing → Response
```

---

## Architecture Layers

### Layer 1: User Interface
- **Entry Point**: User submits a prompt or task
- **Location**: `examples/basic_workflow.py` or `examples/advanced_coordination.py`

### Layer 2: Orchestration
- **Component**: `Orchestrator` (`src/core/orchestrator.py`)
- **Responsibility**: Workflow management, agent coordination, human-in-the-loop

### Layer 3: Agent Processing
- **Components**: `ResearchAgent`, `DataAnalystAgent`, `CodeExecutorAgent`
- **Location**: `src/agents/`
- **Responsibility**: Specialized task processing

### Layer 4: Azure Services
- **Components**: `AzureOpenAIClient`, `AutoGenTeam`
- **Location**: `src/azure/`
- **Responsibility**: LLM inference, embeddings, agent coordination

### Layer 5: Data & Tools
- **Components**: `HybridSearchKnowledgeBase`, `MCPServer`
- **Location**: `src/data/`, `src/mcp/`
- **Responsibility**: Knowledge retrieval, tool execution

---

## Detailed Execution Flow

### 1. Initial Request Reception

```python
# User code (examples/basic_workflow.py)
workflow = [
    WorkflowStep(
        agent_name="ResearchAgent",
        task="Search for information about machine learning"
    )
]

results = await orchestrator.execute_workflow(workflow)
```

**What happens:**
1. User creates a `WorkflowStep` with task description
2. Calls `orchestrator.execute_workflow()`
3. Orchestrator receives the workflow

**File**: `examples/basic_workflow.py:86-95`

---

### 2. Orchestrator Processing

```python
# src/core/orchestrator.py:45-100
async def execute_workflow(self, workflow: List[WorkflowStep]):
    for step in workflow:
        # 2.1: Check dependencies
        if not await self._check_dependencies(step, results):
            continue

        # 2.2: Get appropriate agent
        agent = self.agents.get(step.agent_name)

        # 2.3: Check for human approval
        if step.requires_approval:
            approved = await self.human_approval_callback(...)
            if not approved:
                continue

        # 2.4: Create message for agent
        message = Message(
            role='system',
            content=step.task,
            sender='orchestrator'
        )

        # 2.5: Execute step
        response = await agent.process_message(message)
```

**Flow Steps:**

#### 2.1 Dependency Check
- **File**: `src/core/orchestrator.py:154`
- Verifies all prerequisite tasks are completed
- Checks workflow dependencies

#### 2.2 Agent Selection
- **File**: `src/core/orchestrator.py:58`
- Retrieves agent by name from registry
- Validates agent exists

#### 2.3 Human-in-the-Loop Check
- **File**: `src/core/orchestrator.py:75`
- If `requires_approval=True`, invokes callback
- Waits for human decision
- Can cancel or proceed based on response

#### 2.4 Message Creation
- **File**: `src/core/orchestrator.py:68`
- Creates `Message` object with task details
- Sets context (sender, role, metadata)

#### 2.5 Agent Invocation
- **File**: `src/core/orchestrator.py:85`
- Calls `agent.process_message(message)`
- Awaits async response

---

### 3. Agent Message Processing

Different agents have different processing logic. Let's trace **ResearchAgent**:

```python
# src/agents/research_agent.py:60
async def process_message(self, message: Message) -> AgentResponse:
    # 3.1: Add to memory
    self.add_to_memory(message)

    # 3.2: Parse and classify request
    query = message.content
    research_type = self._identify_research_type(query)

    # 3.3: Route to appropriate handler
    if research_type == "knowledge_search":
        result = await self._knowledge_search(query)

    # 3.4: Store in history
    self.research_history.append({...})

    # 3.5: Return response
    return AgentResponse(
        success=True,
        content=result,
        action_taken=f"Completed {research_type} research"
    )
```

**Flow Steps:**

#### 3.1 Memory Addition
- **File**: `src/agents/research_agent.py:64`
- Stores message in agent's conversation history
- Enables contextual learning
- **Delegates to**: `src/core/base_agent.py:65`

#### 3.2 Request Classification
- **File**: `src/agents/research_agent.py:67`
- Analyzes query content
- Determines type: `fact_check`, `document_analysis`, `knowledge_search`, etc.
- **Method**: `src/agents/research_agent.py:98`

#### 3.3 Handler Routing
- **File**: `src/agents/research_agent.py:73-80`
- Routes to specialized method based on type
- Each type has dedicated handler

#### 3.4 History Storage
- **File**: `src/agents/research_agent.py:83`
- Stores research result
- Updates agent context
- Enables learning from past interactions

#### 3.5 Response Creation
- **File**: `src/agents/research_agent.py:90`
- Creates `AgentResponse` object
- Includes: success status, content, metadata
- Returns to orchestrator

---

### 4. Knowledge Search Execution (Example)

When research type is "knowledge_search":

```python
# src/agents/research_agent.py:165
async def _knowledge_search(self, query: str) -> str:
    # 4.1: Check knowledge base availability
    if self.knowledge_base:
        # 4.2: Execute search
        results = await self._search_knowledge_base(query)

        # 4.3: Format results
        return f"""Knowledge Search Results for: "{query}"

Found {len(results)} relevant entries:
{self._format_search_results(results)}"""
```

**Flow Steps:**

#### 4.1 Knowledge Base Check
- Verifies KB is available and initialized
- Falls back to descriptive message if unavailable

#### 4.2 Search Execution
- **File**: `src/agents/research_agent.py:221`
- Delegates to knowledge base
- Calls `knowledge_base.search(query)`

---

### 5. Hybrid Search in Knowledge Base

```python
# src/data/knowledge_base.py:151
async def search(self, query: str, top_k: int, search_type: str):
    # 5.1: Increment search counter
    self.stats['total_searches'] += 1

    # 5.2: Route based on search type
    if search_type == "hybrid":
        results = await self._hybrid_search(query, top_k)

    # 5.3: Return results
    return results[:top_k]
```

**Flow Steps:**

#### 5.1 Statistics Update
- **File**: `src/data/knowledge_base.py:159`
- Tracks total searches
- Updates analytics

#### 5.2 Hybrid Search Execution
- **File**: `src/data/knowledge_base.py:247`
- Combines vector and keyword search
- Weighted scoring (60% vector, 40% keyword)

```python
# src/data/knowledge_base.py:247
async def _hybrid_search(self, query: str, top_k: int):
    # 5.2.1: Vector search
    vector_results = await self._vector_search(query, top_k * 2)

    # 5.2.2: Keyword search
    keyword_results = await self._keyword_search(query, top_k * 2)

    # 5.2.3: Combine with weighted scoring
    combined_scores = defaultdict(lambda: {'vector': 0.0, 'keyword': 0.0})

    for result in vector_results:
        combined_scores[doc_id]['vector'] = result.score * 0.6

    for result in keyword_results:
        combined_scores[doc_id]['keyword'] = result.score * 0.4

    # 5.2.4: Final scoring
    final_score = scores['vector'] + scores['keyword']

    return sorted_results
```

#### 5.2.1 Vector Search
- **File**: `src/data/knowledge_base.py:175`
- Generates query embedding
- Computes cosine similarity with all documents
- Returns top matches

**Vector Search Detail:**

```python
# src/data/knowledge_base.py:175
async def _vector_search(self, query: str, top_k: int):
    # Generate embedding for query
    query_embedding = await self._generate_embedding(query)

    # Calculate similarity with all documents
    for doc_id, doc_embedding in self.vector_index:
        similarity = self._cosine_similarity(query_embedding, doc_embedding)
        scored_docs.append((doc_id, similarity))

    # Sort and return top-k
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]
```

#### 5.2.2 Keyword Search
- **File**: `src/data/knowledge_base.py:211`
- Tokenizes query
- Matches against inverted index
- Scores by term frequency

**Keyword Search Detail:**

```python
# src/data/knowledge_base.py:211
async def _keyword_search(self, query: str, top_k: int):
    # Tokenize query
    query_terms = self._tokenize(query.lower())

    # Find matching documents
    for term in query_terms:
        if term in self.keyword_index:
            for doc_id in self.keyword_index[term]:
                doc_scores[doc_id] += 1.0

    # Normalize and sort
    return sorted_results[:top_k]
```

#### 5.2.3 Score Combination
- Weights: 60% semantic (vector), 40% lexical (keyword)
- Normalizes scores to 0-1 range
- Combines for final relevance score

---

### 6. Azure OpenAI Integration (Optional)

When Azure OpenAI is configured:

```python
# src/azure/azure_client.py:90
async def chat_completion(self, messages: List[Dict], ...):
    # 6.1: Call Azure OpenAI API
    response = self.client.chat.completions.create(
        model=self.config.deployment_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )

    # 6.2: Parse response
    return {
        "content": response.choices[0].message.content,
        "usage": {...},
        "model": response.model
    }
```

**Azure Integration Flow:**

```
Agent → AzureOpenAIClient → Azure OpenAI Service → GPT-4o Model → Response
```

**Authentication Options:**
1. **API Key**: Direct authentication
2. **Managed Identity**: Azure AD token provider

**File**: `src/azure/azure_client.py:52-79`

---

### 7. Response Propagation Back

After agent completes processing:

```python
# src/core/orchestrator.py:85-103
response = await agent.process_message(message)

# 7.1: Update shared memory
self.shared_memory.add_short_term(
    content=f"{step.agent_name}: {response.content}",
    metadata={'step': step.task},
    importance=0.7
)

# 7.2: Collect results
results.append({
    'step': step.task,
    'agent': step.agent_name,
    'status': step.status.value,
    'response': response.content
})

# 7.3: Return to user
return {
    'steps': results,
    'total_steps': len(workflow),
    'completed': count_completed
}
```

**Flow Steps:**

#### 7.1 Shared Memory Update
- **File**: `src/core/orchestrator.py:94`
- Adds response to shared contextual memory
- Makes result available to other agents
- Enables multi-agent learning

#### 7.2 Result Collection
- **File**: `src/core/orchestrator.py:101`
- Aggregates step results
- Tracks success/failure
- Preserves execution order

#### 7.3 Final Response
- **File**: `src/core/orchestrator.py:112`
- Returns comprehensive results to user
- Includes all step outputs
- Provides statistics

---

## Component Interactions

### Sequence Diagram: Full Request Flow

```
┌──────┐      ┌──────────────┐      ┌───────────┐      ┌──────────────┐      ┌─────────┐
│ User │      │ Orchestrator │      │   Agent   │      │ KnowledgeBase│      │  Azure  │
└──┬───┘      └──────┬───────┘      └─────┬─────┘      └──────┬───────┘      └────┬────┘
   │                 │                    │                    │                    │
   │  1. Submit      │                    │                    │                    │
   │  Workflow       │                    │                    │                    │
   ├────────────────>│                    │                    │                    │
   │                 │                    │                    │                    │
   │                 │  2. Check          │                    │                    │
   │                 │  Dependencies      │                    │                    │
   │                 ├──────┐             │                    │                    │
   │                 │      │             │                    │                    │
   │                 │<─────┘             │                    │                    │
   │                 │                    │                    │                    │
   │                 │  3. Human          │                    │                    │
   │                 │  Approval?         │                    │                    │
   │<────────────────┤                    │                    │                    │
   │                 │                    │                    │                    │
   │  4. Approve     │                    │                    │                    │
   ├────────────────>│                    │                    │                    │
   │                 │                    │                    │                    │
   │                 │  5. Process        │                    │                    │
   │                 │  Message           │                    │                    │
   │                 ├───────────────────>│                    │                    │
   │                 │                    │                    │                    │
   │                 │                    │  6. Add to         │                    │
   │                 │                    │  Memory            │                    │
   │                 │                    ├────┐               │                    │
   │                 │                    │    │               │                    │
   │                 │                    │<───┘               │                    │
   │                 │                    │                    │                    │
   │                 │                    │  7. Search         │                    │
   │                 │                    │  Knowledge         │                    │
   │                 │                    ├───────────────────>│                    │
   │                 │                    │                    │                    │
   │                 │                    │                    │  8. Hybrid Search  │
   │                 │                    │                    ├────┐               │
   │                 │                    │                    │    │               │
   │                 │                    │                    │<───┘               │
   │                 │                    │                    │                    │
   │                 │                    │                    │  9. Generate       │
   │                 │                    │                    │  Embedding         │
   │                 │                    │                    │  (Optional)        │
   │                 │                    │                    ├───────────────────>│
   │                 │                    │                    │                    │
   │                 │                    │                    │  10. Embedding     │
   │                 │                    │                    │<───────────────────┤
   │                 │                    │                    │                    │
   │                 │                    │  11. Results       │                    │
   │                 │                    │<───────────────────┤                    │
   │                 │                    │                    │                    │
   │                 │  12. Agent         │                    │                    │
   │                 │  Response          │                    │                    │
   │                 │<───────────────────┤                    │                    │
   │                 │                    │                    │                    │
   │                 │  13. Update        │                    │                    │
   │                 │  Shared Memory     │                    │                    │
   │                 ├────┐               │                    │                    │
   │                 │    │               │                    │                    │
   │                 │<───┘               │                    │                    │
   │                 │                    │                    │                    │
   │  14. Results    │                    │                    │                    │
   │<────────────────┤                    │                    │                    │
   │                 │                    │                    │                    │
```

---

## Azure Integration Flow

When using Azure OpenAI with AutoGen:

### 1. Configuration Loading

```python
# src/azure/azure_client.py:34
config = AzureConfig.from_env()
# Loads: AZURE_OPENAI_ENDPOINT, API_KEY, DEPLOYMENT_NAME
```

### 2. Client Initialization

```python
# src/azure/azure_client.py:59
client = AzureOpenAI(
    azure_endpoint=config.endpoint,
    api_key=config.api_key,
    api_version=config.api_version
)
```

### 3. Agent Creation with AutoGen

```python
# src/azure/autogen_integration.py:40
autogen_agent = AssistantAgent(
    name=name,
    model_client=azure_client,
    system_message=system_prompt
)
```

### 4. Team Coordination

```python
# src/azure/autogen_integration.py:95
team = RoundRobinGroupChat(
    agents=[agent1, agent2, agent3],
    termination_condition=TextMentionTermination("TERMINATE"),
    max_rounds=10
)
```

### 5. Execution

```python
# src/azure/autogen_integration.py:130
result = await team.run(task="Your task here")
```

### Azure Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│              Azure Multi-Agent System                    │
└─────────────────────────────────────────────────────────┘
           │
           ├──> 1. Load Azure Config (.env)
           │         ├─> Endpoint
           │         ├─> API Key / Managed Identity
           │         └─> Deployment Name
           │
           ├──> 2. Initialize Azure OpenAI Client
           │         └─> Authenticate with Azure
           │
           ├──> 3. Create AutoGen Model Client
           │         └─> AzureOpenAIChatCompletionClient
           │
           ├──> 4. Initialize AutoGen Agents
           │         ├─> AssistantAgent (Research)
           │         ├─> AssistantAgent (Analyst)
           │         └─> AssistantAgent (Executor)
           │
           ├──> 5. Form AutoGen Team
           │         └─> RoundRobinGroupChat
           │
           ├──> 6. Execute Task
           │         ├─> Agent 1 processes
           │         ├─> Agent 2 responds
           │         ├─> Agent 3 concludes
           │         └─> Check termination
           │
           └──> 7. Return Results
                     └─> Aggregated responses
```

---

## Examples

### Example 1: Simple Research Query

**User Input:**
```python
task = "Search for information about machine learning"
```

**Execution Trace:**

1. **Orchestrator** receives task
   - File: `src/core/orchestrator.py:45`

2. **ResearchAgent** selected
   - File: `src/core/orchestrator.py:58`

3. Message created and sent
   - File: `src/core/orchestrator.py:68`

4. Agent processes message
   - File: `src/agents/research_agent.py:60`

5. Classified as "knowledge_search"
   - File: `src/agents/research_agent.py:106`

6. Knowledge base searched
   - File: `src/data/knowledge_base.py:151`

7. Hybrid search executed
   - Vector search: `src/data/knowledge_base.py:175`
   - Keyword search: `src/data/knowledge_base.py:211`
   - Combination: `src/data/knowledge_base.py:247`

8. Results formatted
   - File: `src/agents/research_agent.py:234`

9. Response returned through layers
   - Agent → Orchestrator → User

**Output:**
```
Knowledge Search Results for: "machine learning"
Found 3 relevant entries:
1. Machine learning is a subset of AI... (Relevance: 0.85)
2. Deep learning is a type of ML... (Relevance: 0.72)
```

---

### Example 2: Multi-Agent Coordination

**User Input:**
```python
workflow = [
    WorkflowStep("ResearchAgent", "Research ML"),
    WorkflowStep("DataAnalystAgent", "Analyze findings", dependencies=["Research ML"]),
    WorkflowStep("CodeExecutorAgent", "Generate code", requires_approval=True)
]
```

**Execution Trace:**

1. **Step 1: Research**
   - No dependencies → Execute immediately
   - ResearchAgent processes
   - Result stored in shared memory

2. **Step 2: Analysis**
   - Check dependency "Research ML" → ✓ Completed
   - DataAnalystAgent processes
   - Accesses shared memory for context
   - Result stored

3. **Step 3: Code Execution**
   - Check `requires_approval` → True
   - Invoke human approval callback
   - Wait for approval
   - If approved → Execute
   - CodeExecutorAgent runs code
   - Return results

**Files Involved:**
- Dependency check: `src/core/orchestrator.py:154`
- Approval: `src/core/orchestrator.py:75`
- Shared memory: `src/core/orchestrator.py:94`
- Code execution: `src/agents/code_executor_agent.py:111`

---

### Example 3: AutoGen Team Execution

**User Input:**
```python
team = AutoGenTeam(agents=[research_agent, analyst_agent])
result = await team.run("Analyze AI trends")
```

**Execution Trace:**

1. **Team Initialization**
   - File: `src/azure/autogen_integration.py:95`
   - Creates RoundRobinGroupChat
   - Sets termination condition

2. **Round 1:**
   - ResearchAgent speaks
   - Searches knowledge base
   - Returns findings

3. **Round 2:**
   - DataAnalystAgent responds
   - Analyzes research data
   - Provides insights

4. **Round 3:**
   - ResearchAgent responds
   - Provides additional context

5. **Termination:**
   - Agent says "TERMINATE"
   - Team stops
   - Results aggregated

**AutoGen Coordination:**
- Team run: `src/azure/autogen_integration.py:130`
- Message streaming: `src/azure/autogen_integration.py:151`
- Termination: `src/azure/autogen_integration.py:99`

---

## Performance Considerations

### Caching
- **Knowledge Base**: In-memory document storage
- **Embeddings**: Cached after generation
- **Agent Context**: Maintained across interactions

### Async Operations
- All I/O operations are async (`await`)
- Azure API calls don't block
- Multiple agents can process in parallel

### Memory Management
- Short-term memory: 50 entries (auto-consolidation)
- Long-term memory: 500 entries (importance-based)
- Automatic cleanup of low-importance items

---

## Error Handling

### Layer-by-Layer Error Handling

1. **Orchestrator Level**
   ```python
   try:
       response = await agent.process_message(message)
   except Exception as e:
       logger.error(f"Error executing step: {str(e)}")
       step.status = WorkflowStatus.FAILED
   ```

2. **Agent Level**
   ```python
   try:
       result = await self._knowledge_search(query)
   except Exception as e:
       return AgentResponse(success=False, error=str(e))
   ```

3. **Azure Client Level**
   ```python
   try:
       response = self.client.chat.completions.create(...)
   except Exception as e:
       logger.error(f"Azure API error: {str(e)}")
       raise
   ```

---

## Summary

The multi-agent system processes prompts through a sophisticated pipeline:

1. **Orchestration**: Manages workflow and coordination
2. **Agent Processing**: Specialized task handling
3. **Knowledge Retrieval**: Hybrid search for context
4. **Azure Integration**: LLM inference and embeddings
5. **Response Assembly**: Aggregates results

Each layer is independently testable and can be enhanced without affecting others. The system supports both standalone operation and full Azure integration with AutoGen.

---

## Quick Reference

| Component | File | Key Method |
|-----------|------|------------|
| Orchestrator | `src/core/orchestrator.py` | `execute_workflow()` |
| Base Agent | `src/core/base_agent.py` | `process_message()` |
| Research Agent | `src/agents/research_agent.py` | `_knowledge_search()` |
| Hybrid Search | `src/data/knowledge_base.py` | `_hybrid_search()` |
| Azure Client | `src/azure/azure_client.py` | `chat_completion()` |
| AutoGen Team | `src/azure/autogen_integration.py` | `run()` |
| Memory | `src/core/memory.py` | `add_short_term()` |
| MCP Server | `src/mcp/protocol.py` | `execute_tool()` |

For more details, see the source code with inline documentation.
