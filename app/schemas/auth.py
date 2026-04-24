from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$", description="Unique username (letters, numbers, _ and - only)")
    password: str = Field(..., min_length=8, description="Password — minimum 8 characters")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "riya@example.com",
                "username": "riya_reads",
                "password": "supersecret123",
            }
        }
    }


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    # Optional: pass the frontend's anonymous session ID so votes can be merged
    session_id: str | None = Field(None, description="Anonymous session ID for vote merging on login")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "riya@example.com",
                "password": "supersecret123",
                "session_id": "anon_sess_abc123",
            }
        }
    }


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "dGhpcyBpcyBhIHJlZnJlc2ggdG9rZW4...",
                "token_type": "bearer",
            }
        }
    }


class LogoutRequest(BaseModel):
    refresh_token: str
