# LLM Configuration for Log Monitoring

This document explains how to configure the LLM integration for generating ticket titles and descriptions from error logs.

## Environment Variables

Add the following environment variables to your `.env` file:

### Database Configuration
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prod_monitoring
DB_USER=postgres
DB_PASSWORD=postgres
```

### Log Monitoring Configuration
```bash
LOG_FILE_PATH=/path/to/your/logfile.log
OUTPUT_FILE=errors.json
```

### LLM Configuration
```bash
USE_LLM=true
LLM_CLASS=AzureOpenAI  # or "OpenAI"
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=500
```

### Azure OpenAI Configuration (required if LLM_CLASS=AzureOpenAI)
```bash
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### OpenAI Configuration (required if LLM_CLASS=OpenAI)
```bash
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4
```

## Usage

### Basic Usage
```python
from agents.log_monitor import AdvancedLogMonitor

# Initialize with LLM enabled (default)
monitor = AdvancedLogMonitor(
    log_path="/path/to/logfile.log",
    use_llm=True,
    llm_class="AzureOpenAI"
)
monitor.monitor()
```

### Custom LLM Parameters
```python
monitor = AdvancedLogMonitor(
    log_path="/path/to/logfile.log",
    use_llm=True,
    llm_class="AzureOpenAI",
    llm_params={
        "temperature": 0.2,
        "max_tokens": 1000
    }
)
```

### Disable LLM (use regex fallback)
```python
monitor = AdvancedLogMonitor(
    log_path="/path/to/logfile.log",
    use_llm=False
)
```

## Features

### LLM-Generated Content
- **Smart Title Generation**: Creates descriptive, actionable ticket titles
- **Detailed Descriptions**: Generates comprehensive descriptions with:
  - Summary of the issue
  - Root cause analysis
  - Impact assessment
  - Steps to reproduce
  - Suggested actions

### Fallback Mechanism
- If LLM fails or is disabled, the system falls back to regex-based title extraction
- Ensures the monitoring system continues to work even without LLM access

### Token Usage Tracking
- Monitors token usage for cost management
- Provides token counting for each LLM interaction

## Error Handling

The system includes robust error handling:
- LLM initialization failures fall back to regex mode
- Individual LLM generation failures fall back to regex for that specific error
- All errors are logged for debugging

## Dependencies

Make sure to install the required dependencies:
```bash
poetry install
```

The following packages are automatically installed:
- `langchain`
- `langchain-openai`
- `tiktoken`
