import json
import logging
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from app.config import settings
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService
from app.models.schemas import ChatResponse, Citation

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self):
        self.graph_service = GraphService()
        self.vector_service = VectorService()
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = settings.openai_model

    async def process_query(
        self,
        question: str,
        document_id: str,
        top_k: int = 10
    ) -> ChatResponse:
        """
        Main GraphRAG query pipeline (async):
        1. Vector search in Qdrant for relevant chunks
        2. Extract Neo4j node IDs from results
        3. Graph traversal in Neo4j for connected nodes (exclusions, conditions, waiting periods)
        4. Combine context and generate structured response via LLM
        """
        try:
            # Step 1: Vector search (async)
            vector_results = await self.vector_service.search(
                query=question,
                document_id=document_id,
                limit=top_k
            )

            if not vector_results:
                logger.warning(f"No vector results found for question: {question}")
                return ChatResponse(
                    answer="I couldn't find any relevant information in the policy document to answer your question. Could you please rephrase or ask something more specific about your policy?",
                    citations=[]
                )

            logger.info(f"Found {len(vector_results)} vector results")

            # Step 2: Extract Neo4j node IDs from vector results
            neo4j_node_ids = [
                r.get("neo4j_node_id") for r in vector_results
                if r and r.get("neo4j_node_id")
            ]
            
            logger.info(f"Extracted {len(neo4j_node_ids)} Neo4j node IDs")

            # Step 3: Graph traversal for connected context
            graph_context = []
            if neo4j_node_ids:
                try:
                    graph_context = self.graph_service.get_connected_nodes(neo4j_node_ids) or []
                except Exception as e:
                    logger.error(f"Graph traversal failed: {e}")
                    graph_context = []

            # Also get clause context for specific clauses
            clause_ids = [
                r.get("neo4j_node_id") for r in vector_results
                if r and r.get("neo4j_node_id") and r.get("clause_number")
            ]
            
            clause_contexts = []
            if clause_ids:
                try:
                    clause_contexts = self.graph_service.get_clause_context(clause_ids) or []
                except Exception as e:
                    logger.error(f"Clause context retrieval failed: {e}")
                    clause_contexts = []

            # Step 4: Build unified context
            context = self._build_context(vector_results, graph_context, clause_contexts)

            # Step 5: Generate structured response (async)
            response = await self._generate_response(question, context)

            return response
            
        except Exception as e:
            logger.error(f"Error in process_query: {e}", exc_info=True)
            return ChatResponse(
                answer="I encountered an error processing your question. Please try again or rephrase your question.",
                citations=[]
            )

    def _build_context(
        self,
        vector_results: List[Dict[str, Any]],
        graph_context: List[Dict[str, Any]],
        clause_contexts: List[Dict[str, Any]]
    ) -> str:
        """Build unified context string for LLM."""
        context_parts = []

        # Add vector search results
        context_parts.append("=== RELEVANT POLICY CHUNKS (Vector Search) ===")
        for i, result in enumerate(vector_results):
            if not result:
                continue
            context_parts.append(
                f"[Chunk {i+1}] Section: {result.get('section_id', 'N/A')}, "
                f"Clause: {result.get('clause_number', 'N/A')} - {result.get('clause_name', 'N/A')}\n"
                f"Text: {result.get('text', '')}\n"
                f"Relevance Score: {result.get('score', 0):.3f}\n"
            )

        # Add graph traversal results
        if graph_context and len(graph_context) > 0:
            context_parts.append("\n=== CONNECTED GRAPH CONTEXT (1-hop traversal) ===")
            for node in graph_context:
                if not node:
                    continue
                labels = node.get("labels", [])
                props = node.get("properties", {})
                rel = node.get("relationship", {})
                if props:  # Only add if properties exist
                    context_parts.append(
                        f"Node: {labels} - {props.get('name', 'N/A')}\n"
                        f"Relationship: {rel.get('type', 'N/A') if rel else 'N/A'}\n"
                        f"Properties: {props}\n"
                    )

        # Add clause contexts
        if clause_contexts and len(clause_contexts) > 0:
            context_parts.append("\n=== CLAUSE DETAILS (Conditions, Exclusions, Waiting Periods) ===")
            for ctx in clause_contexts:
                if not ctx:
                    continue
                clause = ctx.get("clause", {})
                if clause:  # Only add if clause exists
                    context_parts.append(
                        f"Clause: {clause.get('name', 'N/A')} ({clause.get('number', 'N/A')})\n"
                        f"Section: {ctx.get('section', {}).get('name', 'N/A') if ctx.get('section') else 'N/A'}\n"
                        f"Conditions: {len(ctx.get('conditions', []))}\n"
                        f"Exclusions: {len(ctx.get('exclusions', []))}\n"
                        f"Waiting Periods: {len(ctx.get('waiting_periods', []))}\n"
                        f"Benefits: {len(ctx.get('benefits', []))}\n"
                    )

        return "\n".join(context_parts)

    async def _generate_response(self, question: str, context: str) -> ChatResponse:
        """Generate structured response using LLM (async)."""
        system_prompt = """You are PolicyPal, an intelligent insurance and banking policy expert assistant. Your task is to help users understand their policies clearly and accurately.

KNOWLEDGE SOURCES:
1. PRIMARY: Analyze the provided policy document context thoroughly
2. SECONDARY: Use your general knowledge of insurance and banking policies to provide helpful explanations
3. SYNTHESIS: Combine both sources to give comprehensive, accurate answers

HANDLING DIFFERENT QUERY TYPES:

**Greetings/Casual Messages** (e.g., "hi", "hello", "thanks"):
- Respond warmly and offer assistance
- Suggest what you can help with
- No citations needed for greetings

**Summarization Requests** (e.g., "summarize the policy", "what's this about"):
- Provide high-level overview from document context
- Cover: Coverage type, key benefits, major exclusions, important conditions
- Use multiple citations from different sections

**Specific Questions** (e.g., "what is covered", "what are exclusions"):
- Detailed answer based on document
- Supplement with general knowledge
- Cite specific sections

**General Concepts** (e.g., "what is a deductible"):
- Explain the concept clearly
- Apply to user's policy if mentioned in document
- Minimal/no citations if purely educational

RESPONSE RULES:
1. **Document-First**: Prioritize information from provided context
2. **Context-Aware**: Understand greeting vs. question vs. summary request
3. **General Knowledge**: Use when helpful to explain concepts
4. **Clear Distinctions**: 
   - From document: "According to your policy..."
   - General knowledge: "Typically..." or "Generally..."
4. **Plain Language**: Simple explanations anyone can understand
5. **Actionable**: Provide next steps when relevant
6. **Friendly**: Be warm, helpful, and conversational

CITATION REQUIREMENTS:
- Greetings: No citations
- Summaries: Multiple citations from different sections
- Specific questions: Cite relevant sections
- General concepts: Cite only if document mentions it

RESPONSE FORMAT:
Return JSON with:
{
  "answer": "Your comprehensive, context-aware answer",
  "citations": [
    {
      "section_id": "Section/Page reference",
      "clause_name": "Clause description",
      "text_snippet": "Exact quote (max 300 chars)"
    }
  ]
}

EXAMPLE RESPONSES:

**Greeting**: "Hi"
```json
{
  "answer": "Hello! I'm PolicyPal, your insurance policy assistant. I've analyzed your policy document and I'm here to help you understand it. You can ask me:\n\n• What does this policy cover?\n• What are the exclusions?\n• What are the waiting periods?\n• How do I file a claim?\n• Or ask me to summarize your entire policy\n\nWhat would you like to know?",
  "citations": []
}
```

**Summary Request**: "Summarize this policy"
```json
{
  "answer": "Here's a summary of your policy:\n\n**Type**: [Policy type from document]\n**Key Coverage**: [Main benefits]\n**Important Exclusions**: [Major exclusions]\n**Waiting Periods**: [If any]\n**Sum Insured**: [If mentioned]\n\nThis policy provides [general overview]. Would you like me to explain any specific aspect in more detail?",
  "citations": [
    {"section_id": "Section 1", "clause_name": "Coverage Overview", "text_snippet": "..."},
    {"section_id": "Section 3", "clause_name": "Exclusions", "text_snippet": "..."}
  ]
}
```

**Specific Question**: "What is covered?"
```json
{
  "answer": "According to your policy, you're covered for [specific coverage from document]. This includes [list items]. Typically, policies like this also cover [general knowledge supplement].",
  "citations": [
    {"section_id": "Section 2", "clause_name": "Covered Expenses", "text_snippet": "..."}
  ]
}
```

Be helpful, accurate, context-aware, and educational!"""

        user_prompt = f"""POLICY DOCUMENT CONTEXT:
{context}

USER QUESTION: {question}

Analyze the document context and provide a comprehensive answer. Use document information as primary source, and supplement with general insurance/banking knowledge where helpful. Return response in required JSON format."""

        try:
            logger.info(f"Generating response for question: {question[:100]}...")
            
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.1
            )

            logger.info("LLM response received")
            
            # Check if response exists
            if not response or not response.choices:
                logger.error("LLM returned empty response or no choices")
                return ChatResponse(
                    answer="I received an empty response from the AI. Please try again.",
                    citations=[]
                )
            
            # Check if message content exists
            content = response.choices[0].message.content
            if not content:
                logger.error("LLM response content is None")
                return ChatResponse(
                    answer="I received an empty response. Please try rephrasing your question.",
                    citations=[]
                )

            logger.info(f"Parsing response content (length: {len(content)})")
            result = json.loads(content)
            
            # Validate result structure
            if not isinstance(result, dict):
                logger.error(f"Result is not a dict: {type(result)}")
                return ChatResponse(
                    answer="I received an invalid response format. Please try again.",
                    citations=[]
                )

            # Validate and convert citations
            citations = []
            citations_raw = result.get("citations", [])
            
            if not isinstance(citations_raw, list):
                logger.warning(f"Citations is not a list: {type(citations_raw)}")
                citations_raw = []
            
            for i, cite in enumerate(citations_raw):
                if not cite:  # Skip None citations
                    logger.warning(f"Skipping None citation at index {i}")
                    continue
                    
                if not isinstance(cite, dict):
                    logger.warning(f"Skipping non-dict citation at index {i}: {type(cite)}")
                    continue
                
                try:
                    citations.append(Citation(
                        section_id=cite.get("section_id", "Unknown"),
                        clause_name=cite.get("clause_name", "Unknown"),
                        text_snippet=cite.get("text_snippet", "")
                    ))
                except Exception as e:
                    logger.error(f"Failed to create Citation from {cite}: {e}")
                    continue

            answer = result.get("answer", "I couldn't generate a proper answer.")
            logger.info(f"Successfully generated response with {len(citations)} citations")
            
            return ChatResponse(
                answer=answer,
                citations=citations
            )

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            logger.error(f"Content was: {content if 'content' in locals() else 'N/A'}")
            return ChatResponse(
                answer="I encountered an error formatting the response. Please try rephrasing your question.",
                citations=[]
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            return ChatResponse(
                answer="I encountered an error while generating the answer. Please try again.",
                citations=[]
            )

    def health_check(self) -> Dict[str, bool]:
        """Check health of all services."""
        return {
            "qdrant": self.vector_service.health_check(),
            "neo4j": self.graph_service.health_check()
        }
