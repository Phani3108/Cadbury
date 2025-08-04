import os, json, openai, asyncio
from digital_twin.utils.config import openai_kwargs, get_model_key

PROMPT = open("llm/prompts/verifier.txt").read()

async def check(draft: dict, chunks: list) -> dict:
    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  No OpenAI API key available: Using mock verification")
        return {"valid": True, "reason": "no-api-key-mode"}
    
    short_snips = [
        {"id": c.chunk_id, "text": c.text[:400], "age_days": getattr(c, 'age_days', 0)}
        for c in chunks[:12]
    ]
    user_msg = PROMPT.replace("{DRAFT_JSON}", json.dumps(draft)[:15000])\
                     .replace("{SNIPPETS}", json.dumps(short_snips))
    try:
        kwargs = openai_kwargs(get_model_key(is_heavy=False))  # Verifier uses cheap tier
        client = openai.AsyncOpenAI(**kwargs)
        
        # Get the actual model name
        model_name = os.getenv(get_model_key(is_heavy=False), "gpt-3.5-turbo")
        
        rsp = await client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": user_msg}],
            max_tokens=256,
            temperature=0,
        )
        out = json.loads(rsp.choices[0].message.content)
        return out if "valid" in out else {"valid": False, "reason": "bad-schema"}
    except Exception as e:
        return {"valid": False, "reason": f"parse-error {e}"} 