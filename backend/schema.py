"""
backend/schema.py
Pydantic schemas and data validation models for API requests, responses,
and e-commerce analytics objects.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., description="User's natural language question in simple English")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation tracking ID")
    filter_params: Optional[Dict[str, Any]] = Field(default=None, description="Optional analytical filters")


class ChatRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="User query in simple English")
    message: Optional[str] = Field(default=None, description="Alternative alias for query")
    schema_info: Optional[Dict[str, Any]] = Field(default=None, alias="schema", description="Dataset schema or column definitions")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Dataset context, active filters, or background metadata")
    conversation_id: Optional[str] = Field(default="default_session", description="Conversation tracking session ID")

    class Config:
        populate_by_name = True


class QueryResponse(BaseModel):
    answer: str = Field(..., description="Explanation of findings written in clear, simple English")
    intent: str = Field(..., description="Recognized query intent")
    chart_url: Optional[str] = Field(default=None, description="URL of generated visualization chart")
    data_table: Optional[List[Dict[str, Any]]] = Field(default=None, description="Structured tabular data records")
    execution_type: str = Field(default="autonomous_engine", description="Engine used (autonomous_engine / llm)")
    status: str = Field(default="success", description="Status code or error string")
    suggestions: List[str] = Field(default_factory=list, description="Follow-up question suggestions")


class KPISummary(BaseModel):
    total_revenue: float
    formatted_revenue: str
    total_orders: int
    total_qty: int
    average_order_value: float
    formatted_aov: str
    cancellation_rate: float
    top_category: str
    top_city: str
    b2b_percentage: float


class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    file_type: str
    records_count: Optional[int] = None
    columns: Optional[List[str]] = None


class DatasetMetadata(BaseModel):
    total_records: int
    columns: List[str]
    date_range: Optional[Dict[str, str]] = None
    currencies: List[str] = Field(default_factory=list)
    available_files: Dict[str, Any] = Field(default_factory=dict)
