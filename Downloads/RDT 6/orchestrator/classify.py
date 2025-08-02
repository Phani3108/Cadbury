from typing import Tuple, List
import re, spacy, pathlib, json
nlp = spacy.load("en_core_web_sm")

INTENT_PATTERNS = {
    "STATUS": r"\bstatus\b",
    "UPDATE": r"\bupdate\b",
    "ACTION": r"\baction\b|\bplan\b",
    # extend later …
}

def classify(text:str) -> Tuple[str, List[str]]:
    """Very light heuristic; fine-tune later."""
    intent = "INSIGHT"
    for label, pat in INTENT_PATTERNS.items():
        if re.search(pat, text, re.I): intent = label; break
    ents = [e.text for e in nlp(text).ents if e.label_ in ("ORG","PERSON","PRODUCT")]
    return intent, ents 