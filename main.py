"""
Backend API - Detran Agent
FastAPI application para upload de CNH e chat com Watsonx Orchestrate
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime
import os
from typing import Optional

from config import settings
from models import (
    UploadResponse,
    ChatRequest,
    ChatResponse,
    SessionResponse,
    HealthResponse,
    ErrorResponse
)
from services import COSService, OrchestrateService, Db2Service
from api import db2_router
from api.auth_routes import router as auth_router
from api.chat_routes import router as chat_router

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Criar aplicação FastAPI
app = FastAPI(
    title="Detran Agent API",
    description="API para upload de CNH e chat com agente Watsonx Orchestrate",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar serviços (opcionais)
cos_service = None
orchestrate_service = None
db2_service = None

# Inicializar COS se configurado
if all([settings.cos_api_key, settings.cos_instance_crn, settings.cos_endpoint, settings.cos_bucket_name]):
    try:
        cos_service = COSService(
            api_key=settings.cos_api_key,
            instance_crn=settings.cos_instance_crn,
            endpoint=settings.cos_endpoint,
            bucket_name=settings.cos_bucket_name
        )
        logger.info("COS Service inicializado com sucesso")
    except Exception as e:
        logger.warning(f"Não foi possível inicializar COS Service: {e}")
else:
    logger.warning("COS Service não configurado - variáveis de ambiente ausentes")

# Inicializar Orchestrate se configurado
if all([settings.orchestrate_api_url, settings.orchestrate_api_key, settings.orchestrate_agent_id]):
    try:
        orchestrate_service = OrchestrateService(
            api_url=settings.orchestrate_api_url,
            api_key=settings.orchestrate_api_key,
            agent_id=settings.orchestrate_agent_id
        )
        logger.info("Orchestrate Service inicializado com sucesso")
    except Exception as e:
        logger.warning(f"Não foi possível inicializar Orchestrate Service: {e}")
else:
    logger.warning("Orchestrate Service não configurado - variáveis de ambiente ausentes")

# Inicializar Db2 com driver nativo se configurado
if all([settings.db2_hostname, settings.db2_database, settings.db2_username, settings.db2_password]):
    try:
        db2_service = Db2Service(
            hostname=settings.db2_hostname,
            port=settings.db2_port,
            database=settings.db2_database,
            username=settings.db2_username,
            password=settings.db2_password,
            security=settings.db2_security
        )
        logger.info("Db2 Service inicializado com driver nativo")
    except Exception as e:
        logger.warning(f"Não foi possível inicializar Db2 Service: {e}")
else:
    logger.warning("Db2 Service não configurado - variáveis de ambiente ausentes")

# Inicializar Auth Service com Db2 nativo (do db2_router)
auth_service_instance = None
try:
    from services.auth_service_rest import AuthServiceRest
    from api.db2_routes import db2_service as db2_native_service
    
    auth_service_instance = AuthServiceRest(db2_service=db2_native_service)
    logger.info("Auth Service inicializado com Db2 nativo")
    
    # Injetar no módulo auth_routes
    import api.auth_routes as auth_routes_module
    auth_routes_module.auth_service = auth_service_instance
except Exception as e:
    logger.warning(f"Não foi possível inicializar Auth Service: {e}")

# Inicializar Chat Service com Orchestrate
chat_service_instance = None
try:
    from services.chat_service import ChatService
    
    if orchestrate_service:
        chat_service_instance = ChatService(orchestrate_service=orchestrate_service)
        logger.info("Chat Service inicializado com OrchestrateService")
    else:
        chat_service_instance = ChatService()
        logger.warning("Chat Service inicializado sem OrchestrateService - usando respostas simuladas")
    
    # Injetar no módulo chat_routes
    import api.chat_routes as chat_routes_module
    chat_routes_module.chat_service = chat_service_instance
    chat_routes_module.auth_service = auth_service_instance
except Exception as e:
    logger.warning(f"Não foi possível inicializar Chat Service: {e}")

# Incluir routers
app.include_router(db2_router)
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/", response_model=dict)
async def root():
    """Endpoint raiz"""
    return {
        "message": "Detran Agent API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "upload": "/api/upload",
            "chat": "/api/chat",
            "session": "/api/session"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {
        "cos": "connected" if cos_service else "not_configured",
        "orchestrate": "connected" if orchestrate_service else "not_configured",
        "db2": "connected" if db2_service else "not_configured"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        services=services_status
    )


@app.post("/api/upload", response_model=UploadResponse)
async def upload_cnh_image(file: UploadFile = File(...)):
    """
    Upload de imagem da CNH para IBM Cloud Object Storage
    
    Args:
        file: Arquivo de imagem da CNH
        
    Returns:
        URL pública da imagem no COS
    """
    if not cos_service:
        raise HTTPException(
            status_code=503,
            detail="COS Service não está configurado. Configure as variáveis de ambiente necessárias."
        )
    
    try:
        # Validar extensão do arquivo
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Extensão não permitida. Use: {', '.join(settings.allowed_extensions)}"
            )
        
        # Validar tamanho do arquivo
        file.file.seek(0, 2)  # Ir para o final do arquivo
        file_size = file.file.tell()
        file.file.seek(0)  # Voltar ao início
        
        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.max_upload_size / 1024 / 1024}MB"
            )
        
        # Determinar content type
        content_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".pdf": "application/pdf"
        }
        content_type = content_type_map.get(file_extension, "application/octet-stream")
        
        # Upload para COS
        file_url = cos_service.upload_file(
            file=file.file,
            filename=file.filename,
            content_type=content_type
        )
        
        logger.info(f"Upload realizado com sucesso: {file.filename}")
        
        return UploadResponse(
            success=True,
            file_url=file_url,
            filename=file.filename,
            message="Upload realizado com sucesso"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao fazer upload: {str(e)}"
        )


@app.post("/api/session", response_model=SessionResponse)
async def create_session():
    """
    Cria uma nova sessão de conversa com o agente
    
    Returns:
        ID da sessão criada
    """
    if not orchestrate_service:
        raise HTTPException(
            status_code=503,
            detail="Orchestrate Service não está configurado. Configure as variáveis de ambiente necessárias."
        )
    
    try:
        session_id = orchestrate_service.create_session()
        
        return SessionResponse(
            session_id=session_id,
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar sessão: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao criar sessão: {str(e)}"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Envia mensagem para o agente Watsonx Orchestrate
    
    Args:
        request: Requisição com mensagem e dados opcionais
        
    Returns:
        Resposta do agente
    """
    if not orchestrate_service:
        raise HTTPException(
            status_code=503,
            detail="Orchestrate Service não está configurado. Configure as variáveis de ambiente necessárias."
        )
    
    try:
        # Preparar contexto
        context = {}
        if request.cnh_image_url:
            context["cnh_image_url"] = request.cnh_image_url
        
        # Enviar mensagem
        response = orchestrate_service.send_message(
            message=request.message,
            session_id=request.session_id,
            context=context if context else None
        )
        
        return ChatResponse(
            session_id=response["session_id"],
            message=response["message"],
            timestamp=response.get("timestamp"),
            metadata=response.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Erro no chat: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar mensagem: {str(e)}"
        )


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    """
    Deleta uma sessão de conversa
    
    Args:
        session_id: ID da sessão a ser deletada
        
    Returns:
        Confirmação de deleção
    """
    if not orchestrate_service:
        raise HTTPException(
            status_code=503,
            detail="Orchestrate Service não está configurado. Configure as variáveis de ambiente necessárias."
        )
    
    try:
        success = orchestrate_service.delete_session(session_id)
        
        if success:
            return {"message": "Sessão deletada com sucesso", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao deletar sessão: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao deletar sessão: {str(e)}"
        )


@app.get("/api/session/{session_id}/history")
async def get_conversation_history(session_id: str):
    """
    Obtém o histórico de conversa de uma sessão
    
    Args:
        session_id: ID da sessão
        
    Returns:
        Lista de mensagens da conversa
    """
    if not orchestrate_service:
        raise HTTPException(
            status_code=503,
            detail="Orchestrate Service não está configurado. Configure as variáveis de ambiente necessárias."
        )
    
    try:
        history = orchestrate_service.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "messages": history
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao obter histórico: {str(e)}"
        )


# Exception handler global
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload
    )