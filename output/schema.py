"""
Output schema for medical paper summaries.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime


class PaperSummary(BaseModel):
    """Structured summary of a medical research paper."""
    
    title: str = Field(
        description="Full title of the research paper"
    )
    
    objective: str = Field(
        description="Primary research objective or question"
    )
    
    study_type: str = Field(
        description="Type of study (e.g., RCT, meta-analysis, cohort study, case-control)"
    )
    
    population: str = Field(
        description="Study population characteristics (sample size, demographics, inclusion/exclusion criteria)"
    )
    
    methods: str = Field(
        description="Key methodological details (design, interventions, measurements, analysis)"
    )
    
    key_findings: List[str] = Field(
        description="Primary results with exact numerical values as reported",
        min_length=1
    )
    
    limitations: List[str] = Field(
        description="Study limitations as acknowledged by authors",
        default_factory=list
    )
    
    author_conclusions: str = Field(
        description="Authors' stated conclusions (not inferred)"
    )
    
    keywords: List[str] = Field(
        description="Key medical/scientific terms",
        default_factory=list
    )
    
    # Metadata
    summary_timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When summary was generated"
    )
    
    model_used: str = Field(
        default="",
        description="LLM model used for summarization"
    )
    
    safety_disclaimer: str = Field(
        default="This summary is for academic research purposes only and does not constitute medical advice.",
        description="Required safety disclaimer"
    )
    
    @field_validator("key_findings")
    @classmethod
    def validate_findings(cls, v: List[str]) -> List[str]:
        """Ensure findings are non-empty."""
        if not v or all(not f.strip() for f in v):
            raise ValueError("key_findings must contain at least one non-empty finding")
        return [f.strip() for f in v if f.strip()]
    
    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        """Clean and deduplicate keywords."""
        cleaned = [k.strip().lower() for k in v if k.strip()]
        return list(dict.fromkeys(cleaned))  # Preserve order while deduplicating
    
    def to_markdown(self) -> str:
        """Convert summary to formatted markdown."""
        md = f"""# {self.title}

## Objective
{self.objective}

## Study Design
**Type:** {self.study_type}

**Population:** {self.population}

## Methods
{self.methods}

## Key Findings
"""
        for i, finding in enumerate(self.key_findings, 1):
            md += f"{i}. {finding}\n"
        
        if self.limitations:
            md += "\n## Limitations\n"
            for i, limitation in enumerate(self.limitations, 1):
                md += f"{i}. {limitation}\n"
        
        md += f"""
## Author Conclusions
{self.author_conclusions}

## Keywords
{", ".join(self.keywords)}

---

**Summary Generated:** {self.summary_timestamp.strftime("%Y-%m-%d %H:%M:%S")}
**Model:** {self.model_used}

⚠️ **{self.safety_disclaimer}**
"""
        return md
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "title": "Efficacy of Drug X in Type 2 Diabetes: A Randomized Controlled Trial",
                "objective": "To evaluate the efficacy and safety of Drug X versus placebo in adults with type 2 diabetes",
                "study_type": "Randomized Controlled Trial (RCT)",
                "population": "600 adults aged 40-75 with HbA1c 7.5-10%, BMI 25-40 kg/m², duration ≥6 months",
                "methods": "Double-blind RCT, 1:1 randomization to Drug X 10mg daily or placebo for 24 weeks. Primary endpoint: change in HbA1c from baseline.",
                "key_findings": [
                    "Mean HbA1c reduction: Drug X -1.2% vs placebo -0.3% (difference -0.9%, 95% CI -1.1 to -0.7, p<0.001)",
                    "Achievement of HbA1c <7%: Drug X 52% vs placebo 18% (p<0.001)",
                    "Adverse events similar between groups (Drug X 12% vs placebo 10%)"
                ],
                "limitations": [
                    "24-week duration may not capture long-term efficacy",
                    "Predominantly White population limits generalizability",
                    "Industry-funded study"
                ],
                "author_conclusions": "Drug X significantly reduced HbA1c compared to placebo with similar safety profile in adults with type 2 diabetes.",
                "keywords": ["type 2 diabetes", "HbA1c", "randomized controlled trial", "drug x", "glycemic control"]
            }
        }
