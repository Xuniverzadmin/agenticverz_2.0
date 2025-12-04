# Skill I/O Schemas
# Pydantic models for skill input/output validation

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class SkillStatus(str, Enum):
    """Skill execution status."""
    OK = "ok"
    ERROR = "error"
    STUBBED = "stubbed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"


class SkillInputBase(BaseModel):
    """Base class for all skill inputs.

    All skill-specific inputs should inherit from this.
    Provides common validation and serialization.
    """
    model_config = ConfigDict(extra="forbid")  # Reject unknown fields for strict validation


class SkillOutputBase(BaseModel):
    """Base class for all skill outputs.

    Provides consistent structure for all skill results.
    """
    model_config = ConfigDict(extra="allow")  # Allow skill-specific output fields

    skill: str = Field(description="Skill name that produced this output")
    skill_version: str = Field(description="Version of the skill")
    status: SkillStatus = Field(description="Execution status")
    duration_seconds: float = Field(ge=0, description="Execution duration")
    started_at: datetime = Field(description="When execution started")
    completed_at: datetime = Field(description="When execution completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")


# ====================
# HTTP Call Skill I/O
# ====================

class HttpMethod(str, Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class HttpCallInput(SkillInputBase):
    """Input schema for http_call skill."""
    url: str = Field(
        description="URL to call",
        examples=["https://api.github.com/zen"]
    )
    method: HttpMethod = Field(
        default=HttpMethod.GET,
        description="HTTP method"
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Request headers"
    )
    body: Optional[Union[Dict[str, Any], str]] = Field(
        default=None,
        description="Request body (JSON object or string)"
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=0.1,
        le=300,
        description="Request timeout in seconds"
    )
    follow_redirects: bool = Field(
        default=True,
        description="Follow HTTP redirects"
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class HttpCallOutput(SkillOutputBase):
    """Output schema for http_call skill."""
    status_code: int = Field(description="HTTP response status code")
    response_body: Optional[str] = Field(
        default=None,
        max_length=10000,
        description="Response body (truncated to 10KB)"
    )
    response_headers: Optional[Dict[str, str]] = Field(
        default=None,
        description="Response headers"
    )
    attempts: int = Field(
        default=1,
        ge=1,
        description="Number of attempts made"
    )


# ====================
# LLM Invoke Skill I/O
# ====================

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"


class LLMMessage(BaseModel):
    """A single message in the LLM conversation."""
    role: str = Field(description="Message role: system, user, assistant")
    content: str = Field(description="Message content")


class LLMInvokeInput(SkillInputBase):
    """Input schema for llm_invoke skill."""
    provider: LLMProvider = Field(
        default=LLMProvider.ANTHROPIC,
        description="LLM provider to use"
    )
    model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model identifier"
    )
    messages: List[LLMMessage] = Field(
        min_length=1,
        description="Conversation messages"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="System prompt (prepended)"
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=8192,
        description="Maximum tokens to generate"
    )
    temperature: float = Field(
        default=0.7,
        ge=0,
        le=2,
        description="Sampling temperature"
    )
    stop_sequences: Optional[List[str]] = Field(
        default=None,
        description="Stop sequences"
    )


class LLMInvokeOutput(SkillOutputBase):
    """Output schema for llm_invoke skill."""
    response_text: str = Field(description="Generated text response")
    llm_model: str = Field(description="Actual model used", alias="model_used")
    input_tokens: int = Field(ge=0, description="Input token count")
    output_tokens: int = Field(ge=0, description="Output token count")
    finish_reason: str = Field(description="Why generation stopped")
    cost_cents: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated cost in cents"
    )
    model_config = ConfigDict(populate_by_name=True)  # Allow both llm_model and model_used


# ====================
# File Read Skill I/O
# ====================

class FileReadInput(SkillInputBase):
    """Input schema for file_read skill."""
    path: str = Field(description="File path to read")
    encoding: str = Field(default="utf-8", description="File encoding")
    max_bytes: int = Field(
        default=1_000_000,
        ge=1,
        le=10_000_000,
        description="Maximum bytes to read"
    )


class FileReadOutput(SkillOutputBase):
    """Output schema for file_read skill."""
    content: str = Field(description="File contents")
    size_bytes: int = Field(ge=0, description="File size in bytes")
    encoding: str = Field(description="Encoding used")
    truncated: bool = Field(default=False, description="Was content truncated")


# ====================
# File Write Skill I/O
# ====================

class FileWriteInput(SkillInputBase):
    """Input schema for file_write skill."""
    path: str = Field(description="File path to write")
    content: str = Field(description="Content to write")
    encoding: str = Field(default="utf-8", description="File encoding")
    mode: str = Field(
        default="write",
        pattern="^(write|append)$",
        description="Write mode: write or append"
    )
    create_dirs: bool = Field(
        default=True,
        description="Create parent directories if needed"
    )


class FileWriteOutput(SkillOutputBase):
    """Output schema for file_write skill."""
    path: str = Field(description="Path written to")
    bytes_written: int = Field(ge=0, description="Bytes written")


# ====================
# Postgres Query Skill I/O
# ====================

class PostgresQueryInput(SkillInputBase):
    """Input schema for postgres_query skill."""
    query: str = Field(description="SQL query to execute")
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Query parameters for safe interpolation"
    )
    database: Optional[str] = Field(
        default=None,
        description="Database name (uses default if not specified)"
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1,
        le=300,
        description="Query timeout"
    )
    max_rows: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum rows to return"
    )


class PostgresQueryOutput(SkillOutputBase):
    """Output schema for postgres_query skill."""
    rows: List[Dict[str, Any]] = Field(description="Query results")
    row_count: int = Field(ge=0, description="Number of rows returned")
    columns: List[str] = Field(description="Column names")
    truncated: bool = Field(default=False, description="Was result truncated")


# ====================
# JSON Transform Skill I/O
# ====================

class JsonTransformInput(SkillInputBase):
    """Input schema for json_transform skill."""
    data: Union[Dict[str, Any], List[Any]] = Field(description="Input JSON data")
    jmespath: Optional[str] = Field(
        default=None,
        description="JMESPath expression to apply"
    )
    jsonpath: Optional[str] = Field(
        default=None,
        description="JSONPath expression to apply"
    )
    template: Optional[str] = Field(
        default=None,
        description="Jinja2 template for transformation"
    )


class JsonTransformOutput(SkillOutputBase):
    """Output schema for json_transform skill."""
    result: Union[Dict[str, Any], List[Any], str, int, float, bool, None] = Field(
        description="Transformed result"
    )
    input_type: str = Field(description="Type of input data")
    output_type: str = Field(description="Type of output data")


# ====================
# Skill Metadata Schema (for registry)
# ====================

class SkillMetadata(BaseModel):
    """Metadata about a registered skill."""
    name: str = Field(description="Unique skill identifier")
    version: str = Field(description="Semantic version")
    description: str = Field(description="Human-readable description")
    input_schema: Dict[str, Any] = Field(description="JSON Schema for input")
    output_schema: Dict[str, Any] = Field(description="JSON Schema for output")
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    requires_config: bool = Field(
        default=False,
        description="Whether skill requires configuration"
    )
    config_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON Schema for config if required"
    )
