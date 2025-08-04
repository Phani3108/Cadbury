import json
import re
import openai
import os
from typing import Dict, Any, List, Optional
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

async def react(model_key: str, query: str, context: str, search_results: List[Any], conversation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    ReAct planner for generating structured responses.
    
    Args:
        model_key: Model to use
        query: User query
        context: Compressed context
        search_results: Search results
        conversation_context: Optional conversation context for follow-up handling
        
    Returns:
        Structured JSON response
    """
    try:
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️  No OpenAI API key available: Using mock response")
            return _generate_mock_response(query, search_results, conversation_context)
        
        # Get conversation context
        conv_context = conversation_context or {}
        previous_queries = conv_context.get("previous_queries", [])
        previous_responses = conv_context.get("previous_responses", [])
        
        # Check if this is a follow-up question
        is_follow_up = False
        follow_up_indicators = ["what about", "tell me more", "and", "also", "additionally", "furthermore", "moreover", "specifically", "in detail", "elaborate", "what else", "anything else"]
        is_follow_up = any(indicator in query.lower() for indicator in follow_up_indicators)
        
        # Enhance query with context for follow-ups
        enhanced_query = query
        if is_follow_up and previous_queries:
            last_query = previous_queries[-1]
            enhanced_query = f"Follow-up to '{last_query}': {query}"
        
        # Create system prompt with conversation context
        system_prompt = PROMPT
        if is_follow_up and previous_responses:
            last_response = previous_responses[-1]
            system_prompt += f"\n\nPrevious response context: {last_response[:500]}..."
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {enhanced_query}\nContext: {context}"}
        ]
        
        # Add conversation history if available
        if len(previous_queries) > 0:
            conversation_history = "\n".join([
                f"Q: {q}\nA: {r[:200]}..." 
                for q, r in zip(previous_queries[-2:], previous_responses[-2:])
            ])
            messages.insert(1, {"role": "system", "content": f"Conversation history:\n{conversation_history}"})
        
        # Call OpenAI
        client = openai.OpenAI(**openai_kwargs())
        response = client.chat.completions.create(
            model=get_model_key(model_key),
            messages=messages,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Log the interaction
        log_prompt_and_tokens(messages, response.usage)
        
        # Parse the response
        content = response.choices[0].message.content
        return extract_final_answer(content)
        
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

def _generate_mock_response(query: str, search_results: List[Any], conversation_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate a mock response for development mode that strictly adheres to Truth Policy."""
    
    # Debug output
    print(f"🔍 Mock response called with query: '{query}'")
    print(f"🔍 Search results count: {len(search_results) if search_results else 0}")
    if search_results and len(search_results) > 0:
        print(f"🔍 First search result: {search_results[0].text[:100]}...")
    
    # Get conversation context
    conv_context = conversation_context or {}
    previous_queries = conv_context.get("previous_queries", [])
    previous_responses = conv_context.get("previous_responses", [])
    
    # Check if this is a follow-up question
    follow_up_indicators = ["what about", "tell me more", "and", "also", "additionally", "furthermore", "moreover", "specifically", "in detail", "elaborate", "what else", "anything else"]
    is_follow_up = any(indicator in query.lower() for indicator in follow_up_indicators)
    
    # Check for unverifiable claims that should trigger SAFE_FAIL
    # More precise detection to avoid false positives
    query_lower = query.lower()
    unverifiable_claims = [
        "promise", "guarantee", "10x", "10X", "revenue", "profit", "success",
        "will happen", "definitely", "certainly", "assure", "commit"
    ]
    
    # Only trigger SAFE_FAIL if the query contains specific unverifiable claim patterns
    # Not just individual words, but specific phrases that indicate unverifiable claims
    has_unverifiable_claim = False
    for claim in unverifiable_claims:
        if claim in query_lower:
            # Check if it's part of a legitimate query pattern
            legitimate_patterns = [
                "status", "current status", "project status", "what is the status",
                "progress", "current progress", "project progress", "what is the progress",
                "discussion", "discussions", "meeting", "meetings", "call", "calls",
                "decision", "decisions", "update", "updates", "report", "reports"
            ]
            
            # If the query contains legitimate patterns, don't flag as unverifiable
            is_legitimate = any(pattern in query_lower for pattern in legitimate_patterns)
            if not is_legitimate:
                has_unverifiable_claim = True
                break
    
    if has_unverifiable_claim:
        print(f"🔍 Query flagged as unverifiable claim: '{query}'")
        return {
            "summary": "This information is not available in the provided transcripts",
            "insights": [],
            "discussion": [],
            "actions": [],
            "ramki_quote": "",
            "followups": ["Please ask about specific discussions or decisions"],
            "sources": [],
            "safe_fail": True
        }
    
    # Check if search results are empty or None
    if not search_results or len(search_results) == 0:
        print(f"🔍 No search results found for query: '{query}'")
        return {
            "summary": "This information is not available in the provided transcripts",
            "insights": [],
            "discussion": [],
            "actions": [],
            "ramki_quote": "",
            "followups": ["Please ask about specific discussions or decisions"],
            "sources": []
        }
    
    # Extract key information from search results - TRUTH POLICY COMPLIANT
    insights = []
    discussion = []
    sources = []
    
    # Process actual search results to extract real insights
    for chunk in search_results[:3]:  # Use top 3 results
        chunk_text = chunk.text.strip()
        chunk_text_lower = chunk_text.lower()
        
        # Extract insights from any meaningful chunk content
        if len(chunk_text) > 30:  # Ensure substantial content
            # Extract the first meaningful sentence or phrase
            sentences = chunk_text.split('.')
            if sentences:
                first_sentence = sentences[0].strip()
                if len(first_sentence) > 20:  # Ensure meaningful content
                    insights.append(f"From {chunk.source_id}: {first_sentence}...")
            
            # Add to discussion points
            discussion.append(f"From {chunk.source_id}: {chunk_text[:200]}...")
            sources.append(chunk.chunk_id)
    
    # If no meaningful insights found, return SAFE_FAIL
    if not insights:
        print(f"🔍 No meaningful insights extracted from search results for query: '{query}'")
        return {
            "summary": "This information is not available in the provided transcripts",
            "insights": [],
            "discussion": [],
            "actions": [],
            "ramki_quote": "",
            "followups": ["Please ask about specific discussions or decisions"],
            "sources": []
        }
    
    # Generate response based on actual content found
    summary = "Based on the available transcripts, here are the relevant discussions found"
    followups = ["Would you like more specific details about any aspect?", "Should I search for more recent discussions?"]
    
    # Enhance response for follow-up questions
    if is_follow_up and previous_queries:
        last_query = previous_queries[-1]
        summary = f"Following up on your question about '{last_query}', here are additional relevant discussions found"
        followups = ["Would you like me to elaborate on any specific aspect?", "Should I search for more related information?"]
    
    print(f"🔍 Generated mock response with {len(insights)} insights for query: '{query}'")
    return {
        "summary": summary,
        "insights": insights,
        "discussion": discussion,
        "actions": [],
        "ramki_quote": "",
        "followups": followups,
        "sources": sources
    } 