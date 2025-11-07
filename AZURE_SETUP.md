# Azure Setup Guide

Complete guide for deploying the multi-agent system on Microsoft Azure.

## Prerequisites

### Required Azure Resources

1. **Azure OpenAI Service**
   - GPT-4o deployment
   - Text-embedding-ada-002 deployment (for embeddings)
   - API endpoint and key

2. **Azure Subscription**
   - Active Azure subscription
   - Contributor role access

3. **Development Tools**
   - Azure CLI (`az`)
   - Azure Developer CLI (`azd`) - optional for IaC
   - Python 3.9 or higher
   - Git

## Quick Start

### Option 1: Manual Setup

#### Step 1: Create Azure OpenAI Resource

```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Create resource group
az group create \
  --name rg-multiagent \
  --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --kind OpenAI \
  --sku S0 \
  --location eastus
```

#### Step 2: Deploy Models

```bash
# Deploy GPT-4o
az cognitiveservices account deployment create \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"

# Deploy embeddings model
az cognitiveservices account deployment create \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "Standard"
```

#### Step 3: Get Credentials

```bash
# Get endpoint
az cognitiveservices account show \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --query "properties.endpoint" \
  --output tsv

# Get API key
az cognitiveservices account keys list \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --query "key1" \
  --output tsv
```

#### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Update `.env`:
```bash
AZURE_OPENAI_ENDPOINT=https://openai-multiagent.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
EMBEDDING_DEPLOYMENT_NAME=text-embedding-ada-002
```

#### Step 5: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import openai; import azure.identity; print('✓ Azure packages installed')"
```

#### Step 6: Run Examples

```bash
# Run Azure-integrated workflow
python examples/azure_basic_workflow.py
```

---

### Option 2: Azure Developer CLI (azd)

#### Step 1: Initialize Project

```bash
# Install azd (if not already installed)
# https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd

# Login
azd auth login

# Initialize the project
azd init
```

#### Step 2: Provision Infrastructure

```bash
# Provision all Azure resources
azd provision

# This will create:
# - Azure OpenAI Service
# - Model deployments
# - (Optional) Container Apps environment
# - (Optional) Storage account
```

#### Step 3: Deploy Application

```bash
# Deploy to Azure
azd deploy

# Or provision + deploy in one command
azd up
```

---

## Configuration Options

### Authentication Methods

#### 1. API Key Authentication (Development)

```python
from src.azure import AzureOpenAIClient, AzureConfig

config = AzureConfig(
    endpoint="https://your-resource.openai.azure.com/",
    api_key="your-api-key",
    deployment_name="gpt-4o"
)

client = AzureOpenAIClient(config)
```

#### 2. Managed Identity (Production)

```python
config = AzureConfig(
    endpoint="https://your-resource.openai.azure.com/",
    deployment_name="gpt-4o",
    use_managed_identity=True
)

client = AzureOpenAIClient(config)
```

**Setup Managed Identity:**

```bash
# Enable system-assigned identity on your resource
az webapp identity assign \
  --name your-app-name \
  --resource-group rg-multiagent

# Grant access to Azure OpenAI
PRINCIPAL_ID=$(az webapp identity show \
  --name your-app-name \
  --resource-group rg-multiagent \
  --query principalId \
  --output tsv)

az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Cognitive Services OpenAI User" \
  --scope "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/rg-multiagent/providers/Microsoft.CognitiveServices/accounts/openai-multiagent"
```

---

## AutoGen Integration

### Setup AutoGen with Azure OpenAI

```python
from src.azure import create_autogen_model_client, AutoGenAgent, AutoGenTeam

