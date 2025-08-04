#!/bin/bash
# deploy-secrets.sh - Digital Twin Pilot Secrets Deployment
# 
# Instructions for Ops:
# 1. Fill in secrets.todo.yml with real values
# 2. Update RESOURCE_GROUP and REGION below
# 3. Run this script to deploy secrets and restart the Container App

set -e

# UPDATE THESE VALUES
RESOURCE_GROUP="digital-twin-rg"
REGION="eastus"

echo "🚀 Digital Twin Pilot - Secrets Deployment"
echo "=========================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "Region: $REGION"
echo ""

# Step 1: Add all secrets in one shot
echo "📝 Step 1: Injecting secrets into Container App..."
az containerapp secret set -n twin-dev -g $RESOURCE_GROUP \
  --secrets @secrets.todo.yml

echo "✅ Secrets injected successfully"
echo ""

# Step 2: Map env-vars to secrets and force restart
echo "🔄 Step 2: Updating Container App with secret mappings..."
az containerapp update -n twin-dev -g $RESOURCE_GROUP \
  --env-vars \
  OPENAI_API_KEY=OPENAI_KEY \
  AZURE_OPENAI_ENDPOINT=AZURE_OPENAI_ENDPOINT \
  LLM_CHEAP=LLM_CHEAP_DEPLOY \
  LLM_HEAVY=LLM_HEAVY_DEPLOY \
  AZURE_SEARCH_ADMIN_KEY=AZURE_SEARCH_ADMIN \
  AZURE_SEARCH_SERVICE=AZURE_SEARCH_SERVICE \
  JIRA_PAT=JIRA_PAT \
  JIRA_BASE_URL=JIRA_BASE_URL \
  GRAPH_CLIENT_ID=GRAPH_CLIENT_ID \
  GRAPH_TENANT_ID=GRAPH_TENANT_ID \
  GRAPH_SECRET=GRAPH_CLIENT_SECRET \
  APPLICATIONINSIGHTS_CONNECTION_STRING=APPLICATIONINSIGHTS_CONNECTION_STRING \
  TOOLS_MOCK=TOOLS_MOCK \
  MODE=MODE \
  SEARCH_BACKEND=SEARCH_BACKEND \
  --revision-suffix livekeys

echo "✅ Container App updated with live keys"
echo ""

# Step 3: Get the new endpoint URL
echo "🌐 Step 3: Getting deployment URL..."
DT_URL=$(az containerapp show -n twin-dev -g $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
echo "Digital Twin URL: https://$DT_URL"
echo ""

echo "🎯 Next Steps:"
echo "1. Run the three-call smoke test (see smoke-test.sh)"
echo "2. If tests pass, invite pilot users to Teams channel"
echo "3. Monitor KPIs for 72 hours"
echo "4. When ready, flip to prod slot"
echo ""

echo "✅ Secrets deployment complete!" 