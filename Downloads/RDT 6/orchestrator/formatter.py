def render(intent:str, data:dict)->str:
    """Render response following Master File structure requirements."""
    
    # Handle safe-fail cases with proper Master File structure
    if data.get("safe_fail"):
        md = []
        md.append("**Summary**")
        md.append("This information is not available in the provided transcripts. The system cannot verify or provide information about unverifiable claims, promises, or predictions that are not documented in the knowledge base.")
        md.append("")
        md.append("**Insights**")
        md.append("• The system is designed to provide only factual, verifiable information from documented discussions")
        md.append("• Claims about future outcomes, promises, or guarantees require explicit documentation")
        md.append("• The Truth Policy ensures responses are grounded in actual transcript content")
        md.append("")
        md.append("**Discussion**")
        md.append("When users ask about unverifiable claims such as promises, guarantees, or predictions, the system must decline to provide information that cannot be verified against the knowledge base. This protects against hallucination and ensures all responses are factually grounded.")
        md.append("")
        md.append("**Sources**")
        md.append("No sources available for unverifiable claims")
        md.append("")
        md.append("**Suggested Actions**")
        md.append("• Ask about specific documented discussions or decisions")
        md.append("• Request information about actual project status or technical discussions")
        md.append("• Focus on factual, verifiable information from the knowledge base")
        md.append("")
        md.append("**Follow-up Questions**")
        md.append("• What specific discussions or decisions would you like to know about?")
        md.append("• Are there particular projects or topics you'd like to explore?")
        return "\n".join(md)
    
    # Handle calendar suggestions with proper structure
    if data.get("calendar_suggestions"):
        md = []
        md.append("**Summary**")
        md.append("I can help you schedule a meeting with Ramki. Based on the available information, here are some suggested time slots for your meeting request.")
        md.append("")
        md.append("**Insights**")
        md.append("• Meeting scheduling requests are processed through the calendar integration")
        md.append("• Available slots are determined based on Ramki's calendar and preferences")
        md.append("• Priority levels (P0-P5) help determine meeting urgency and scheduling")
        md.append("")
        md.append("**Discussion**")
        md.append("The system can assist with scheduling meetings by identifying available time slots and coordinating with Ramki's executive assistant. This ensures efficient scheduling while respecting existing commitments and priorities.")
        md.append("")
        md.append("**Sources**")
        md.append("Calendar integration and scheduling system")
        md.append("")
        md.append("**Suggested Actions**")
        md.append("• Review the available time slots below")
        md.append("• Select a preferred time and confirm your meeting")
        md.append("• Provide meeting topic and attendee information")
        md.append("")
        md.append("**Available Slots**")
        for i, slot in enumerate(data["calendar_suggestions"]):
            md.append(f"• **{slot['time']}** - {slot['duration']} minutes")
        md.append("")
        md.append("**Follow-up Questions**")
        md.append("• What is the topic for this meeting?")
        md.append("• Who else should attend this meeting?")
        md.append("• What is the priority level (P0-P5) for this meeting?")
        return "\n".join(md)
    
    # Normal response formatting with Master File structure
    md = []
    
    # Summary (3+ lines minimum)
    if data.get("summary"):
        md.append("**Summary**")
        md.append(data["summary"])
        md.append("The information provided is based on documented discussions and decisions from the knowledge base.")
        md.append("")
    
    # Insights (bulleted points with 1+ lines explanation)
    if data.get("insights"):
        md.append("**Insights**")
        for insight in data["insights"]:
            md.append(f"• {insight}")
        md.append("")
    
    # Key High-Level Discussion Points (2+ lines minimum)
    if data.get("discussion"):
        md.append("**Key Discussion Points**")
        for discussion in data["discussion"]:
            md.append(f"• {discussion}")
        md.append("")
    
    # Sources (from where information is extracted)
    if data.get("sources"):
        md.append("**Sources**")
        for source in data["sources"]:
            md.append(f"• {source}")
        md.append("")
    
    # Suggested Actions (bulleted points)
    if data.get("actions"):
        md.append("**Suggested Actions**")
        for action in data["actions"]:
            if isinstance(action, dict):
                md.append(f"• P{action.get('priority', 'N/A')} → @{action.get('owner', 'N/A')} — {action.get('text', 'N/A')} (due {action.get('due', 'N/A')})")
            else:
                md.append(f"• {action}")
        md.append("")
    
    # Ramki's Quote (if available)
    if data.get("ramki_quote"):
        md.append("**Ramki's Quote**")
        md.append(f"> {data['ramki_quote']}")
        md.append("")
    
    # Follow-up Questions (natural conversation nudge)
    if data.get("followups"):
        md.append("**Follow-up Questions**")
        for i, followup in enumerate(data["followups"]):
            md.append(f"• {followup}")
    
    return "\n".join(md) 