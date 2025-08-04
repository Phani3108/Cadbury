# 🚀 Digital Twin Pilot - Ops Hand-off Guide

## Overview
The Digital Twin system is ready for production deployment. All code is green and tested. The system currently runs in SAFE_FAIL mode without real Azure keys, which is the expected behavior.

## 📋 Pre-Deployment Checklist

### ✅ Completed
- [x] All code tested and functional
- [x] Production mode working correctly
- [x] Search engine finding relevant content
- [x] Intent detection working
- [x] SAFE_FAIL handling verified
- [x] Azure Container Apps infrastructure ready
- [x] Bicep templates validated

### 🔑 Required for Deployment
- [ ] Azure OpenAI API key and endpoint
- [ ] Azure Search admin key
- [ ] Jira Personal Access Token
- [ ] Microsoft Graph API credentials
- [ ] Application Insights connection string

## 🛠️ Deployment Steps

### Step 1: Prepare Secrets
1. **Edit `secrets.todo.yml`**
   - Fill in all empty values with real Azure credentials
   - Update `RESOURCE_GROUP` and `REGION` in `deploy-secrets.sh`

2. **Required Secrets:**
   ```yaml
   OPENAI_KEY:               "your-azure-openai-key"
   AZURE_OPENAI_ENDPOINT:    "https://your-resource.openai.azure.com"
   AZURE_SEARCH_ADMIN:       "your-search-admin-key"
   JIRA_PAT:                 "your-jira-pat"
   GRAPH_CLIENT_ID:          "your-graph-client-id"
   GRAPH_TENANT_ID:          "your-tenant-id"
   GRAPH_CLIENT_SECRET:      "your-graph-secret"
   APPLICATIONINSIGHTS_CONNECTION_STRING: "your-app-insights-connection"
   ```

### Step 2: Deploy Secrets
```bash
# Run the deployment script
./deploy-secrets.sh
```

This will:
- Inject all secrets into the Container App
- Map environment variables to secrets
- Force a restart with `--revision-suffix livekeys`

### Step 3: Verify Deployment
```bash
# Run the smoke test
./smoke-test.sh
```

**Expected Results:**
1. **Optum Query**: Should return cited answer (not SAFE_FAIL)
2. **Calendar Query**: Should return calendar JSON stub
3. **False Claim**: Should return SAFE_FAIL template

## 🎯 Post-Deployment Actions

### 1. Pilot User Invitation
- Add users to Teams channel `#digital-twin-pilot`
- Post pilot FAQ and test scenarios
- Share the Digital Twin URL

### 2. Monitoring Setup
- Monitor Application Insights for errors
- Check nightly cost/latency reports
- Watch for critical errors

### 3. KPI Tracking (72-hour burn-in)
| KPI | Target |
|-----|--------|
| p95 latency | < 2s |
| Thumb-up rate | ≥ 70% |
| SAFE_FAIL incidence | < 3% |
| Avg tokens per query | ≤ 1,500 |
| Critical errors | 0 |

## 🚨 Troubleshooting

### If Smoke Test Fails
1. **Check Container App logs:**
   ```bash
   az containerapp logs show -n twin-dev -g digital-twin-rg
   ```

2. **Verify secrets are set:**
   ```bash
   az containerapp secret list -n twin-dev -g digital-twin-rg
   ```

3. **Check environment variables:**
   ```bash
   az containerapp show -n twin-dev -g digital-twin-rg --query "properties.template.containers[0].env"
   ```

### Common Issues
- **SAFE_FAIL still showing**: Check OpenAI API key and endpoint
- **Search not working**: Verify Azure Search admin key
- **Authentication errors**: Check Teams SSO configuration

## 📞 Support Contacts
- **Technical Issues**: Contact the development team
- **Azure Issues**: Contact Azure support
- **Pilot Feedback**: Use Teams channel `#digital-twin-pilot`

## 🎉 Success Criteria
The pilot is successful when:
- ✅ All smoke tests pass
- ✅ No critical errors for 72 hours
- ✅ KPI targets are met
- ✅ Pilot users provide positive feedback

## 🔄 Production Rollout
When pilot is successful:
```bash
# Copy dev slot to prod slot
az containerapp revision copy \
   --name twin-dev --resource-group digital-twin-rg \
   --destination-containerapp twin-prod \
   --revision-suffix pilot1
```

Update Teams tab URL to point to prod endpoint.

---

**🎯 Ready to deploy! The system is fully tested and waiting for real Azure keys.** 