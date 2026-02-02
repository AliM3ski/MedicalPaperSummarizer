"""
Prompt templates for medical paper summarization.
"""


class PromptTemplates:
    """Prompt templates for different summarization tasks."""
    
    # System prompt with safety guidelines
    SYSTEM_PROMPT = """You are an expert medical research analyst tasked with summarizing peer-reviewed medical research papers.

CRITICAL RULES - NEVER VIOLATE:
1. ACCURACY: Use ONLY information explicitly stated in the source text
2. NO INFERENCE: Do not infer, interpret, or extrapolate beyond what authors state
3. PRESERVE NUMBERS: Copy all numerical results, statistics, p-values, and confidence intervals EXACTLY as reported
4. NO CLINICAL ADVICE: Never provide medical advice, treatment recommendations, or clinical guidance
5. AUTHOR CONCLUSIONS ONLY: Only report conclusions explicitly stated by the authors
6. NO SPECULATION: Do not speculate about implications, mechanisms, or applications
7. ACKNOWLEDGE LIMITATIONS: Include all limitations mentioned by authors
8. NO CHERRY-PICKING: Represent the full picture, including negative or null results

Your role is to extract and condense information, not to interpret or advise."""
    
    # Chunk summarization (map phase)
    CHUNK_SUMMARY_PROMPT = """Summarize the following excerpt from the {section_name} section of a medical research paper.

INSTRUCTIONS:
- Extract key information relevant to a {section_name} section
- Preserve ALL numerical values, statistics, and measurements exactly
- Keep technical terminology
- Be concise but comprehensive
- If multiple findings, list them separately
- Do not add interpretation

TEXT:
{chunk_text}

SUMMARY:"""
    
    # Section synthesis (reduce phase)
    SECTION_SYNTHESIS_PROMPT = """You have {num_chunks} summaries from different parts of the {section_name} section. Combine them into a coherent summary.

INSTRUCTIONS:
- Merge overlapping information
- Preserve ALL numerical values exactly
- Maintain logical flow
- Eliminate redundancy
- Keep concise (max 300 words for most sections)
- Organize information logically

CHUNK SUMMARIES:
{chunk_summaries}

COMBINED SUMMARY:"""
    
    # Extract study metadata
    METADATA_EXTRACTION_PROMPT = """Extract the following metadata from this research paper text. The text may include abstract, introduction, and methods sections - extract from wherever the information appears.

1. **study_type**: Type of study. Look in both introduction and methods. Examples:
   - Clinical: RCT, cohort, case-control, cross-sectional, meta-analysis
   - Basic science: In vitro study, laboratory study, animal study, cell culture study, experimental study
   - Other: Systematic review, case series, observational study

2. **population**: Who or what was studied. Look in methods section if not in abstract:
   - For clinical studies: sample size, demographics, inclusion/exclusion criteria
   - For in vitro/lab studies: cell lines (e.g., mouse osteoblasts), materials (e.g., Ti6Al4V alloy), specimens
   - For animal studies: species, sample size

You MUST provide both fields. If not explicitly stated, infer the closest match from context.

TEXT:
{text}

Respond ONLY with a JSON object (no markdown, no explanation):
{
  "study_type": "...",
  "population": "..."
}"""
    
    # Extract key findings
    FINDINGS_PROMPT = """Extract the key findings from the results section. 

CRITICAL: 
- List each distinct finding separately
- Include EXACT numerical values (means, SDs, p-values, CIs, effect sizes)
- Specify sample sizes if reported
- Include both positive and negative/null results
- Do not interpret or explain results

RESULTS SECTION:
{results_text}

KEY FINDINGS (as JSON array of strings):
[
  "Finding 1 with exact numbers",
  "Finding 2 with exact numbers",
  ...
]"""
    
    # Extract limitations
    LIMITATIONS_PROMPT = """Extract the study limitations as stated by the authors.

List each limitation separately. Include only limitations explicitly mentioned in the text.

TEXT:
{text}

LIMITATIONS (as JSON array of strings):
[
  "Limitation 1",
  "Limitation 2",
  ...
]

If no limitations are mentioned, respond with: []"""
    
    # Extract author conclusions
    CONCLUSIONS_PROMPT = """Extract the authors' stated conclusions from the discussion/conclusion section.

CRITICAL:
- Use ONLY conclusions explicitly stated by the authors
- Do not infer or interpret
- Preserve the authors' hedging language (e.g., "suggests", "may indicate")
- Include important caveats they mention

DISCUSSION/CONCLUSION:
{conclusion_text}

AUTHOR CONCLUSIONS (1-2 sentences):"""
    
    # Extract keywords
    KEYWORDS_PROMPT = """Extract 5-8 key medical/scientific terms from this paper.

Focus on:
- Medical conditions/diseases
- Interventions/treatments
- Study type
- Primary outcomes
- Population characteristics

TEXT (first 2000 tokens):
{text}

KEYWORDS (as JSON array, lowercase):
["keyword1", "keyword2", ...]"""
    
    # Final synthesis prompt
    FINAL_SYNTHESIS_PROMPT = """You have summaries of different sections of a medical research paper. Create a final structured summary.

SECTION SUMMARIES:
{section_summaries}

Using the information above, create a comprehensive but concise summary. Extract:

1. Key findings with exact numbers
2. Limitations
3. Author conclusions

Respond with a JSON object following this structure:
{{
  "key_findings": [
    "Finding 1 with exact statistics",
    "Finding 2 with exact statistics"
  ],
  "limitations": [
    "Limitation 1",
    "Limitation 2"
  ],
  "author_conclusions": "Authors' stated conclusions"
}}

CRITICAL: Preserve all numerical values exactly. Do not add any findings or conclusions not present in the source text."""


def get_chunk_summary_prompt(section_name: str, chunk_text: str) -> str:
    """Get prompt for chunk summarization."""
    return PromptTemplates.CHUNK_SUMMARY_PROMPT.format(
        section_name=section_name,
        chunk_text=chunk_text
    )


def get_section_synthesis_prompt(section_name: str, chunk_summaries: str, num_chunks: int) -> str:
    """Get prompt for section synthesis."""
    return PromptTemplates.SECTION_SYNTHESIS_PROMPT.format(
        section_name=section_name,
        chunk_summaries=chunk_summaries,
        num_chunks=num_chunks
    )


def get_metadata_prompt(text: str) -> str:
    """Get prompt for metadata extraction."""
    return PromptTemplates.METADATA_EXTRACTION_PROMPT.format(text=text)


def get_findings_prompt(results_text: str) -> str:
    """Get prompt for findings extraction."""
    return PromptTemplates.FINDINGS_PROMPT.format(results_text=results_text)


def get_limitations_prompt(text: str) -> str:
    """Get prompt for limitations extraction."""
    return PromptTemplates.LIMITATIONS_PROMPT.format(text=text)


def get_conclusions_prompt(conclusion_text: str) -> str:
    """Get prompt for conclusions extraction."""
    return PromptTemplates.CONCLUSIONS_PROMPT.format(conclusion_text=conclusion_text)


def get_keywords_prompt(text: str) -> str:
    """Get prompt for keyword extraction."""
    return PromptTemplates.KEYWORDS_PROMPT.format(text=text)


def get_final_synthesis_prompt(section_summaries: str) -> str:
    """Get prompt for final synthesis."""
    return PromptTemplates.FINAL_SYNTHESIS_PROMPT.format(
        section_summaries=section_summaries
    )
