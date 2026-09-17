from typing import List

from pydantic import BaseModel, Field


class GuardrailDecision(BaseModel):
    allowed: bool = Field(
        description="True if the questionnaire is safe and in-scope for skin/hair consults"
    )
    reason: str = Field(
        description="Short explanation of the decision; shown when the input is rejected"
    )
    risk_categories: List[str] = Field(
        default_factory=list,
        description=(
            "Zero or more of: prompt_injection, jailbreak, off_topic, "
            "abuse, self_harm, criminal, unrelated_medical"
        ),
    )
