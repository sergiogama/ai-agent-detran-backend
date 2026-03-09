"""
Serviço para IBM Watsonx Orchestrate
"""
import requests
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OrchestrateService:
    """Serviço para interagir com o agente Watsonx Orchestrate"""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        agent_id: str
    ):
        """
        Inicializa o serviço Orchestrate
        
        Args:
            api_url: URL base da API do Watsonx Orchestrate
            api_key: API Key para autenticação
            agent_id: ID do agente a ser usado
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.agent_id = agent_id
        self.session_id = None
        
        logger.info(f"Orchestrate Service inicializado para agente: {agent_id}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna os headers para as requisições"""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def create_session(self) -> str:
        """
        Cria uma nova sessão de conversa
        
        Returns:
            ID da sessão criada
        """
        try:
            url = f"{self.api_url}/sessions"
            payload = {
                "agent_id": self.agent_id
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            self.session_id = data.get("session_id")
            
            logger.info(f"Sessão criada: {self.session_id}")
            return self.session_id
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao criar sessão: {str(e)}")
            raise Exception(f"Falha ao criar sessão: {str(e)}")
    
    def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Envia uma mensagem para o agente
        
        Args:
            message: Mensagem do usuário
            session_id: ID da sessão (opcional, usa a sessão atual se não fornecido)
            context: Contexto adicional (opcional)
            
        Returns:
            Resposta do agente
        """
        try:
            # Usar sessão fornecida ou criar nova
            if not session_id:
                if not self.session_id:
                    self.create_session()
                session_id = self.session_id
            
            url = f"{self.api_url}/sessions/{session_id}/messages"
            payload = {
                "message": message,
                "agent_id": self.agent_id
            }
            
            if context:
                payload["context"] = context
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Mensagem enviada com sucesso para sessão: {session_id}")
            
            return {
                "session_id": session_id,
                "message": data.get("response", ""),
                "metadata": data.get("metadata", {}),
                "timestamp": data.get("timestamp")
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            raise Exception(f"Falha ao enviar mensagem: {str(e)}")
    
    def get_conversation_history(
        self,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtém o histórico de conversa de uma sessão
        
        Args:
            session_id: ID da sessão (opcional, usa a sessão atual se não fornecido)
            
        Returns:
            Lista de mensagens da conversa
        """
        try:
            if not session_id:
                session_id = self.session_id
            
            if not session_id:
                raise Exception("Nenhuma sessão ativa")
            
            url = f"{self.api_url}/sessions/{session_id}/history"
            
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("messages", [])
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter histórico: {str(e)}")
            raise Exception(f"Falha ao obter histórico: {str(e)}")
    
    def delete_session(self, session_id: Optional[str] = None) -> bool:
        """
        Deleta uma sessão
        
        Args:
            session_id: ID da sessão (opcional, usa a sessão atual se não fornecido)
            
        Returns:
            True se deletada com sucesso
        """
        try:
            if not session_id:
                session_id = self.session_id
            
            if not session_id:
                return False
            
            url = f"{self.api_url}/sessions/{session_id}"
            
            response = requests.delete(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            if session_id == self.session_id:
                self.session_id = None
            
            logger.info(f"Sessão deletada: {session_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao deletar sessão: {str(e)}")
            return False
    
    def chat(
        self,
        message: str,
        cnh_image_url: Optional[str] = None
    ) -> Dict:
        """
        Método simplificado para chat com o agente
        
        Args:
            message: Mensagem do usuário
            cnh_image_url: URL da imagem da CNH (opcional)
            
        Returns:
            Resposta do agente
        """
        context = {}
        if cnh_image_url:
            context["cnh_image_url"] = cnh_image_url
        
        return self.send_message(message, context=context)