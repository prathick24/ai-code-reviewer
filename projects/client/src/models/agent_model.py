import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class Base(BaseModel):
    pass


class data(Base):
  
    username: str = Field(description="Unique identifier for the user — used as thread_id to maintain session memory")
    user_query: str = Field(description="The message / question sent by the user")


class Code(BaseModel):
    Code: str = Field(description="Raw executable code only — no markdown fences, no prose")
   


class Review(BaseModel):
    ReviewResponse: dict = Field(
        description="Dict with keys: correctness, performance, security, style, suggestions"
    )
    IsReviewValid: bool = Field(
        description="True if code is production-ready with no significant issues, False otherwise"
    )
    NeedsResearch: bool = Field(
        description="True if the topic requires deep domain expertise and research before code can be regenerated"
    )


class Research(BaseModel):
    ResearchResponse: str 
    IsResearchCompleted: bool


class Error:
    def __init__(self, code: str, message: str, error_code_id: Optional[str] = None):
        self.code = code
        self.message = message
        self.error_code_id = error_code_id

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "error_code_id": self.error_code_id
        }


"""
Encapsulates a standardized API response structure for both success and error scenarios.
Automatically generates appropriate messages based on content and supports request tracing.

Attributes:
    data: Payload data (typically a list or dict); defaults to empty list
    errors: List of Error objects; if present, indicates a failed response
    code: HTTP status code (e.g., 200, 400, 500); defaults to 200
    message: User-friendly summary; auto-generated if not provided
    request_id: Unique UUID to trace requests across logs and services

Generates consistent JSON output via `to_dict()` for use in HTTP responses.

Message Logic:
    - If custom message is given -> use it
    - If no errors -> "Success"
    - If one error -> use that error's message
    - If multiple errors -> "Something went wrong."
"""


class APIResponse:
    def __init__(
        self,
        data=None,
        errors: Optional[List[Error]] = None,
        code: Optional[int] = None,
        message: Optional[str] = None
    ):
        self.data = data or []
        self.errors = errors or []
        self.code = code or 200
        self.request_id = str(uuid.uuid4())

        if message is not None:
            self.message = message
        elif not self.errors:
            self.message = "Success"
        elif len(self.errors) == 1:
            self.message = self.errors[0].message
        else:
            self.message = "Something went wrong."

    def to_dict(self):
        return {
            "data": self.data if self.data is not None else None,
            "errors": [error.to_dict() for error in self.errors] if self.errors else [],
            "status_code": self.code,
            "request_id": self.request_id,
            "message": self.message
        }
