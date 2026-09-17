from typing import List

from pydantic import BaseModel, Field


class GuardrailDecision(BaseModel):
    allowed: bool = Field(
        description=(
            "True if the content is safe and in-scope for skin/hair consults"
        )
    )
    reason: str = Field(
        description="Short explanation of the decision"
    )
    risk_categories: List[str] = Field(
        default_factory=list,
        description=(
            "Zero or more of: prompt_injection, jailbreak, off_topic, "
            "abuse, self_harm, criminal, unrelated_medical, unsafe_advice"
        ),
    )
