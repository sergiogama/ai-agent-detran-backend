"""
Rotas de Chat
Endpoints para interação com o agente Detran
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
import logging

from services.chat_service import ChatService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Instâncias dos serviços (serão injetadas pelo main.py)
chat_service = None
auth_service = None


class MessageRequest(BaseModel):
    """Modelo de requisição de mensagem"""

    message: str
    conversation_id: Optional[str] = None


class MessageResponse(BaseModel):
    """Modelo de resposta de mensagem"""

    conversation_id: str
    message: str
    timestamp: str


def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Obtém usuário atual a partir do token

    Args:
        authorization: Header Authorization com o token

    Returns:
        Dados do usuário

    Raises:
        HTTPException: Se token inválido ou ausente
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    return payload


@router.post("/message", response_model=dict)
async def send_message(
    request: MessageRequest, authorization: Optional[str] = Header(None)
):
    """
    Envia uma mensagem para o agente

    Args:
        request: Mensagem e ID da conversa (opcional)
        authorization: Token de autenticação

    Returns:
        Resposta do agente

    Raises:
        HTTPException: Se não autenticado ou erro no processamento
    """
    try:
        # Verifica autenticação
        user = get_current_user(authorization)
        user_cpf = user.get("cpf")

        logger.info(
            f"Mensagem recebida de {user_cpf}: {len(request.message)} caracteres"
        )

        # Envia mensagem para o agente
        response = chat_service.send_message(
            message=request.message,
            conversation_id=request.conversation_id,
            user_cpf=user_cpf,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar mensagem: {str(e)}"
        )


@router.get("/history/{conversation_id}")
async def get_conversation_history(
    conversation_id: str, authorization: Optional[str] = Header(None)
):
    """
    Obtém histórico de uma conversa

    Args:
        conversation_id: ID da conversa
        authorization: Token de autenticação

    Returns:
        Lista de mensagens da conversa

    Raises:
        HTTPException: Se não autenticado ou conversa não encontrada
    """
    try:
        # Verifica autenticação
        user = get_current_user(authorization)

        logger.info(f"Histórico solicitado para conversa: {conversation_id}")

        # Obtém histórico
        history = chat_service.get_conversation_history(conversation_id)

        return {"conversation_id": conversation_id, "messages": history}

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Erro ao obter histórico: {str(e)}"
        )