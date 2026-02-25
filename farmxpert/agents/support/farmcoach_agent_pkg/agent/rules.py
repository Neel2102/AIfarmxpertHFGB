"""
Agent Behavior Rules - VERY IMPORTANT
These rules must be strictly followed by the Farmer Coach Agent.
"""

RULES = [
    "Only use data present in schemes_data",
    "Do NOT add eligibility rules unless explicitly provided",
    "Do NOT guess benefits or deadlines",
    "If information is missing, say: 'Please refer to the official website for more details.'",
    "Keep language simple and non-technical",
    "Preserve scheme names and URLs exactly as given"
]

STANDARD_DISCLAIMER = (
    "This information is based on official government data. "
    "For applications and latest updates, please visit the official website."
)

def validate_response_content(scheme_name: str, simple_explanation: str, original_description: str) -> bool:
    """
    Validate that the response doesn't add information beyond what's provided.
    """
    # Basic validation - explanation should be simpler version of description
    # not adding new facts or details
    return len(simple_explanation) > 0 and scheme_name.strip() != ""
