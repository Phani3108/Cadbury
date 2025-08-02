# Digital Twin System

A sophisticated digital twin system that analyzes multi-document transcripts and provides insightful, user-centric responses while maintaining strict truth adherence and high-quality output.

## 🎯 Project Overview

This system is designed to:
- **Analyze multi-document transcripts** with conflicting views and multi-turn conversations
- **Provide user-centric responses** with proper greeting, acknowledgment, and follow-up questions
- **Maintain strict truth adherence** - no hallucination, only KB-grounded responses
- **Handle topic evolution** across multiple calls and documents
- **Support meeting scheduling** with Ramki's office hours
- **Integrate with Jira** for action item tracking
- **Process quotes intelligently** - rephrasing as insights/advice when appropriate

## 🏗️ Architecture

### Core Components

```
digital_twin/
├── core/                    # Core system components
│   ├── knowledge_processor.py      # KB processing and refinement
│   ├── semantic_search.py          # Multi-level semantic search
│   ├── response_generator.py       # Response synthesis and formatting
│   ├── memory_manager.py          # Short/long-term memory
│   └── truth_validator.py         # Truth policy enforcement
├── handlers/               # Query handling components
│   ├── intent_recognizer.py       # Query intent classification
│   ├── entity_extractor.py        # Entity recognition
│   ├── action_handler.py          # Special actions (scheduling, Jira)
│   └── conversation_manager.py    # Multi-turn conversation handling
├── processors/             # Data processing components
│   ├── transcript_processor.py    # Raw transcript processing
│   ├── quote_processor.py         # Quote refinement and rephrasing
│   ├── topic_analyzer.py          # Topic evolution and synthesis
│   └── conflict_resolver.py       # Conflicting information handling
├── integrations/           # External integrations
│   ├── jira_connector.py          # Jira integration
│   ├── calendar_connector.py      # Meeting scheduling
│   └── graph_connector.py         # Microsoft Graph integration
├── utils/                  # Utility components
│   ├── config.py                  # Configuration management
│   ├── logger.py                  # Logging utilities
│   └── validators.py              # Input/output validation
└── api/                   # API layer
    ├── main.py                    # FastAPI application
    ├── routes.py                  # API endpoints
    └── middleware.py              # Request/response middleware
```

### Data Flow

```
User Query → Intent Recognition → Semantic Search → KB Retrieval → 
Response Synthesis → Truth Validation → Memory Update → Response Delivery
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Azure AI Search (for production)
- ChromaDB (for local development)
- Microsoft Graph API (for calendar integration)

### Development Status

**Current Status**: Alpha Development Phase

#### ✅ Completed Features
- Core pipeline with 8-stage processing
- Truth policy compliance with source attribution
- Hybrid search with Azure AI Search integration
- Basic Teams frontend with SSE streaming
- Unit test coverage for core components

#### 🔧 In Development
- **Telemetry Integration**: Requires Azure Log Analytics workspace setup
- **Calendar Booking**: Requires Microsoft Graph API configuration
- **Teams Webhook**: Requires Teams webhook URL configuration
- **Production Deployment**: Requires Azure Container Apps setup

#### 📋 Production Requirements
- Set `AZURE_LOG_ANALYTICS_WORKSPACE_ID` for telemetry
- Set `TEAMS_WEBHOOK_URL` for metrics posting
- Configure Microsoft Graph API for calendar integration
- Deploy to Azure Container Apps for production

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd digital-twin-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the system**
   ```bash
   python -m digital_twin.setup
   ```

### Configuration

The system supports dual environment setup for seamless local development and production deployment.

#### Local Development

Create `.env.development` (safe to commit):

```env
MODE=dev
OPENAI_API_TYPE=openai          # plain OpenAI
OPENAI_API_KEY=sk-…             # your personal key
MODEL_GPT4=gpt-4o-mini
MODEL_GPT35=gpt-3.5-turbo-1106

# Vector Database (local)
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Database (local)
REDIS_URL=redis://localhost:6379

# Search Configuration
SEMANTIC_SEARCH_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.7
MAX_SEARCH_RESULTS=10

# Truth Policy
STRICT_TRUTH_ENFORCEMENT=true
REQUIRE_SOURCE_ATTRIBUTION=true

# Response Configuration
MAX_RESPONSE_LENGTH=2000
INCLUDE_FOLLOW_UP_QUESTIONS=true

# Logging
LOG_LEVEL=DEBUG
ENVIRONMENT=development
```

#### Production Deployment

Create `.env.production` (never commit):

```env
MODE=prod
OPENAI_API_TYPE=azure           # Azure OpenAI
OPENAI_API_KEY=<az key>
AZURE_OPENAI_ENDPOINT=https://YOUR-res.openai.azure.com
DEPLOYMENT_GPT4_1=gpt4o_1m
DEPLOYMENT_GPT35=gpt35_16k

# Azure Search
AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_KEY=your-search-key
AZURE_INDEX=digital-twin-index

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=your-connection-string

# Authentication
TEAMS_CLIENT_ID=your-teams-client-id
TEAMS_CLIENT_SECRET=your-teams-client-secret
TEAMS_TENANT_ID=your-tenant-id
JWT_SECRET=your-jwt-secret

# Container Registry
AZURE_RESOURCE_GROUP=digital-twin-rg
AZURE_LOCATION=eastus

AZURE_INDEX=your-index-name

# Jira Integration
JIRA_URL=https://your-domain.atlassian.net
JIRA_PAT=your-jira-personal-access-token

# Microsoft Graph (Calendar)
AZ_TENANT=your-tenant-id
AZ_CLIENT=your-client-id
AZ_SECRET=your-client-secret

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=production
```

```env
# LLM Configuration
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
DEFAULT_LLM_PROVIDER=openai

