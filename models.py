"""
Modelos de dados do Backend
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UploadResponse(BaseModel):
    """Resposta do upload de imagem"""
    success: bool
    file_url: str
    filename: str
    message: str


class ChatRequest(BaseModel):
    """Requisição de chat"""
    message: str = Field(..., description="Mensagem do usuário")
    session_id: Optional[str] = Field(None, description="ID da sessão (opcional)")
    cnh_image_url: Optional[str] = Field(None, description="URL da imagem da CNH (opcional)")


class ChatResponse(BaseModel):
    """Resposta do chat"""
    session_id: str
    message: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """Resposta de criação de sessão"""
    session_id: str
    created_at: str


class HealthResponse(BaseModel):
    """Resposta de health check"""
    status: str
    timestamp: str
    services: Dict[str, str]


class ErrorResponse(BaseModel):
    """Resposta de erro"""
    error: str
    detail: Optional[str] = None
    timestamp: str