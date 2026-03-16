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
            
            # Timeout reduzido - sem cold start (min instances = 1)
            # Watsonx Orchestrate normalmente responde em 5-15 segundos
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30,  # 30s é suficiente sem cold start
                stream=True
            )
            
            logger.info(f"Status da resposta: {response.status_code}")
            response.raise_for_status()
            
            # Processar resposta em streaming
            agent_message = ""
            thread_id = session_id
            done_received = False
            last_data_time = time.time()
            idle_timeout = 45  # 45s idle timeout (sem cold start)
            line_count = 0
            
            logger.info("🚀 Iniciando processamento do streaming...")
            
            try:
                for line in response.iter_lines(decode_unicode=True):
                    line_count += 1
                    
                    # Verificar timeout de inatividade
                    if time.time() - last_data_time > idle_timeout:
                        logger.warning(f"⏱️ Timeout de inatividade ({idle_timeout}s) - finalizando streaming")
                        break
                    
                    if not line or line.strip() == "":
                        continue
                    
                    last_data_time = time.time()
                    line = line.strip()
                    
                    logger.info(f"📥 Linha {line_count}: {line[:300]}")
                    
                    # Tentar parsear como JSON
                    try:
                        data = json.loads(line)
                        event_type = data.get("event")
                        event_data = data.get("data", {})
                        
                        logger.info(f"✅ JSON parseado - Event: '{event_type}', Data keys: {list(event_data.keys())}")
                        
                        # Extrair thread_id
                        if "thread_id" in event_data:
                            thread_id = event_data["thread_id"]
                            logger.info(f"🔗 Thread ID: {thread_id}")
                        
                        # Tentar extrair mensagem de TODOS os campos possíveis
                        extracted = False
                        
                        # Campo 'message'
                        if "message" in event_data:
                            msg = event_data["message"]
                            logger.info(f"📝 Campo 'message' encontrado, tipo: {type(msg).__name__}")
                            if isinstance(msg, str):
                                agent_message = msg
                                extracted = True
                                logger.info(f"✅ Mensagem extraída (string): {msg[:100]}...")
                            elif isinstance(msg, dict):
                                logger.info(f"   Keys do message: {list(msg.keys())}")
                                if "content" in msg:
                                    content = msg["content"]
                                    if isinstance(content, str):
                                        agent_message = content
                                        extracted = True
                                        logger.info(f"✅ Mensagem extraída de message.content (string)")
                                    elif isinstance(content, list):
                                        for item in content:
                                            if isinstance(item, dict) and "text" in item:
                                                agent_message += item["text"]
                                                extracted = True
                                        if extracted:
                                            logger.info(f"✅ Mensagem extraída de message.content (list)")
                        
                        # Campo 'content' direto
                        if "content" in event_data and not extracted:
                            content = event_data["content"]
                            logger.info(f"📝 Campo 'content' encontrado, tipo: {type(content).__name__}")
                            if isinstance(content, str):
                                agent_message = content
                                extracted = True
                                logger.info(f"✅ Mensagem extraída de content (string)")
                            elif isinstance(content, list):
                                for item in content:
                                    if isinstance(item, dict) and "text" in item:
                                        agent_message += item["text"]
                                        extracted = True
                                if extracted:
                                    logger.info(f"✅ Mensagem extraída de content (list)")
                        
                        # Campo 'delta'
                        if "delta" in event_data:
                            delta = event_data["delta"]
                            logger.info(f"📝 Campo 'delta' encontrado, tipo: {type(delta).__name__}")
                            if isinstance(delta, str):
                                agent_message += delta
                                extracted = True
                                logger.info(f"✅ Delta adicionado (string)")
                            elif isinstance(delta, dict):
                                if "content" in delta:
                                    if isinstance(delta["content"], list):
                                        for item in delta["content"]:
                                            if isinstance(item, dict) and "text" in item:
                                                agent_message += item["text"]
                                                extracted = True
                                        if extracted:
                                            logger.info(f"✅ Delta adicionado de delta.content (list)")
                        
                        if not extracted and event_type not in ["done", "error"]:
                            logger.warning(f"⚠️ Nenhuma mensagem extraída deste evento. Data completo: {json.dumps(event_data)[:500]}")
                        
                        # Eventos de controle
                        if event_type == "done":
                            logger.info("🏁 Evento 'done' recebido - streaming concluído")
                            done_received = True
                            break
                        
                        elif event_type == "error":
                            error_msg = event_data.get("error", "Erro desconhecido")
                            logger.error(f"❌ Erro no streaming: {error_msg}")
                            raise Exception(f"Erro do agente: {error_msg}")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Linha não é JSON válido: {e}")
                
                logger.info(f"🔚 Loop finalizado. Linhas processadas: {line_count}")
                logger.info(f"   Done received: {done_received}")
                logger.info(f"   Message length: {len(agent_message)}")
                        
            except Exception as e:
                logger.error(f"💥 Erro no loop de streaming: {e}", exc_info=True)
            finally:
                response.close()
            
            if not done_received:
                logger.warning("⚠️ Streaming finalizado sem receber evento 'done'")
            
            if not agent_message:
                logger.error("❌ CRÍTICO: Nenhuma mensagem capturada do streaming!")
                logger.error(f"   Done received: {done_received}")
                logger.error(f"   Thread ID: {thread_id}")
                logger.error(f"   Linhas processadas: {line_count}")
                agent_message = "Desculpe, não recebi resposta do agente."
            else:
                logger.info(f"✅ Mensagem capturada com sucesso!")
                logger.info(f"   Tamanho: {len(agent_message)} caracteres")
                logger.info(f"   Thread ID: {thread_id}")
                logger.info(f"   Resposta: {agent_message[:200]}...")
            
            return {
                "session_id": thread_id,
                "message": agent_message,
                "metadata": {},
                "timestamp": datetime.now().isoformat()
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