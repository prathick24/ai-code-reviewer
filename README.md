# AI Code Reviewer - Multi-Agent System

A multi-agent AI system built with LangGraph that orchestrates code generation, review, and research capabilities using AWS Bedrock and PostgreSQL for state persistence.

## Overview

This project implements an intelligent coding assistant with three specialized agents coordinated by an orchestrator:
- **Code Agent** - Generates code based on user queries
- **Review Agent** - Reviews generated code for correctness, performance, security, and style
- **Research Agent** - Conducts research when additional domain knowledge is needed
- **Orchestrator** - Routes requests between agents based on the task type

## Architecture

The system uses a LangGraph state machine with PostgreSQL checkpointing for conversation memory. The flow is:
1. User query comes in via the FastAPI endpoint
2. Orchestrator decides the appropriate agent path (code/review/research)
3. Agents collaborate iteratively - code generation may trigger reviews, reviews may trigger research or regeneration
4. Results are persisted in PostgreSQL using LangGraph's AsyncPostgresSaver

## Tech Stack

- **Framework**: FastAPI
- **AI/ML**: LangChain, LangGraph, AWS Bedrock (Amazon Nova models)
- **Database**: PostgreSQL (for state checkpointing)
- **Tools**: AST parsing, MCP (Model Context Protocol) adapters
- **Language**: Python 3.11+

## Project Structure

`
.
+-- Flow_diagrams/           # PlantUML diagrams (class, sequence)
+-- docs/                    # Training materials and documentation
+-- projects/client/src/     # Main application code
    +-- Agents/              # Agent implementations
    ¦   +-- code_agent.py
    ¦   +-- research_agent.py
    ¦   +-- review_agent.py
    +-- models/              # Pydantic models and API response schemas
    +-- Prompts/             # System prompts for each agent
    +-- Repositories/        # Database layer (Postgres, schema)
    +-- routes/              # FastAPI route definitions
    +-- services/            # Business logic and LangGraph orchestration
    +-- tools/               # Custom tools (AST analyzer)
    +-- utils/               # Utilities, exceptions, logging
    +-- main.py              # FastAPI application entry point
    +-- pyproject.toml       # Dependencies
`

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- AWS credentials with access to Bedrock
- AWS Bedrock model access (Amazon Nova model configured)

## Installation

1. Clone the repository:
`ash
git clone https://github.com/prathick24/ai-code-reviewer.git
cd ai-code-reviewer
`

2. Navigate to the source directory:
`ash
cd projects/client/src
`

3. Install dependencies (using uv or pip):
`ash
# With uv
uv sync

# Or with pip
pip install -e .
`

4. Set up environment variables. Create a .env file with the following:
`env
DB_PORT=5432
DB_HOST=localhost
DB_NAME=agent
DB_USERNAME=postgres
DB_PASSWORD=your_password
REGION=us-east-1
MODEL_ID=arn:aws:bedrock:us-east-1:YOUR_ACCOUNT:application-inference-profile/YOUR_PROFILE
PROVIDER=amazon
AWS_ACCESS_KEY=your_access_key
AWS_SECRET_KEY=your_secret_key
MCP_SERVER_URL=http://localhost:8000/mcp
`

5. Ensure PostgreSQL is running and accessible. The app will auto-setup checkpoint tables via LangGraph.

## Running the Application

Start the FastAPI server:
`ash
python main.py
`

Or with uvicorn directly:
`ash
uvicorn main:main --host 0.0.0.0 --port 8080 --reload
`

The API will be available at http://localhost:8080

## API Endpoints

### POST /MultiAgent/api/v1/chatbot
Process a user query through the multi-agent system.

**Request Body:**
`json
{
  "username": "user123",
  "user_query": "Write a Python function to sort a list"
}
`

**Response:**
`json
{
  "data": {
    "content": "code|review|research",
    "code": "generated code...",
    "review_response": {
      "correctness": "...",
      "performance": "...",
      "security": "...",
      "style": "...",
      "suggestions": ["..."]
    },
    "research_response": "research findings..."
  },
  "errors": [],
  "status_code": 200,
  "request_id": "...",
  "message": "Success"
}
`

## Key Components

### Agents
- **CodeAgent**: Generates code using structured output with the Code model
- **ReviewAgent**: Reviews code using AST analysis tool, returns structured review feedback
- **ResearchAgent**: Conducts research with MCP integration capabilities

### State Management
The system maintains state across agent interactions with fields like user_query, decision, Code, ReviewResponse, ResearchResponse, and routing information.

### Error Handling
Comprehensive error handling with custom exceptions, error codes, and centralized logging.

## Development

- Agents use LangChain's create_agent with structured output
- State persistence via PostgreSQL checkpoints enables conversation continuity per user (thread_id = username)
- Decorators for logging function calls
- Custom AST tool for code analysis

## Notes

- Never commit .env files or credentials. Use .gitignore to exclude them.
- The system uses AWS Bedrock - ensure you have appropriate IAM permissions and model access.
- PostgreSQL is required for checkpointing; make sure the database is configured correctly.