# Create model client
model_client = create_autogen_model_client(
    endpoint="https://your-resource.openai.azure.com/",
    api_key="your-api-key",
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

# Create team
team = AutoGenTeam(
    agents=[researcher, analyst],
    max_rounds=10
)

# Execute task
result = await team.run("Research AI trends and provide analysis")
```

---

## Optional: Container Apps for Code Execution

For secure, scalable code execution:

### Step 1: Create Container Apps Environment

```bash
# Create environment
az containerapp env create \
  --name env-multiagent \
  --resource-group rg-multiagent \
  --location eastus
```

### Step 2: Create Session Pool

```bash
# Create session pool for dynamic code execution
az containerapp sessionpool create \
  --name pool-codeexec \
  --resource-group rg-multiagent \
  --environment env-multiagent \
  --container-type PythonLTS \
  --max-sessions 10 \
  --cooldown-period 300
```

### Step 3: Configure Application

```bash
# Add to .env
AZURE_CONTAINER_APPS_SESSION_POOL_ENDPOINT=https://pool-codeexec...
AZURE_CONTAINER_APPS_SESSION_POOL_ID=pool-codeexec
```

---

## Testing Azure Integration

### Test 1: Basic Connection

```python
import asyncio
from src.azure import get_azure_client

async def test_connection():
    client = get_azure_client()

    response = await client.chat_completion(
        messages=[
            {"role": "user", "content": "Hello Azure!"}
        ]
    )

    print(response['content'])

asyncio.run(test_connection())
```

### Test 2: Embeddings

```python
async def test_embeddings():
    client = get_azure_client()

    embedding = await client.generate_embedding(
        "Multi-agent systems with Azure OpenAI"
    )

    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

asyncio.run(test_embeddings())
```

### Test 3: Full Workflow

```bash
# Run the Azure example
python examples/azure_basic_workflow.py
```

---

## Cost Management

### Estimate Costs

**Azure OpenAI Pricing (as of 2024):**
- GPT-4o: ~$0.005 per 1K input tokens, ~$0.015 per 1K output tokens
- Embeddings: ~$0.0001 per 1K tokens

**Example Monthly Cost:**
- 1M tokens/month with GPT-4o: ~$10-15
- 100K embeddings: ~$1-2
- Container Apps (if used): ~$50-100/month

### Cost Optimization

1. **Use smaller models when appropriate**
   ```python
   # Use GPT-3.5-Turbo for simple tasks
   config.deployment_name = "gpt-35-turbo"
   ```

2. **Cache embeddings**
   ```python
   # Embeddings are cached in knowledge base
   # Don't regenerate for same content
   ```

3. **Set token limits**
   ```python
   response = await client.chat_completion(
       messages=messages,
       max_tokens=500  # Limit response length
   )
   ```

4. **Monitor usage**
   ```bash
   # View usage in Azure Portal
   # Or use Azure Monitor
   az monitor metrics list \
     --resource openai-multiagent \
     --metric-names "Azure OpenAI API Calls"
   ```

---

## Troubleshooting

### Common Issues

#### Issue: "Unauthorized" Error

**Solution:**
```bash
# Verify API key
az cognitiveservices account keys list \
  --name openai-multiagent \
  --resource-group rg-multiagent

# Check endpoint URL format
# Should be: https://<resource-name>.openai.azure.com/
```

#### Issue: "DeploymentNotFound" Error

**Solution:**
```bash
# List deployments
az cognitiveservices account deployment list \
  --name openai-multiagent \
  --resource-group rg-multiagent

# Verify deployment name in .env matches
```

#### Issue: Rate Limiting

**Solution:**
```python
# Implement retry logic
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(min=1, max=60), stop=stop_after_attempt(3))
async def call_with_retry():
    return await client.chat_completion(...)
```

#### Issue: AutoGen Import Errors

**Solution:**
```bash
# Reinstall AutoGen
pip uninstall autogen-agentchat autogen-ext
pip install 'autogen-agentchat==0.4.*' 'autogen-ext[openai]==0.4.*'
```

---

## Security Best Practices

### 1. Use Managed Identity in Production

Never commit API keys. Use managed identity for production:

```python
# Production configuration
config = AzureConfig(
    endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    use_managed_identity=True
)
```

### 2. Implement Key Rotation

```bash
# Regenerate keys periodically
az cognitiveservices account keys regenerate \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --key-name key1
```

### 3. Use Azure Key Vault

```bash
# Store secrets in Key Vault
az keyvault secret set \
  --vault-name kv-multiagent \
  --name "OpenAI-API-Key" \
  --value "your-api-key"

# Retrieve in application
az keyvault secret show \
  --vault-name kv-multiagent \
  --name "OpenAI-API-Key" \
  --query "value"
```

### 4. Enable Network Security

```bash
# Restrict access to specific IPs/VNets
az cognitiveservices account network-rule add \
  --name openai-multiagent \
  --resource-group rg-multiagent \
  --ip-address "YOUR_IP"
```

---

## Monitoring and Logging

### Enable Diagnostics

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group rg-multiagent \
  --workspace-name law-multiagent

# Enable diagnostic settings
az monitor diagnostic-settings create \
  --name diag-openai \
  --resource openai-multiagent \
  --resource-group rg-multiagent \
  --workspace law-multiagent \
  --logs '[{"category": "Audit", "enabled": true}]' \
  --metrics '[{"category": "AllMetrics", "enabled": true}]'
```

### Query Logs

```kusto
// View API calls in last 24 hours
AzureDiagnostics
| where TimeGenerated > ago(24h)
| where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
| project TimeGenerated, OperationName, ResultType, DurationMs
| order by TimeGenerated desc
```

---

## Support and Resources

- **Azure OpenAI Documentation**: https://learn.microsoft.com/azure/ai-services/openai/
- **AutoGen Documentation**: https://microsoft.github.io/autogen/
- **Azure Developer CLI**: https://learn.microsoft.com/azure/developer/azure-developer-cli/
- **Multi-Agent Workshop**: https://github.com/Azure-Samples/multi-agent-workshop

For issues specific to this implementation, see [GitHub Issues](https://github.com/your-repo/issues).
