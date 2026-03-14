"""
Serviço de Autenticação
Gerencia login e validação de usuários usando Db2Service (driver nativo)
"""

import jwt
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)

# Configurações JWT
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "detran-sp-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas


class AuthServiceRest:
    """Serviço de autenticação de usuários"""

    def __init__(self, db2_service=None):
        """
        Inicializa o serviço de autenticação
        
        Args:
            db2_service: Instância do Db2Service (driver nativo)
        """
        if db2_service:
            self.db2_service = db2_service
        else:
            # Será injetado pelo main.py
            self.db2_service = None
            logger.warning("AuthServiceRest inicializado sem db2_service")

    def authenticate_user(self, cpf: str, senha: str) -> Optional[Dict]:
        """
        Autentica um usuário por CPF e senha

        Args:
            cpf: CPF do condutor (com ou sem formatação)
            senha: Senha do condutor

        Returns:
            Dados do condutor se autenticado, None caso contrário
        """
        if not self.db2_service:
            logger.error("Db2ServiceRest não configurado")
            return None

        try:
            # Remove formatação do CPF
            cpf_limpo = cpf.replace(".", "").replace("-", "")
            
            # Formata CPF: 000.000.000-00
            if len(cpf_limpo) == 11:
                cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
            else:
                cpf_formatado = cpf
            
            # Busca condutor usando REST API
            condutor = self.db2_service.get_condutor_by_cpf(cpf_formatado)
            
            if not condutor:
                logger.warning(f"Condutor não encontrado: {cpf_formatado}")
                return None

            # Verifica senha
            senha_db = condutor.get("SENHA")
            if not senha_db or senha_db != senha:
                logger.warning(f"Senha incorreta para CPF: {cpf_formatado}")
                return None

            logger.info(f"Usuário autenticado com sucesso: {cpf_formatado}")
            return condutor

        except Exception as e:
            logger.error(f"Erro na autenticação: {str(e)}")
            return None

    def create_access_token(self, data: dict) -> str:
        """
        Cria um token JWT de acesso

        Args:
            data: Dados a serem codificados no token

        Returns:
            Token JWT
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verifica e decodifica um token JWT

        Args:
            token: Token JWT a ser verificado

        Returns:
            Dados decodificados do token ou None se inválido
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expirado")
            return None
        except jwt.JWTError as e:
            logger.warning(f"Token inválido: {str(e)}")
            return None

    def login(self, cpf: str, senha: str) -> Optional[Dict]:
        """
        Realiza o login do usuário

        Args:
            cpf: CPF do condutor
            senha: Senha do condutor

        Returns:
            Dict com token e dados do usuário, ou None se falhar
        """
        # Autentica usuário
        condutor = self.authenticate_user(cpf, senha)

        if not condutor:
            return None

        # Cria token
        token_data = {
            "cpf": condutor.get("CPF"),
            "id_condutor": condutor.get("ID_CONDUTOR"),
            "nome": condutor.get("NOME"),
        }
        access_token = self.create_access_token(token_data)

        # Retorna token e dados do usuário
        return {
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "cpf": condutor.get("CPF"),
                "nome": condutor.get("NOME"),
                "cnh": condutor.get("CNH"),
                "categoria_cnh": condutor.get("CATEGORIA_CNH"),
            },
        }