# Vector Database
VECTOR_DB_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Database
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:password@localhost/dbname

# Search Configuration
SEMANTIC_SEARCH_MODEL=all-MiniLM-L6-v2
SIMILARITY_THRESHOLD=0.7
MAX_SEARCH_RESULTS=10

# Truth Policy
STRICT_TRUTH_ENFORCEMENT=true
REQUIRE_SOURCE_ATTRIBUTION=true

# Response Configuration
MAX_RESPONSE_LENGTH=2000
INCLUDE_FOLLOW_UP_QUESTIONS=true
```

## 📋 Usage

### Basic Usage

```python
from digital_twin.core.semantic_search import SemanticSearch
from digital_twin.core.truth_validator import TruthValidator
from digital_twin.utils.config import get_settings

# Initialize components
settings = get_settings()
search = SemanticSearch()
validator = TruthValidator()

# Search knowledge base
results = search.search("What did Ramki say about our product strategy?", knowledge_base)

# Validate response
is_valid, violations, confidence = validator.validate_response(response, query, sources)
```

### Running the Application

#### Local Development

```bash
# Test configuration
python scripts/ping_models.py

# Test local setup
python scripts/test_local.py

# Start development server
MODE=dev uvicorn orchestrator.app:app --reload --port 8000
```

#### Production Deployment

```bash
# Build and deploy to Azure Container Apps
python scripts/deploy.py --environment prod

# Or deploy manually with Azure CLI
docker build -t digital-twin:latest .
az deployment group create \
  --resource-group digital-twin-rg \
  --template-file infra/aca.bicep \
  --parameters environment=prod openaiApiKey="your-key"

# Monitor deployment
az containerapp logs show --name digital-twin-prod --resource-group digital-twin-rg
```

### API Usage

Start the API server:

Make requests:

```bash
# Query the system
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What was discussed about our product strategy?",
    "user_id": "user123",
    "session_id": "session456"
  }'

# Schedule a meeting
curl -X POST "http://localhost:8000/api/v1/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Q2 Budget Discussion",
    "attendees": ["user1", "user2"],
    "priority": "P1",
    "duration": 60
  }'
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_semantic_search.py
pytest tests/test_truth_validator.py
pytest tests/test_response_generator.py

# Run with coverage
pytest --cov=digital_twin --cov-report=html
```

### Test Cases

The system includes comprehensive test cases covering:

- **General topic queries** - Product strategy, technical challenges
- **Specific person queries** - Ramki's views on topics
- **Action item queries** - Follow-up on assigned tasks
- **Meeting scheduling queries** - Booking time with Ramki
- **Follow-up queries** - Elaboration requests
- **Insight requests** - Analysis-only responses

See `TEST_CASES.md` for detailed examples.

## 🔧 Development

### Project Structure

- **Truth Policy**: `TRUTH_POLICY.md` - Strict guidelines for response accuracy
- **Standard Instructions**: `STANDARD_INSTRUCTIONS.md` - Development guidelines
- **Project Plan**: `PROJECT_PLAN.md` - Detailed development phases
- **Test Cases**: `TEST_CASES.md` - Comprehensive test scenarios

### Development Phases

1. **Foundation** (Week 1-2): Core infrastructure and basic functionality
2. **Intelligence** (Week 3-4): Advanced search and processing capabilities
3. **Response Enhancement** (Week 5-6): High-quality, user-centric responses
4. **Special Features** (Week 7-8): Meeting scheduling and Jira integration
5. **Optimization** (Week 9-10): Performance, testing, and refinement

### Code Quality

```bash
# Format code
black digital_twin/
isort digital_twin/

# Lint code
flake8 digital_twin/
mypy digital_twin/

# Run tests
pytest
```

## 📊 Monitoring

### Logging

The system provides comprehensive logging:

- **Application logs**: `logs/digital_twin.log`
- **Error logs**: `logs/errors.log`
- **Performance metrics**: Search time, response quality
- **Truth policy violations**: Hallucination detection

### Metrics

- **Response accuracy**: 95%+ truth adherence
- **Response quality**: 90%+ user satisfaction
- **Response time**: < 3 seconds average
- **System uptime**: 99.9% availability

## 🔒 Truth Policy

The system enforces strict truth adherence:

- **No hallucination**: All responses must be grounded in KB
- **Proper attribution**: Clear source references
- **Uncertainty handling**: Acknowledge when information is unavailable
- **Quote validation**: Ensure quotes are grammatically complete
- **Source grounding**: Verify claims against provided sources

## 🎯 Key Features

### Multi-Level Semantic Search

- **Basic**: Simple cosine similarity
- **Advanced**: Query expansion and metadata filtering
- **Enhanced**: Multi-query approach with clustering
- **Adaptive**: Strategy selection based on query type

### Response Quality

- **User-centric**: Greeting, acknowledgment, follow-up questions
- **Structured**: Summary, insights, actions, suggestions
- **Truth-validated**: Pre and post-response validation
- **Context-aware**: Memory for conversation continuity

### Special Functionality

- **Meeting scheduling**: Ramki's office hours integration
- **Jira integration**: Action item tracking and ticket creation
- **Quote processing**: Intelligent rephrasing of quotes
- **Conflict resolution**: Handling conflicting information

## 🤝 Contributing

1. Follow the truth policy and standard instructions
2. Write comprehensive tests for new features
3. Ensure all responses are KB-grounded
4. Maintain code quality and documentation
5. Focus on user value over technical complexity

## 📝 License

This project is proprietary and confidential.

---

**Remember**: The success of this system depends on the quality of the knowledge base. Spend more time on KB refinement than response generation. 