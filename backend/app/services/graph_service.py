import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from neo4j import GraphDatabase
from openai import OpenAI
from app.config import settings
from app.services.pdf_processor import DocumentChunk

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password)
        )
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

    def close(self):
        self.driver.close()

    def health_check(self) -> bool:
        try:
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False

    def create_document_node(self, document_id: str, filename: str) -> str:
        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (d:Document {id: $id, filename: $filename, created_at: datetime()})
                RETURN d.id as id
                """,
                id=document_id, filename=filename
            )
            return result.single()["id"]

    def extract_entities_and_relationships(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """
        Use GPT-4o-mini to extract entities and relationships from document chunks.
        """
        # Combine chunks into a single text for processing
        combined_text = "\n\n---\n\n".join([
            f"[Page {c.page_number}, Section: {c.section_title or 'Unknown'}]\n{c.text}"
            for c in chunks
        ])

        prompt = f"""
        You are an expert insurance policy analyst. Extract structured entities and relationships from this insurance policy document.

        Extract the following entity types:
        - Policy: The main policy document
        - Section: Major sections (e.g., "Coverage", "Exclusions", "Conditions")
        - Clause: Specific clauses within sections (e.g., "Clause 3.1: Hospitalization Coverage")
        - Condition: Conditions that must be met (e.g., "Pre-authorization required")
        - Exclusion: Specific exclusions (e.g., "Pre-existing conditions excluded for 24 months")
        - WaitingPeriod: Waiting periods (e.g., "30 days waiting period for illness")
        - Benefit: Benefits provided (e.g., "Room rent up to 1% of sum insured")
        - Definition: Defined terms

        Extract relationships:
        - (Section)-[:CONTAINS]->(Clause)
        - (Clause)-[:HAS_CONDITION]->(Condition)
        - (Clause)-[:HAS_EXCLUSION]->(Exclusion)
        - (Clause)-[:HAS_WAITING_PERIOD]->(WaitingPeriod)
        - (Clause)-[:PROVIDES_BENEFIT]->(Benefit)
        - (Section)-[:DEFINES]->(Definition)
        - (Policy)-[:HAS_SECTION]->(Section)

        Return a JSON object with:
        {{
            "entities": [
                {{"id": "unique_id", "type": "EntityType", "name": "Name", "properties": {{...}}}}
            ],
            "relationships": [
                {{"source": "source_id", "target": "target_id", "type": "RELATIONSHIP_TYPE", "properties": {{...}}}}
            ]
        }}

        Document text:
        {combined_text[:15000]}
        """

        try:
            response = self.client.chat.completions.create(
                model="openai/gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=4000,
                temperature=0.1
            )
            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {"entities": [], "relationships": []}

    def store_graph(self, document_id: str, extraction_result: Dict[str, Any]) -> List[str]:
        """
        Store extracted entities and relationships in Neo4j.
        Returns list of created node IDs.
        """
        node_ids = []

        with self.driver.session() as session:
            # Create entities
            for entity in extraction_result.get("entities", []):
                entity_id = entity.get("id", str(uuid.uuid4()))
                entity_type = entity.get("type", "Entity")
                name = entity.get("name", "")
                properties = entity.get("properties", {})

                # Add document_id to properties
                properties["document_id"] = document_id
                properties["name"] = name

                # Create node with dynamic label
                query = f"""
                CREATE (n:{entity_type} {{id: $id, name: $name, document_id: $doc_id}})
                SET n += $props
                RETURN n.id as id
                """
                result = session.run(query, id=entity_id, name=name, doc_id=document_id, props=properties)
                node_ids.append(result.single()["id"])

            # Create relationships
            for rel in extraction_result.get("relationships", []):
                source_id = rel.get("source")
                target_id = rel.get("target")
                rel_type = rel.get("type", "RELATED_TO")
                properties = rel.get("properties", {})

                query = f"""
                MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                CREATE (a)-[r:{rel_type}]->(b)
                SET r += $props
                """
                session.run(query, source_id=source_id, target_id=target_id, props=properties)

        return node_ids

    def get_connected_nodes(self, node_ids: List[str], max_hops: int = 1) -> List[Dict[str, Any]]:
        """
        Get connected nodes (exclusions, conditions, waiting periods) for given node IDs.
        """
        if not node_ids:
            return []

        with self.driver.session() as session:
            # Build query for 1-hop traversal
            placeholders = ", ".join([f"'{nid}'" for nid in node_ids])
            query = f"""
            MATCH (n) WHERE n.id IN [{placeholders}]
            OPTIONAL MATCH (n)-[r]->(m)
            WHERE type(r) IN ['HAS_EXCLUSION', 'HAS_CONDITION', 'HAS_WAITING_PERIOD', 'PROVIDES_BENEFIT', 'DEFINES']
            RETURN n, r, m
            UNION
            MATCH (n) WHERE n.id IN [{placeholders}]
            OPTIONAL MATCH (m)-[r]->(n)
            WHERE type(r) IN ['CONTAINS', 'HAS_EXCLUSION', 'HAS_CONDITION', 'HAS_WAITING_PERIOD']
            RETURN m, r, n
            """

            results = session.run(query)
            connected = []

            for record in results:
                nodes = [record.get("n"), record.get("m")]
                rel = record.get("r")

                for node in nodes:
                    if node and node.id not in node_ids:
                        connected.append({
                            "id": node.id,
                            "labels": list(node.labels),
                            "properties": dict(node),
                            "relationship": dict(rel) if rel else None
                        })

            return connected

    def get_clause_context(self, clause_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get full context for specific clauses including section, conditions, exclusions.
        """
        if not clause_ids:
            return []

        with self.driver.session() as session:
            placeholders = ", ".join([f"'{cid}'" for cid in clause_ids])
            query = f"""
            MATCH (c:Clause) WHERE c.id IN [{placeholders}]
            OPTIONAL MATCH (s:Section)-[:CONTAINS]->(c)
            OPTIONAL MATCH (c)-[:HAS_CONDITION]->(cond:Condition)
            OPTIONAL MATCH (c)-[:HAS_EXCLUSION]->(exc:Exclusion)
            OPTIONAL MATCH (c)-[:HAS_WAITING_PERIOD]->(wp:WaitingPeriod)
            OPTIONAL MATCH (c)-[:PROVIDES_BENEFIT]->(b:Benefit)
            RETURN c, s, collect(DISTINCT cond) as conditions, collect(DISTINCT exc) as exclusions,
                   collect(DISTINCT wp) as waiting_periods, collect(DISTINCT b) as benefits
            """

            results = session.run(query)
            contexts = []

            for record in results:
                clause = record["c"]
                section = record["s"]
                conditions = [dict(c) for c in record["conditions"] if c]
                exclusions = [dict(e) for e in record["exclusions"] if e]
                waiting_periods = [dict(w) for w in record["waiting_periods"] if w]
                benefits = [dict(b) for b in record["benefits"] if b]

                contexts.append({
                    "clause": dict(clause),
                    "section": dict(section) if section else None,
                    "conditions": conditions,
                    "exclusions": exclusions,
                    "waiting_periods": waiting_periods,
                    "benefits": benefits
                })

            return contexts

    def clear_document(self, document_id: str):
        """
        Delete all nodes and relationships for a document.
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (n {document_id: $doc_id})
                DETACH DELETE n
                """,
                doc_id=document_id
            )
    
    def get_graph_for_visualization(self, document_id: str) -> dict:
        """
        Get graph data formatted for visualization.
        Returns nodes and edges in a format suitable for visualization libraries.
        """
        with self.driver.session() as session:
            # Get all nodes for the document
            nodes_result = session.run(
                """
                MATCH (n {document_id: $doc_id})
                RETURN n, labels(n) as labels, id(n) as neo4j_id
                """,
                doc_id=document_id
            )
            
            nodes = []
            node_ids = set()
            
            for record in nodes_result:
                node = record["n"]
                labels = record["labels"]
                neo4j_id = record["neo4j_id"]
                
                node_data = {
                    "id": node.get("id", str(neo4j_id)),
                    "label": node.get("name", node.get("id", f"Node {neo4j_id}")),
                    "type": labels[0] if labels else "Unknown",
                    "properties": dict(node)
                }
                nodes.append(node_data)
                node_ids.add(node.get("id"))
            
            # Get all relationships
            edges_result = session.run(
                """
                MATCH (a {document_id: $doc_id})-[r]->(b {document_id: $doc_id})
                RETURN a.id as source, b.id as target, type(r) as type, properties(r) as properties
                """,
                doc_id=document_id
            )
            
            edges = []
            for record in edges_result:
                edge_data = {
                    "source": record["source"],
                    "target": record["target"],
                    "type": record["type"],
                    "properties": record["properties"]
                }
                edges.append(edge_data)
            
            return {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "node_types": list(set(n["type"] for n in nodes))
                }
            }