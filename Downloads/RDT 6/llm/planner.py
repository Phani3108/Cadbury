import json
import re
import openai
import os
from typing import Dict, Any, List
from digital_twin.utils.config import openai_kwargs, get_model_key
from digital_twin.utils.logger import log_prompt_and_tokens
from skills._mock_mode import calendar_find_free_slot, jira_create, jira_status, jira_status_search

def load_prompt(filename: str) -> str:
    """Load prompt from file."""
    with open(f"llm/prompts/{filename}", "r") as f:
        return f.read()

def parse_tool_calls(response: str) -> List[Dict[str, Any]]:
    """Parse tool calls from ReAct response."""
    tool_calls = []
    
    # Find all Action: tool_name[{json_args}] patterns
    action_pattern = r'Action:\s*(\w+)\[(\{[^}]*\})\]'
    matches = re.findall(action_pattern, response)
    
    for tool_name, json_args in matches:
        try:
            args = json.loads(json_args)
            tool_calls.append({
                "tool": tool_name,
                "args": args
            })
        except json.JSONDecodeError:
            print(f"Failed to parse tool args: {json_args}")
    
    return tool_calls

def execute_tool_call(tool_call: Dict[str, Any]) -> str:
    """Execute a single tool call."""
    tool_name = tool_call["tool"]
    args = tool_call["args"]
    
    try:
        if tool_name == "calendar_find_free_slot":
            result = calendar_find_free_slot(**args)
            return f"Found {len(result)} available slots"
        elif tool_name == "jira_create":
            result = jira_create(**args)
            return f"Created Jira ticket: {result}"
        elif tool_name == "jira_status":
            result = jira_status(**args)
            return f"Jira status: {result}"
        elif tool_name == "jira_status_search":
            result = jira_status_search(**args)
            return f"Found {len(result)} Jira issues"
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Tool execution failed: {e}"

def extract_final_answer(response: str) -> Dict[str, Any]:
    """Extract FinalAnswer JSON from response."""
    final_answer_pattern = r'FinalAnswer:\s*(\{.*\})'
    match = re.search(final_answer_pattern, response, re.DOTALL)
    
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            print(f"Failed to parse FinalAnswer JSON: {match.group(1)}")
    
    return {}

# TODO(cursor): implement react(model, query, context, chunks) -> dict
"""
Pass messages:
SYSTEM = prompts/system.txt
TOOL_HINT = prompts/planner.txt
messages = [ {"role":"system","content":SYSTEM},
             {"role":"system","content":TOOL_HINT},
             {"role":"user","content":query},
             {"role":"assistant","content":"Context:\n"+context} ]
Stream Thoughts/Actions until 'FinalAnswer'. Return parsed JSON.
"""

PROMPT = open("llm/prompts/planner.txt").read()

async def react(model_key: str, query: str, context: str, search_results: List[Any]) -> Dict[str, Any]:
    """
    ReAct planner for generating structured responses.
    
    Args:
        model_key: Model to use
        query: User query
        context: Compressed context
        search_results: Search results
        
    Returns:
        Structured JSON response
    """
    try:
        # Prepare context from search results
        context_text = "\n\n".join([
            f"Source: {chunk.source_id}\n{chunk.text}"
            for chunk in search_results[:5]  # Limit to top 5 results
        ])
        
        # Create user message
        user_msg = PROMPT.replace("{QUERY}", query)\
                         .replace("{CONTEXT}", context_text)
        
        # Call OpenAI
        kwargs = openai_kwargs(model_key)
        client = openai.AsyncOpenAI(**kwargs)
        
        # Get the actual model name
        model_name = os.getenv(model_key, "gpt-3.5-turbo")
        
        response = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=2000,
            temperature=0.1,
        )
        
        # Log prompt and tokens
        total_tokens = response.usage.total_tokens if response.usage else 0
        log_prompt_and_tokens("llm/prompts/planner.txt", total_tokens, model_name)
        
        # Extract JSON from response
        content = response.choices[0].message.content
        
        # Try to find JSON in the response
        if "FinalAnswer:" in content:
            json_str = content.split("FinalAnswer:")[-1].strip()
            try:
                return json.loads(json_str)
            except:
                pass
        
        # Fallback: try to parse the entire response as JSON
        try:
            return json.loads(content)
        except:
            # Return a safe fallback
            return {
                "summary": "Unable to process query at this time",
                "insights": [],
                "discussion": [],
                "actions": [],
                "ramki_quote": "",
                "followups": ["Please try rephrasing your question"],
                "sources": []
            }
            
    except Exception as e:
        print(f"Planner error: {e}")
        return {
            "summary": "Error processing query",
            "insights": [],
            "discussion": [],
            "actions": [],
            "ramki_quote": "",
            "followups": ["Please try again"],
            "sources": []
        } 