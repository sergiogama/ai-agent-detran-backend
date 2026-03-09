"""
Configuração do Backend - Detran Agent
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # IBM Cloud Object Storage
    cos_api_key: str
    cos_instance_crn: str
    cos_endpoint: str
    cos_bucket_name: str
    
    # IBM Db2 Warehouse
    db2_hostname: str
    db2_port: int
    db2_database: str
    db2_username: str
    db2_password: str
    db2_security: str = "SSL"
    db2_verify_ssl: bool = False  # Desabilitar verificação SSL para IBM Cloud Db2
    
    # IBM Watsonx Orchestrate
    orchestrate_api_url: str
    orchestrate_api_key: str
    orchestrate_agent_id: str
    
    # Backend
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_reload: bool = True
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Upload
    max_upload_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = [".jpg", ".jpeg", ".png", ".pdf"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Instância global de configurações
settings = Settings()