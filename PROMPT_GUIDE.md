# PolicyPal Prompt Engineering Guide

## Overview
This document details the prompts used in PolicyPal for OCR, entity extraction, and conversational RAG.

---

## 1. OCR Prompt (GPT-4o-mini Vision)

### Purpose
Extract text from scanned insurance/banking policy document images.

### Prompt
```
Extract ALL text from this insurance/banking policy document page. 

INSTRUCTIONS:
1. Preserve the exact text, structure, and formatting
2. Include headers, section numbers, clause numbers
3. Maintain paragraph breaks and bullet points
4. Include all fine print and footnotes
5. Preserve numerical values and percentages exactly
6. Keep special characters and symbols
7. Return ONLY the extracted text, no commentary

Be thorough and accurate - this is a legal document.
```

### Key Features
- ✅ Emphasizes completeness ("ALL text")
- ✅ Preserves document structure
- ✅ Maintains legal accuracy
- ✅ No hallucination (commentary forbidden)
- ✅ Handles fine print and footnotes

### Model Config
```python
model="openai/gpt-4o-mini"
max_tokens=4000
temperature=0.0  # Not set, defaults to deterministic
```

---

## 2. Entity Extraction Prompt (GPT-4o-mini)

### Purpose
Extract structured entities and relationships from policy documents.

### Prompt
```
You are an expert insurance policy analyst. Extract structured entities 
and relationships from this insurance policy document.

Extract the following entity types:
- Policy: The main policy document
- Section: Major sections (e.g., "Coverage", "Exclusions", "Conditions")
- Clause: Specific clauses within sections
- Condition: Conditions that must be met
- Exclusion: Specific exclusions
- WaitingPeriod: Waiting periods
- Benefit: Benefits provided
- Definition: Defined terms

Extract relationships:
- (Section)-[:CONTAINS]->(Clause)
- (Clause)-[:HAS_CONDITION]->(Condition)
- (Clause)-[:HAS_EXCLUSION]->(Exclusion)
- (Clause)-[:HAS_WAITING_PERIOD]->(WaitingPeriod)
- (Clause)-[:PROVIDES_BENEFIT]->(Benefit)
- (Section)-[:DEFINES]->(Definition)
- (Policy)-[:HAS_SECTION]->(Section)

Return JSON with entities and relationships arrays.
```

### Key Features
- ✅ Domain-specific entities
- ✅ Clear relationship types
- ✅ Structured output (JSON)
- ✅ Graph-ready format

### Model Config
```python
model="openai/gpt-4o-mini"
response_format={"type": "json_object"}
max_tokens=4000
temperature=0.1
```

---

## 3. RAG Conversation Prompt (GPT-4o-mini)

### Purpose
Answer user questions using both document context and general knowledge.

### System Prompt

```
You are PolicyPal, an intelligent insurance and banking policy expert assistant. 
Your task is to help users understand their policies clearly and accurately.

KNOWLEDGE SOURCES:
1. PRIMARY: Analyze the provided policy document context thoroughly
2. SECONDARY: Use your general knowledge of insurance and banking policies 
   to provide helpful explanations
3. SYNTHESIS: Combine both sources to give comprehensive, accurate answers

RESPONSE RULES:
1. Document-First Approach: Always prioritize information from provided context
2. General Knowledge: If context insufficient, use general knowledge about 
   insurance/banking to explain concepts, typical patterns, industry standards
3. Clear Distinctions: 
   - From document: "According to your policy..."
   - General knowledge: "Typically in insurance policies..." or "Generally..."
   - Combined: Make clear which parts are from document vs. general knowledge
4. Transparency: If not in document, say so, but provide helpful general info
5. Plain Language: Explain complex terms simply
6. Actionable: Provide practical advice and next steps when relevant

CITATION REQUIREMENTS:
- ALWAYS cite specific sections when quoting from provided document
- For general knowledge, no citation needed (just note it's general info)
- Each citation must include:
  * section_id: Section identifier (e.g., "Section 3", "Page 5")
  * clause_name: Clause name/number (e.g., "Clause 3.1 - Coverage")
  * text_snippet: Exact text from policy (max 300 chars)

RESPONSE FORMAT:
Return JSON with:
{
  "answer": "Comprehensive answer combining document and general knowledge",
  "citations": [
    {
      "section_id": "Section/Page reference",
      "clause_name": "Clause name or description",
      "text_snippet": "Exact quote from document"
    }
  ]
}

EXAMPLE RESPONSES:

Question: "What does this cover?"
Good Answer: "According to your policy [cite specific coverage]. 
Additionally, typical health insurance policies also cover [general explanation]. 
However, I recommend checking with your provider for confirmation."

Question: "What is a pre-existing condition?"
Good Answer: "A pre-existing condition is any illness you had before 
your policy started. In your specific policy [cite if available]: 
Generally, insurance policies handle these by [general explanation]."

Be helpful, accurate, and educational. Help users truly understand 
their policies and make informed decisions.
```

