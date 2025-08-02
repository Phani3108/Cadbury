"""
Truth validator for enforcing truth policy and preventing hallucination.
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from .utils.logger import get_logger, log_truth_policy_violation
from .utils.config import get_settings


class TruthValidator:
    """
    Validates responses against truth policy to prevent hallucination.
    """
    
    def __init__(self):
        self.logger = get_logger("truth_validator")
        self.settings = get_settings()
        
        # Patterns that indicate potential hallucination
        self.hallucination_patterns = [
            r'\b(according to|based on|research shows|studies indicate)\b.*\b(but I don\'t have|not in the provided|not available)\b',
            r'\b(generally|typically|usually|commonly)\b.*\b(but this may not apply)\b',
            r'\b(I think|I believe|I assume|I guess)\b',
            r'\b(probably|maybe|possibly|likely)\b.*\b(but I\'m not sure)\b',
            r'\b(without more context|without additional information)\b',
            r'\b(this is a common pattern|this is typical|this is standard)\b'
        ]
        
        # Required attribution phrases
        self.attribution_phrases = [
            r'\b(according to the transcripts?)\b',
            r'\b(the transcripts? (indicate|show|mention))\b',
            r'\b(based on the (discussions?|conversations?|calls?))\b',
            r'\b(from the (meetings?|calls?|discussions?))\b',
            r'\b(Ramki (said|mentioned|stated|emphasized))\b',
            r'\b(the team (discussed|agreed|decided))\b'
        ]
        
        # Uncertainty indicators
        self.uncertainty_indicators = [
            r'\b(maybe|perhaps|possibly|likely|probably)\b',
            r'\b(I\'m not sure|I don\'t know|I can\'t tell)\b',
            r'\b(this might be|this could be|this seems to be)\b',
            r'\b(without more context|without additional information)\b'
        ]
    
    def validate_response(self, response: str, query: str, sources: List[str]) -> Tuple[bool, List[str], float]:
        """
        Validate response against truth policy.
        
        Args:
            response: System response to validate
            query: Original user query
            sources: List of source documents used
            
        Returns:
            Tuple of (is_valid, violations, confidence_score)
        """
        violations = []
        confidence_score = 1.0
        
        # Check for hallucination patterns
        hallucination_violations = self._check_hallucination_patterns(response)
        violations.extend(hallucination_violations)
        
        # Check for proper attribution
        attribution_violations = self._check_attribution(response, sources)
        violations.extend(attribution_violations)
        
        # Check for uncertainty handling
        uncertainty_violations = self._check_uncertainty_handling(response)
        violations.extend(uncertainty_violations)
        
        # Check for source grounding
        grounding_violations = self._check_source_grounding(response, sources)
        violations.extend(grounding_violations)
        
        # Calculate confidence score
        if violations:
            confidence_score = max(0.0, 1.0 - (len(violations) * 0.2))
            self.logger.warning(f"Truth policy violations found: {len(violations)}")
            for violation in violations:
                log_truth_policy_violation("truth_policy", violation, query)
        
        is_valid = len(violations) == 0
        return is_valid, violations, confidence_score
    
    def _check_hallucination_patterns(self, response: str) -> List[str]:
        """Check for patterns that indicate hallucination."""
        violations = []
        
        for pattern in self.hallucination_patterns:
            matches = re.findall(pattern, response, re.IGNORECASE)
            if matches:
                violations.append(f"Potential hallucination pattern detected: {pattern}")
        
        # Check for generic statements without specific context
        generic_statements = [
            r'\b(this is a common practice)\b',
            r'\b(this is standard procedure)\b',
            r'\b(this is typical in the industry)\b',
            r'\b(companies usually do this)\b'
        ]
        
        for pattern in generic_statements:
            if re.search(pattern, response, re.IGNORECASE):
                violations.append(f"Generic statement without specific context: {pattern}")
        
        return violations
    
    def _check_attribution(self, response: str, sources: List[str]) -> List[str]:
        """Check for proper attribution to sources."""
        violations = []
        
        if not sources:
            violations.append("No sources provided for response")
            return violations
        
        # Check if response contains attribution phrases
        has_attribution = False
        for pattern in self.attribution_phrases:
            if re.search(pattern, response, re.IGNORECASE):
                has_attribution = True
                break
        
        if not has_attribution and len(response) > 100:
            violations.append("Response lacks proper attribution to transcripts")
        
        return violations
    
    def _check_uncertainty_handling(self, response: str) -> List[str]:
        """Check for proper uncertainty handling."""
        violations = []
        
        # Check for uncertainty indicators without proper acknowledgment
        uncertainty_found = False
        for pattern in self.uncertainty_indicators:
            if re.search(pattern, response, re.IGNORECASE):
                uncertainty_found = True
                break
        
        if uncertainty_found:
            # Check if uncertainty is properly acknowledged
            acknowledgment_patterns = [
                r'\b(this information is not available in the provided transcripts)\b',
                r'\b(the transcripts do not contain this information)\b',
                r'\b(this is not mentioned in the discussions)\b'
            ]
            
            has_acknowledgment = False
            for pattern in acknowledgment_patterns:
                if re.search(pattern, response, re.IGNORECASE):
                    has_acknowledgment = True
                    break
            
            if not has_acknowledgment:
                violations.append("Uncertainty indicated but not properly acknowledged")
        
        return violations
    
    def _check_source_grounding(self, response: str, sources: List[str]) -> List[str]:
        """Check if response is grounded in provided sources."""
        violations = []
        
        # Check for specific claims that should be grounded
        specific_claims = [
            r'\b(Ramki (said|mentioned|stated|emphasized))\b',
            r'\b(the team (agreed|decided|concluded))\b',
            r'\b(we (discussed|planned|scheduled))\b',
            r'\b(action items (were|are))\b',
            r'\b(meetings (were|are) scheduled)\b'
        ]
        
        for pattern in specific_claims:
            if re.search(pattern, response, re.IGNORECASE):
                # Check if this is properly attributed
                if not any(attr_pattern in response.lower() for attr_pattern in [
                    "according to", "transcripts", "discussions", "calls"
                ]):
                    violations.append(f"Specific claim without proper grounding: {pattern}")
        
        return violations
    
    def validate_quote_usage(self, response: str) -> Tuple[bool, List[str]]:
        """
        Validate proper usage of quotes in responses.
        
        Args:
            response: Response to validate
            
        Returns:
            Tuple of (is_valid, violations)
        """
        violations = []
        
        # Check for incomplete quotes
        quote_pattern = r'"([^"]*)"'
        quotes = re.findall(quote_pattern, response)
        
        for quote in quotes:
            # Check if quote is grammatically complete
            if not self._is_grammatically_complete(quote):
                violations.append(f"Incomplete or grammatically incorrect quote: '{quote}'")
            
            # Check if quote makes sense in context
            if not self._quote_makes_sense(quote):
                violations.append(f"Quote that may not make sense: '{quote}'")
        
        # Check for excessive quote usage
        quote_count = len(quotes)
        if quote_count > 3:
            violations.append(f"Too many quotes in response: {quote_count}")
        
        return len(violations) == 0, violations
    
    def _is_grammatically_complete(self, text: str) -> bool:
        """Check if text is grammatically complete."""
        # Basic checks for grammatical completeness
        text = text.strip()
        
        # Should start with capital letter
        if not text or not text[0].isupper():
            return False
        
        # Should end with proper punctuation
        if not text.endswith(('.', '!', '?', ':', ';')):
            return False
        
        # Should have reasonable length
        if len(text) < 10:
            return False
        
        # Should not be just a single word (unless it's a proper noun)
        words = text.split()
        if len(words) < 2:
            return False
        
        return True
    
    def _quote_makes_sense(self, quote: str) -> bool:
        """Check if quote makes sense in context."""
        # Check for common nonsensical patterns
        nonsensical_patterns = [
            r'^\s*[.,;:!?]+\s*$',  # Just punctuation
            r'^\s*[A-Z]+\s*$',     # Just uppercase letters
            r'^\s*\d+\s*$',         # Just numbers
            r'^\s*[^\w\s]+\s*$',    # Just special characters
        ]
        
        for pattern in nonsensical_patterns:
            if re.match(pattern, quote):
                return False
        
        # Check for incomplete sentences
        incomplete_patterns = [
            r'^\s*[a-z]',           # Starts with lowercase
            r'[a-z]\s*$',           # Ends with lowercase (not proper noun)
            r'\b(and|or|but|the|a|an)\s*$',  # Ends with articles/conjunctions
        ]
        
        for pattern in incomplete_patterns:
            if re.search(pattern, quote):
                return False
        
        return True
    
    def suggest_improvements(self, violations: List[str]) -> List[str]:
        """
        Suggest improvements based on violations.
        
        Args:
            violations: List of truth policy violations
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        for violation in violations:
            if "hallucination" in violation.lower():
                suggestions.append("Add specific attribution to transcripts or remove unsupported claims")
            elif "attribution" in violation.lower():
                suggestions.append("Include phrases like 'according to the transcripts' or 'based on the discussions'")
            elif "uncertainty" in violation.lower():
                suggestions.append("Clearly state when information is not available in the provided transcripts")
            elif "grounding" in violation.lower():
                suggestions.append("Ensure all specific claims are properly attributed to source materials")
            elif "quote" in violation.lower():
                suggestions.append("Review quotes for grammatical completeness and contextual relevance")
        
        return suggestions
    
    def get_truth_policy_summary(self) -> Dict[str, Any]:
        """
        Get a summary of truth policy requirements.
        
        Returns:
            Dictionary with truth policy requirements
        """
        return {
            "strict_truth_enforcement": self.settings.strict_truth_enforcement,
            "require_source_attribution": self.settings.require_source_attribution,
            "hallucination_prevention": True,
            "attribution_required": True,
            "uncertainty_handling": True,
            "quote_validation": True,
            "source_grounding": True
        } 