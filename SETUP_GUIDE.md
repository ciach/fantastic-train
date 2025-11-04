# Document Assistant - Setup Guide

## Quick Start

### 1. Prerequisites
- Python 3.9 or higher
- OpenAI API key

### 2. Installation Steps

#### Step 1: Navigate to Project Directory
```bash
cd /home/c/Nauka/document-assistance-project/starter
```

#### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

#### Step 4: Configure Environment Variables
```bash
cp .env.example .env
```

Edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_actual_api_key_here
```

#### Step 5: Run the Assistant
```bash
python3 main.py
```

## First Run

When you first run the assistant:
1. You'll be prompted to enter a user ID (or press Enter for 'demo_user')
2. A new session will be created
3. You'll see available commands and example queries

## Available Commands

- `/help` - Show help message with example queries
- `/docs` - List all available documents in the system
- `/quit` - Exit the assistant

## Example Queries to Try

### Q&A Queries
```
What's the total amount in invoice INV-001?
What are the terms of contract CON-001?
Show me details about claim CLM-001
```

### Summarization Queries
```
Summarize all contracts
Give me a summary of invoice INV-002
Summarize the insurance claims
```

### Calculation Queries
```
Calculate the sum of all invoice totals
What's the average amount of all documents?
Add the totals from INV-001 and INV-002
```

## Directory Structure After First Run

```
starter/
├── src/                  # Source code
├── sessions/             # Session files (auto-created)
│   └── <session-id>.json
├── logs/                 # Tool usage logs (auto-created)
│   └── session_<session-id>.json
├── main.py
├── requirements.txt
├── .env                  # Your configuration (not in git)
└── .env.example          # Template
```

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"
**Solution**: Make sure you created the `.env` file and added your API key.

### Issue: "ModuleNotFoundError"
**Solution**: Activate your virtual environment and run `pip install -r requirements.txt`

### Issue: "No active session"
**Solution**: This shouldn't happen in normal flow. If it does, restart the application.

### Issue: Tool not being used
**Solution**: The LLM decides which tools to use. Try rephrasing your query to be more explicit.

## Session Management

- Sessions are automatically saved to `./sessions/` directory
- Each session has a unique ID
- You can resume a session by providing the session ID when starting
- Session files contain conversation history and document context

## Logs

- Tool usage is automatically logged to `./logs/` directory
- Each session has its own log file
- Logs include timestamps, tool names, inputs, and outputs
- Useful for debugging and understanding agent behavior

## Advanced Usage

### Resuming a Session
When prompted for user ID, you can also specify a session ID to resume:
```python
# In the code, modify start_session call:
session_id = assistant.start_session(user_id, session_id="existing-session-id")
```

### Customizing the LLM
Edit `main.py` to change model parameters:
```python
assistant = DocumentAssistant(
    openai_api_key=api_key,
    model_name="gpt-4o",      # Change model
    temperature=0.1           # Adjust temperature
)
```

## Understanding the Output

When you send a message, you'll see:
- **🤖 Assistant**: The main response
- **INTENT**: The classified intent (qa, summarization, or calculation)
- **SOURCES**: Document IDs referenced in the response
- **TOOLS USED**: Which tools were called (e.g., calculator, document_reader)
- **CONVERSATION SUMMARY**: Summary of the conversation so far

## Next Steps

1. Try different types of queries
2. Explore the conversation history in session files
3. Check the logs to see which tools were used

## Support

For project requirements, see `README.md`
