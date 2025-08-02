def render(intent:str, data:dict)->str:
    md = ["Buddy,"]
    
    # Handle safe-fail cases
    if data.get("safe_fail"):
        md.append("I don't have a recent source for that—want me to widen the search?")
        if data.get("followups"):
            md.append("\n**Next?**")
            md += [f"1. {q}" if i==0 else f"{i+1}. {q}" for i,q in enumerate(data["followups"])]
        return "\n".join(md)
    
    # Handle calendar suggestions
    if data.get("calendar_suggestions"):
        md.append("I found some available slots for your meeting:")
        for i, slot in enumerate(data["calendar_suggestions"]):
            md.append(f"• **{slot['time']}** - {slot['duration']} minutes")
        md.append("\nClick a slot to confirm your meeting!")
        return "\n".join(md)
    
    # Normal response formatting
    if data.get("summary"): md.append(f"**TL;DR** ▸ {data['summary']}")
    if data.get("insights"):
        md.append("\n**Insights**")
        md += [f"• {s}" for s in data["insights"]]
    if data.get("discussion"):
        md.append("\n**Discussion**")
        md += [f"• {s}" for s in data["discussion"]]
    if data.get("actions"):
        md.append("\n**Actions**")
        for a in data["actions"]:
            md.append(f"• P{a['priority']} → @{a['owner']} — {a['text']} (due {a['due']})")
    if data.get("ramki_quote"):
        md.append(f"\n**Ramki's Quote**\n> {data['ramki_quote']}")
    if data.get("followups"):
        md.append("\n**Next?**")
        md += [f"1. {q}" if i==0 else f"{i+1}. {q}" for i,q in enumerate(data["followups"])]
    if data.get("sources"):
        md.append("\n**Sources**")
        md += [f"• {s}" for s in data["sources"]]
    return "\n".join(md) 