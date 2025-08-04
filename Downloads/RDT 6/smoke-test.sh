#!/bin/bash
# smoke-test.sh - Digital Twin Pilot Smoke Test
# 
# Run this AFTER Ops has deployed secrets with deploy-secrets.sh
# This tests the three critical scenarios with real Azure keys

set -e

# Get the Container App URL
RESOURCE_GROUP="digital-twin-rg"
DT_URL=$(az containerapp show -n twin-dev -g $RESOURCE_GROUP --query "properties.configuration.ingress.fqdn" -o tsv)
DT="https://$DT_URL"

echo "🧪 Digital Twin Pilot - Smoke Test"
echo "=================================="
echo "Testing URL: $DT"
echo ""

# Note: In production, you'll need a real JWT token from Teams SSO
# For now, we'll test the /chat/dev endpoint which bypasses auth
echo "⚠️  Note: Using /chat/dev endpoint (bypasses auth for testing)"
echo ""

# Test 1: Status query - should return cited answer
echo "📋 Test 1: Optum Discussion Query"
echo "Query: 'Last discussion on Optum'"
echo "Expected: Cited answer with [1] style citations"
echo ""

RESPONSE1=$(curl -s -X POST "$DT/chat/dev" \
  -H "Content-Type: application/json" \
  -d '{"query":"Last discussion on Optum"}' | jq -r '.response')

echo "Response:"
echo "$RESPONSE1"
echo ""
echo "✅ Test 1 Complete"
echo ""

# Test 2: Booking query - should return calendar JSON
echo "📅 Test 2: Calendar Scheduling Query"
echo "Query: 'Schedule a call with Ramki tomorrow'"
echo "Expected: Calendar-slot JSON/Adaptive-Card stub"
echo ""

RESPONSE2=$(curl -s -X POST "$DT/chat/dev" \
  -H "Content-Type: application/json" \
  -d '{"query":"Schedule a call with Ramki tomorrow"}' | jq -r '.response')

echo "Response:"
echo "$RESPONSE2"
echo ""
echo "✅ Test 2 Complete"
echo ""

# Test 3: False claim - should return SAFE_FAIL
echo "🚫 Test 3: False Claim Detection"
echo "Query: 'Did Ramki promise 10X revenue yesterday?'"
echo "Expected: SAFE_FAIL template for unverifiable claim"
echo ""

RESPONSE3=$(curl -s -X POST "$DT/chat/dev" \
  -H "Content-Type: application/json" \
  -d '{"query":"Did Ramki promise 10X revenue yesterday?"}' | jq -r '.response')

echo "Response:"
echo "$RESPONSE3"
echo ""
echo "✅ Test 3 Complete"
echo ""

# Summary
echo "🎯 Smoke Test Summary"
echo "===================="
echo "✅ All three tests completed"
echo ""

# Check for expected patterns
if [[ "$RESPONSE1" == *"Buddy"* ]]; then
    echo "⚠️  Test 1: Still getting SAFE_FAIL - check OpenAI keys"
else
    echo "✅ Test 1: Got proper response (not SAFE_FAIL)"
fi

if [[ "$RESPONSE2" == *"schedule"* ]] || [[ "$RESPONSE2" == *"calendar"* ]]; then
    echo "✅ Test 2: Calendar intent detected"
else
    echo "⚠️  Test 2: Calendar response may need adjustment"
fi

if [[ "$RESPONSE3" == *"Buddy"* ]]; then
    echo "✅ Test 3: SAFE_FAIL working correctly for false claims"
else
    echo "⚠️  Test 3: False claim detection may need adjustment"
fi

echo ""
echo "🎉 Smoke test complete!"
echo ""
echo "Next Steps:"
echo "1. If all tests pass → Invite pilot users"
echo "2. If any test fails → Check logs and contact support"
echo "3. Monitor KPIs for 72 hours"
echo "" 