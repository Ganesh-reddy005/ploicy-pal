from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class DocumentStatus(str, Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: DocumentStatus
    progress: int = 0
    message: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class Citation(BaseModel):
    section_id: str
    clause_name: str
    text_snippet: str


class ChatMessage(BaseModel):
    role: str
    content: str
    citations: List[Citation] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    document_id: str
    question: str
    conversation_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]


class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    text: str
    page_number: int
    section_title: Optional[str] = None
    chunk_index: int
    embedding: Optional[List[float]] = None


class Entity(BaseModel):
    entity_id: str
    name: str
    entity_type: str
    properties: Dict[str, Any] = {}


class Relationship(BaseModel):
    relationship_id: str
    source_entity_id: str
    target_entity_id: str
    relationship_type: str
    properties: Dict[str, Any] = {}


class GraphEntity(BaseModel):
    entity: Entity
    relationships: List[Relationship] = []


class SearchResult(BaseModel):
    chunk: DocumentChunk
    score: float
    entities: List[Entity] = []