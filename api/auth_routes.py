"""
Rotas de Autenticação
Endpoints para login e gerenciamento de sessão
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import logging

# Importar ambos os serviços
try:
    from services.auth_service import AuthService
    auth_service = AuthService()
    logger = logging.getLogger(__name__)
    logger.info("Usando AuthService com driver nativo")
except Exception as e:
    # Fallback para REST API se driver nativo falhar
    from services.auth_service_rest import AuthServiceRest
    auth_service = None  # Será inicializado no main.py
    logger = logging.getLogger(__name__)
    logger.warning(f"Driver nativo não disponível, usando REST API: {e}")

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


class LoginRequest(BaseModel):
    """Modelo de requisição de login"""

    cpf: str
    senha: str


class LoginResponse(BaseModel):
    """Modelo de resposta de login"""

    token: str
    user: dict


@router.post("/login", response_model=dict)
async def login(request: LoginRequest):
    """
    Endpoint de login

    Args:
        request: Dados de login (CPF e senha)

    Returns:
        Token de acesso e dados do usuário

    Raises:
        HTTPException: Se credenciais inválidas
    """
    try:
        logger.info(f"Tentativa de login para CPF: {request.cpf}")

        # Realiza login
        result = auth_service.login(request.cpf, request.senha)

        if not result:
            logger.warning(f"Login falhou para CPF: {request.cpf}")
            raise HTTPException(
                status_code=401, detail="CPF ou senha incorretos"
            )

        logger.info(f"Login bem-sucedido para CPF: {request.cpf}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")


@router.post("/verify")
async def verify_token(authorization: Optional[str] = Header(None)):
    """
    Verifica se um token é válido

    Args:
        authorization: Header Authorization com o token

    Returns:
        Dados do token se válido

    Raises:
        HTTPException: Se token inválido ou ausente
    """
    try:
        if not authorization:
            raise HTTPException(status_code=401, detail="Token não fornecido")

        # Remove "Bearer " do início
        token = authorization.replace("Bearer ", "")

        # Verifica token
        payload = auth_service.verify_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido ou expirado")

        return {"valid": True, "user": payload}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao verificar token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no servidor: {str(e)}")


@router.post("/logout")
async def logout():
    """
    Endpoint de logout (cliente deve remover o token)

    Returns:
        Mensagem de sucesso
    """
    return {"message": "Logout realizado com sucesso"}