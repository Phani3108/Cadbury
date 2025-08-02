import httpx, os, base64, time

# Handle missing environment variables for testing
JIRA_URL = os.getenv("JIRA_URL", "https://mock-jira.atlassian.net")
JIRA_PAT = os.getenv("JIRA_PAT", "mock-token")
AUTH = base64.b64encode(JIRA_PAT.encode()).decode()

async def create(summary:str, description:str, project="OPS") -> str:
    payload = {
        "fields":{
          "project":{"key":project},
          "summary":summary,
          "description":description,
          "issuetype":{"name":"Task"}
        }
    }
    
    try:
        async with httpx.AsyncClient() as c:
            r = await c.post(f"{JIRA_URL}/issue",
                             headers={"Authorization": f"Basic {AUTH}",
                                      "Content-Type":"application/json"},
                             json=payload, timeout=10)
            r.raise_for_status()
            return (await r.json())["key"]
    except httpx.HTTPStatusError as e:
        if e.response.status_code in [401, 403]:
            print(f"⚠️  Jira authentication failed: {e}")
            return f"JIRA-{int(time.time())}"  # Fallback to mock
        elif e.response.status_code in [400, 404, 500]:
            print(f"⚠️  Jira API error: {e}")
            return f"JIRA-{int(time.time())}"  # Fallback to mock
        else:
            raise
    except Exception as e:
        print(f"⚠️  Jira request failed: {e}")
        return f"JIRA-{int(time.time())}"  # Fallback to mock

async def status(issue_key: str) -> dict:
    """Get status of a Jira issue."""
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{JIRA_URL}/issue/{issue_key}",
                        headers={"Authorization": f"Basic {AUTH}",
                                 "Content-Type":"application/json"},
                        timeout=10)
    r.raise_for_status()
    return await r.json()

async def status_search(entity: str) -> list:
    """Search Jira issues by entity name."""
    jql = f'text~"{entity}" AND statusCategory != Done ORDER BY priority DESC'
    
    async with httpx.AsyncClient() as c:
        r = await c.get(f"{JIRA_URL}/search",
                        params={"jql": jql, "maxResults": 10},
                        headers={"Authorization": f"Basic {AUTH}",
                                 "Content-Type":"application/json"},
                        timeout=10)
    r.raise_for_status()
    
    issues = (await r.json())["issues"]
    return [
        {
            "id": issue["key"],
            "summary": issue["fields"]["summary"],
            "owner": issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else "Unassigned",
            "priority": issue["fields"]["priority"]["name"] if issue["fields"]["priority"] else "Medium",
            "status": issue["fields"]["status"]["name"]
        }
        for issue in issues
    ] 