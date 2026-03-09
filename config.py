"""
Configuração do Backend - Detran Agent
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # IBM Cloud Object Storage (opcional para permitir inicialização)
    cos_api_key: Optional[str] = None
    cos_instance_crn: Optional[str] = None
    cos_endpoint: Optional[str] = None
    cos_bucket_name: Optional[str] = None
    
    # IBM Db2 Warehouse (opcional para permitir inicialização)
    db2_hostname: Optional[str] = None
    db2_port: Optional[int] = None
    db2_database: Optional[str] = None
    db2_username: Optional[str] = None
    db2_password: Optional[str] = None
    db2_security: str = "SSL"
    db2_verify_ssl: bool = False  # Desabilitar verificação SSL para IBM Cloud Db2
    
    # IBM Watsonx Orchestrate (opcional para permitir inicialização)
    orchestrate_api_url: Optional[str] = None
    orchestrate_api_key: Optional[str] = None
    orchestrate_agent_id: Optional[str] = None
    
    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8080  # Porta padrão do Code Engine
    backend_reload: bool = False  # Desabilitado em produção
    
    # CORS
    cors_origins: List[str] = ["*"]  # Permitir todas as origens (ajuste em produção)
    
    # Upload
    max_upload_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".pdf"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Não falhar se .env não existir
        env_file_encoding = 'utf-8'


# Instância global de configurações
try:
    settings = Settings()
except Exception as e:
    print(f"⚠️  Aviso: Erro ao carregar configurações: {e}")
    print("⚠️  Algumas funcionalidades podem não estar disponíveis.")
    print("⚠️  Configure as variáveis de ambiente no Code Engine.")
    settings = Settings()