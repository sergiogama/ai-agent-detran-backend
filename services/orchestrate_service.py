"""
Serviço para IBM Watsonx Orchestrate
"""
import requests
import logging
import json
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

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
            api_key: API Key para autenticação IAM
            agent_id: ID do agente a ser usado
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.agent_id = agent_id
        self.access_token = None
        self.token_expiry = None
        
        logger.info(f"Orchestrate Service inicializado para agente: {agent_id}")
    
    def _get_iam_token(self) -> str:
        """
        Obtém token de acesso IAM usando a API key
        
        Returns:
            Token de acesso IAM
        """
        try:
            # Verificar se token ainda é válido
            if self.access_token and self.token_expiry:
                if datetime.now() < self.token_expiry:
                    return self.access_token
            
            # Obter novo token
            url = "https://iam.cloud.ibm.com/identity/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            data = {
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self.api_key
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            
            # Token expira em 1 hora, renovar 5 minutos antes
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)
            
            logger.info("Token IAM obtido com sucesso")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao obter token IAM: {str(e)}")
            raise Exception(f"Falha ao obter token IAM: {str(e)}")
    
    def _get_headers(self) -> Dict[str, str]:
        """Retorna os headers para as requisições"""
        token = self._get_iam_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def send_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Envia uma mensagem para o agente usando a API /v1/orchestrate/runs com streaming
        
        Args:
            message: Mensagem do usuário
            session_id: ID da thread/conversa (opcional)
            context: Contexto adicional (opcional)
            
        Returns:
            Resposta do agente
        """
        try:
            import time
            
            # Timestamp 1: Início
            t1_start = time.time()
            
            url = f"{self.api_url}/v1/orchestrate/runs?stream=true"
            
            # Construir payload conforme documentação
            payload = {
                "agent_id": self.agent_id,
                "message": {
                    "role": "user",
                    "content": [
                        {
                            "response_type": "text",
                            "text": message
                        }
                    ]
                }
            }
            
            # Adicionar thread_id se fornecido
            if session_id:
                payload["thread_id"] = session_id
            
            # Log do CPF do usuário (sem modificar a mensagem)
            if context and "user_cpf" in context:
                user_cpf = context["user_cpf"]
                logger.info(f"Mensagem enviada pelo usuário CPF: {user_cpf}")
            
            logger.info(f"Enviando mensagem para Orchestrate com streaming: {message[:50]}...")
            logger.info(f"Agent ID: {self.agent_id}")
            
            # Timestamp 2: Antes da chamada HTTP
            t2_before_http = time.time()
            
            # Timeout aumentado para suportar tools lentas do DB2
            # Langfuse mostra 91s (0.67s latency + 90s tools), então usamos 120s com margem
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=120,  # 120s para tools do DB2 (91s observado no Langfuse + margem)
                stream=False  # Receber resposta completa
            )
            
            # Timestamp 3: Após receber resposta HTTP
            t3_after_http = time.time()
            
            logger.info(f"Status da resposta: {response.status_code}")
            response.raise_for_status()
            
            # Processar resposta completa
            agent_message = ""
            thread_id = session_id
            response_data = {}
            
            logger.info("🚀 Processando resposta completa...")
            
            try:
                # Obter resposta como JSON
                response_data = response.json()
                logger.info(f"📥 Resposta JSON recebida. Keys: {list(response_data.keys())}")
                
                # Caso 1: Resposta direta do Watsonx (formato: {"role": "assistant", "content": "..."})
                if "role" in response_data and "content" in response_data:
                    logger.info(f"✅ Resposta direta do Watsonx detectada")
                    agent_message = response_data["content"]
                    thread_id = response_data.get("thread_id", thread_id)
                    logger.info(f"✅ Mensagem extraída (len={len(agent_message)}): {agent_message[:200]}...")
                
                # Caso 2: Formato com envelope
                elif "data" in response_data:
                    event_data = response_data.get("data", {})
                    logger.info(f"✅ Formato com envelope - Data keys: {list(event_data.keys())}")
                        
                    # Extrair thread_id
                    if "thread_id" in event_data:
                        thread_id = event_data["thread_id"]
                        logger.info(f"🔗 Thread ID: {thread_id}")
                    
                    # Extrair mensagem
                    if "message" in event_data:
                        msg = event_data["message"]
                        if isinstance(msg, str):
                            agent_message = msg
                        elif isinstance(msg, dict) and "content" in msg:
                            agent_message = msg["content"]
                    elif "content" in event_data:
                        agent_message = event_data["content"]
                
                logger.info(f"✅ Processamento concluído. Message length: {len(agent_message)}")
                        
            except Exception as e:
                logger.error(f"💥 Erro ao processar resposta: {e}", exc_info=True)
            
            if not agent_message:
                logger.error("❌ CRÍTICO: Nenhuma mensagem capturada da resposta!")
                logger.error(f"   Thread ID: {thread_id}")
                logger.error(f"   Response data: {json.dumps(response_data)[:500]}")
                agent_message = "Desculpe, não recebi resposta do agente."
            else:
                logger.info(f"✅ Mensagem capturada com sucesso!")
                logger.info(f"   Tamanho: {len(agent_message)} caracteres")
                logger.info(f"   Thread ID: {thread_id}")
                logger.info(f"   Resposta: {agent_message[:200]}...")
            
            # Timestamp 4: Fim do processamento
            t4_end = time.time()
            
            # Calcular tempos (em milissegundos)
            timing = {
                "preparation_ms": int((t2_before_http - t1_start) * 1000),
                "http_call_ms": int((t3_after_http - t2_before_http) * 1000),
                "processing_ms": int((t4_end - t3_after_http) * 1000),
                "total_ms": int((t4_end - t1_start) * 1000)
            }
            
            logger.info(f"⏱️  Timing - Prep: {timing['preparation_ms']}ms | HTTP: {timing['http_call_ms']}ms | Process: {timing['processing_ms']}ms | Total: {timing['total_ms']}ms")
            
            return {
                "session_id": thread_id,
                "message": agent_message,
                "metadata": {},
                "timestamp": datetime.now().isoformat(),
                "timing": timing
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Resposta do servidor: {e.response.text}")
            raise Exception(f"Falha ao enviar mensagem: {str(e)}")
    
    def create_session(self) -> Optional[str]:
        """
        Cria uma nova sessão/thread
        Na API v1/orchestrate/runs, o thread_id é criado automaticamente
        na primeira mensagem se não for fornecido
        
        Returns:
            ID da sessão (None para criar automaticamente)
        """
        logger.info("Thread será criado automaticamente na primeira mensagem")
        return None
    
    def get_conversation_history(
        self,
        session_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Obtém o histórico de conversa de uma sessão
        Nota: Esta funcionalidade pode não estar disponível na API v1/orchestrate/runs
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de mensagens da conversa
        """
        logger.warning("get_conversation_history não implementado para API v1/orchestrate/runs")
        return []
    
    def delete_session(self, session_id: Optional[str] = None) -> bool:
        """
        Deleta uma sessão
        Nota: Esta funcionalidade pode não estar disponível na API v1/orchestrate/runs
        
        Args:
            session_id: ID da sessão
            
        Returns:
            True se deletada com sucesso
        """
        logger.warning("delete_session não implementado para API v1/orchestrate/runs")
        return True
    
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
        
        return self.send_message(message, context=context if context else None)