"""
Serviço para IBM Cloud Object Storage (COS)
"""
import ibm_boto3
from ibm_botocore.client import Config
from typing import BinaryIO, Optional
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class COSService:
    """Serviço para gerenciar uploads no IBM Cloud Object Storage"""
    
    def __init__(
        self,
        api_key: str,
        instance_crn: str,
        endpoint: str,
        bucket_name: str
    ):
        """
        Inicializa o serviço COS
        
        Args:
            api_key: API Key do IBM Cloud
            instance_crn: CRN da instância do COS
            endpoint: Endpoint do COS
            bucket_name: Nome do bucket
        """
        self.bucket_name = bucket_name
        
        # Criar cliente COS
        self.cos_client = ibm_boto3.client(
            "s3",
            ibm_api_key_id=api_key,
            ibm_service_instance_id=instance_crn,
            config=Config(signature_version="oauth"),
            endpoint_url=endpoint
        )
        
        logger.info(f"COS Service inicializado para bucket: {bucket_name}")
    
    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Faz upload de um arquivo para o COS
        
        Args:
            file: Arquivo binário para upload
            filename: Nome do arquivo
            content_type: Tipo de conteúdo (MIME type)
            
        Returns:
            URL pública do arquivo no COS
        """
        try:
            # Gerar nome único para o arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = os.path.splitext(filename)[1]
            unique_filename = f"cnh_{timestamp}_{filename}"
            
            # Upload do arquivo
            self.cos_client.upload_fileobj(
                Fileobj=file,
                Bucket=self.bucket_name,
                Key=unique_filename,
                ExtraArgs={
                    "ContentType": content_type,
                    "ACL": "public-read"  # Tornar o arquivo público
                }
            )
            
            # Construir URL pública
            file_url = f"{self.cos_client.meta.endpoint_url}/{self.bucket_name}/{unique_filename}"
            
            logger.info(f"Arquivo enviado com sucesso: {unique_filename}")
            return file_url
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload do arquivo: {str(e)}")
            raise Exception(f"Falha no upload: {str(e)}")
    
    def delete_file(self, filename: str) -> bool:
        """
        Deleta um arquivo do COS
        
        Args:
            filename: Nome do arquivo a ser deletado
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        try:
            self.cos_client.delete_object(
                Bucket=self.bucket_name,
                Key=filename
            )
            logger.info(f"Arquivo deletado com sucesso: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao deletar arquivo: {str(e)}")
            return False
    
    def list_files(self, prefix: str = "") -> list:
        """
        Lista arquivos no bucket
        
        Args:
            prefix: Prefixo para filtrar arquivos
            
        Returns:
            Lista de nomes de arquivos
        """
        try:
            response = self.cos_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if "Contents" in response:
                return [obj["Key"] for obj in response["Contents"]]
            return []
            
        except Exception as e:
            logger.error(f"Erro ao listar arquivos: {str(e)}")
            return []
    
    def get_file_url(self, filename: str) -> str:
        """
        Obtém a URL pública de um arquivo
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            URL pública do arquivo
        """
        return f"{self.cos_client.meta.endpoint_url}/{self.bucket_name}/{filename}"