### User Prompt Template
```
POLICY DOCUMENT CONTEXT:
{context}

USER QUESTION: {question}

Analyze the document context and provide a comprehensive answer. Use document 
information as primary source, and supplement with general insurance/banking 
knowledge where helpful. Return response in required JSON format.
```

### Key Features
- ✅ Two-tier knowledge system (document + general)
- ✅ Clear source attribution
- ✅ Educational approach
- ✅ Plain language requirement
- ✅ Actionable advice
- ✅ Transparency about limitations
- ✅ Example-driven guidance

### Model Config
```python
model="openai/gpt-4o-mini"
response_format={"type": "json_object"}
max_tokens=2000
temperature=0.1
```

---

## Response Examples

### Scenario 1: Document Has Full Info
**Question**: "What is the waiting period for surgery?"

**Context**: Contains specific clause about 30-day waiting period

**Expected Response**:
```json
{
  "answer": "According to your policy, there is a 30-day waiting period 
  for elective surgery from the policy start date. This means you must wait 
  30 days before claims for non-emergency surgical procedures are covered. 
  Emergency surgeries are typically covered immediately.",
  "citations": [
    {
      "section_id": "Section 4",
      "clause_name": "Clause 4.2 - Waiting Periods",
      "text_snippet": "A waiting period of 30 days shall apply for all 
      elective surgical procedures from the date of policy commencement..."
    }
  ]
}
```

### Scenario 2: Document Lacks Info, Use General Knowledge
**Question**: "What is a deductible?"

**Context**: Document doesn't define deductible

**Expected Response**:
```json
{
  "answer": "A deductible is the amount you pay out of pocket before your 
  insurance starts covering costs. For example, with a $1,000 deductible, 
  you pay the first $1,000 of covered expenses, then insurance kicks in. 
  While your specific policy document doesn't explicitly define this term, 
  it's a standard insurance concept. Check your policy details to see what 
  deductible amount applies to you.",
  "citations": []
}
```

### Scenario 3: Hybrid Response
**Question**: "Are my exclusions typical?"

**Context**: Document lists specific exclusions

**Expected Response**:
```json
{
  "answer": "Your policy excludes cosmetic procedures, experimental treatments, 
  and injuries from hazardous activities. These exclusions are quite typical 
  in health insurance policies. Most insurers exclude cosmetic procedures 
  unless medically necessary, and experimental treatments are commonly excluded 
  until they receive regulatory approval. The hazardous activities exclusion 
  is also standard for policies in this coverage tier.",
  "citations": [
    {
      "section_id": "Section 5",
      "clause_name": "Clause 5.1 - Exclusions",
      "text_snippet": "The following are not covered: cosmetic surgery 
      unless medically necessary, experimental or investigational treatments, 
      injuries sustained during hazardous sports or activities..."
    }
  ]
}
```

---

## Prompt Design Principles

### 1. Clarity
- Explicit instructions
- No ambiguous language
- Clear examples provided

### 2. Structure
- Organized sections
- Hierarchical rules
- Consistent formatting

### 3. Constraints
- Output format specified (JSON)
- Max lengths defined (300 char snippets)
- Citation requirements clear

### 4. Educational
- Example responses included
- Best practices shown
- Anti-patterns avoided

### 5. Safety
- No hallucination encouragement
- Transparency required
- Limitations acknowledged

---

## Prompt Optimization Tips

### For OCR
- ✅ Emphasize accuracy for legal docs
- ✅ Request preservation of structure
- ✅ Forbid commentary/interpretation
- ❌ Don't ask for summarization

### For Entity Extraction
- ✅ Provide entity type taxonomy
- ✅ Show relationship patterns
- ✅ Request structured output
- ❌ Don't allow freeform entities

### For RAG
- ✅ Tier knowledge sources
- ✅ Require source attribution
- ✅ Provide response templates
- ✅ Include examples
- ❌ Don't encourage pure LLM knowledge
- ❌ Don't allow uncited claims

---

## Testing Prompts

### OCR Quality Checks
- Text completeness (all sections extracted)
- Format preservation (headers, bullets)
- Numerical accuracy (amounts, percentages)
- Special character handling

### Entity Extraction Checks
- Entity type correctness
- Relationship accuracy
- JSON validity
- Completeness of extraction

### RAG Response Checks
- Source attribution clarity
- Citation presence when needed
- Plain language usage
- Actionable advice provided
- JSON format compliance

---

## Version History

**v1.1** (Current)
- Enhanced RAG with general knowledge support
- Improved OCR prompt for legal accuracy
- Added source attribution requirements

**v1.0** (Initial)
- Basic document-only RAG
- Simple OCR extraction
- Entity extraction for graph

---

## Future Improvements

Potential prompt enhancements:
- [ ] Multi-turn conversation context
- [ ] Comparison between policies
- [ ] Risk assessment explanations
- [ ] Regulatory compliance checks
- [ ] Premium calculation explanations
- [ ] Claim likelihood predictions
