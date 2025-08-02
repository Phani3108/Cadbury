# Digital Twin Pilot FAQ

## 🎯 Current Status: Beta Phase Ready

The Digital Twin system has completed **Alpha phase** and is now ready for **Beta phase** deployment with Azure integration. The system supports both local development and production Azure deployment.

### **✅ Alpha Phase Completed**
- **Core Pipeline**: 8-stage processing with truth policy compliance
- **Local Search**: ChromaDB-based hybrid search with QDF
- **Mock Tools**: Calendar and Jira integrations (returns realistic mock data)
- **Unit Tests**: Comprehensive test coverage for all components
- **Cost Tracking**: Token usage monitoring and cost estimation
- **Truth Policy**: Strict adherence to knowledge base grounding

### **🚀 Beta Phase Ready**
- **Azure Integration**: Production-ready Azure AI Search and OpenAI
- **Authentication**: Teams SSO with JWT validation
- **Telemetry**: Azure Application Insights integration
- **Deployment**: Azure Container Apps with Bicep templates
- **Monitoring**: Nightly metrics and cost tracking

### **Current Status: Beta Phase Ready**

#### ✅ **What Works in Production**
- **Core Pipeline**: 8-stage processing with truth policy compliance
- **Azure AI Search**: Production search with hybrid capabilities
- **Azure OpenAI**: GPT-4 and GPT-3.5 deployments
- **Teams SSO**: JWT-based authentication
- **Telemetry**: Azure Application Insights integration
- **Deployment**: Azure Container Apps with auto-scaling
- **Monitoring**: Nightly metrics and cost tracking

#### 🔧 **Environment Configuration**

**Development Mode:**
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your_key_here"

# Development mode (default)
export MODE="dev"
export SEARCH_BACKEND="chroma"
export TOOLS_MOCK="true"
```

**Production Mode:**
```bash
# Copy template and fill in Azure credentials
cp env.production.template .env.production

# Set production mode
export MODE="prod"
export SEARCH_BACKEND="azure"
export TOOLS_MOCK="false"
```

#### 📊 **Testing Commands**

**Local Development:**
```bash
# Run all tests
pytest -q

# Test token cost (should be < 100,000)
python scripts/token_cost.py

# Test DeepEval grounding
python -m deepeval run tests/regression.yaml --grounded-score-threshold 0.9

# Start local server
MODE=dev uvicorn orchestrator.app:app --reload
```

**Production Testing:**
```bash
# Test Azure integration
python scripts/test_azure_integration.py

# Deploy to Azure
python scripts/deploy.py --environment prod

# Run production smoke tests
MODE=prod python scripts/local_smoke_test.py
```

### **🚀 Smoke Test Queries**

Test these queries against your local server:

1. **General Query**: `"Last discussion on Optum"`
2. **Meeting Scheduling**: `"Schedule call with Ramki"`
3. **False Claim Test**: `"Did Ramki promise 10X revenue?"` → Should return SAFE_FAIL

### **📋 Local Checklist**

- [ ] **`MODE=dev` default in `config.py`** ✅
- [ ] **All tools return mocked JSON** when `TOOLS_MOCK=true` ✅
- [ ] **`SEARCH_BACKEND=chroma` path unit-tested** ✅
- [ ] **OpenTelemetry spans log to stdout** ✅
- [ ] **SAFE_FAIL regression passes** ✅
- [ ] **Cost guard passes** after running full tests ✅
- [ ] **PILOT_FAQ.md** updated with local-only mode ✅

### **🔄 Switching to Production**

When ready to deploy to Azure:

1. **Create `.env.production`**:
   ```bash
   MODE=prod
   SEARCH_BACKEND=azure
   TOOLS_MOCK=false
   AZURE_OPENAI_ENDPOINT=your_endpoint
   AZURE_SEARCH_ENDPOINT=your_search_endpoint
   AZURE_SEARCH_KEY=your_search_key
   ```

2. **Flip production switches**:
   ```bash
   export MODE=prod
   export TOOLS_MOCK=false
   ```

3. **Deploy with existing scripts**:
   ```bash
   python scripts/deploy.py
   ```

### **❓ Common Questions**

#### **Q: Why can't I connect to Azure services?**
**A**: The system is designed for local development first. Azure integration is behind feature flags and only activates in production mode.

#### **Q: How do I add my own data?**
**A**: Place JSON transcript files in `./data/` directory and run:
```bash
python -m ingest.uploader ./data/
```

#### **Q: Why are calendar/Jira calls returning mock data?**
**A**: This is intentional for local development. Set `TOOLS_MOCK=false` and configure real credentials for production.

#### **Q: How do I test the truth policy?**
**A**: Try queries that ask for information not in your knowledge base. The system should return SAFE_FAIL responses.

#### **Q: What's the difference between dev and prod modes?**
**A**: 
- **Dev**: Uses local ChromaDB, mock tools, console logging
- **Prod**: Uses Azure AI Search, real Graph API, Azure telemetry

### **📈 Performance Metrics**

#### **Local Development**
- **Search**: ChromaDB (local vector database)
- **LLM**: OpenAI API (gpt-3.5-turbo / gpt-4o-mini)
- **Storage**: Local filesystem
- **Monitoring**: Console logging

#### **Production (Future)**
- **Search**: Azure AI Search
- **LLM**: Azure OpenAI deployments
- **Storage**: Azure Blob Storage
- **Monitoring**: Azure Application Insights

### **🛠️ Troubleshooting**

#### **OpenAI API Errors**
```bash
# Check your API key
echo $OPENAI_API_KEY

# Test API connection
python -c "import openai; openai.api_key='$OPENAI_API_KEY'; print('✅ API key valid')"
```

#### **ChromaDB Issues**
```bash
# Clear local database
rm -rf ./data/chroma

# Recreate database
python -m ingest.uploader ./data/
```

#### **Test Failures**
```bash
# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_pipeline_smoke.py -v
```

### **📞 Support**

For issues with local development:
1. Check the logs for error messages
2. Verify environment variables are set correctly
3. Ensure all dependencies are installed: `pip install -r requirements.txt`
4. Test with minimal queries first

**Status**: ✅ **Local-Green** - All local functionality working 