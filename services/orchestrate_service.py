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
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=120,  # 2 minutos para acomodar cold start do serverless
                stream=True
            )
            
            logger.info(f"Status da resposta: {response.status_code}")
            response.raise_for_status()
            
            # Processar resposta em streaming (JSON lines)
            agent_message = ""
            thread_id = session_id
            done_received = False
            last_data_time = time.time()
            idle_timeout = 150  # 2.5 minutos para acomodar cold start completo do serverless
            
            logger.info("Iniciando processamento do streaming...")
            
            try:
                for line in response.iter_lines(decode_unicode=True, chunk_size=1):
                    # Verificar timeout de inatividade
                    if time.time() - last_data_time > idle_timeout:
                        logger.warning(f"Timeout de inatividade ({idle_timeout}s) - finalizando streaming")
                        break
                    
                    if not line:
                        continue
                    
                    last_data_time = time.time()  # Resetar timer
                        
                    try:
                        data = json.loads(line)
                        event_type = data.get("event")
                        event_data = data.get("data", {})
                        
                        logger.info(f"Evento recebido: {event_type}")
                        
                        # Extrair thread_id
                        if "thread_id" in event_data:
                            thread_id = event_data["thread_id"]
                        
                        # Processar eventos
                        if event_type == "message.delta":
                            # Acumular deltas de mensagem
                            delta = event_data.get("delta", "")
                            # Delta pode ser string ou dict com estrutura complexa
                            if isinstance(delta, str):
                                agent_message += delta
                            elif isinstance(delta, dict):
                                # Extrair texto de estrutura: {'role': 'assistant', 'content': [{'text': '...'}]}
                                if "content" in delta and isinstance(delta["content"], list) and len(delta["content"]) > 0:
                                    content_item = delta["content"][0]
                                    if "text" in content_item:
                                        agent_message += content_item["text"]
                        
                        elif event_type == "message.complete" or event_type == "answer":
                            # Mensagem completa recebida
                            logger.info(f"Evento '{event_type}' recebido - extraindo mensagem completa")
                            
                            # Tentar extrair mensagem de diferentes estruturas
                            if "message" in event_data:
                                msg = event_data["message"]
                                if isinstance(msg, str):
                                    agent_message = msg
                                elif isinstance(msg, dict):
                                    if "content" in msg:
                                        if isinstance(msg["content"], str):
                                            agent_message = msg["content"]
                                        elif isinstance(msg["content"], list) and len(msg["content"]) > 0:
                                            content_item = msg["content"][0]
                                            if isinstance(content_item, dict) and "text" in content_item:
                                                agent_message = content_item["text"]
                            
                            # Também verificar em 'content' direto
                            elif "content" in event_data:
                                content = event_data["content"]
                                if isinstance(content, str):
                                    agent_message = content
                                elif isinstance(content, list) and len(content) > 0:
                                    if isinstance(content[0], dict) and "text" in content[0]:
                                        agent_message = content[0]["text"]
                            
                            logger.info(f"Mensagem extraída: {agent_message[:100]}...")
                        
                        elif event_type == "done":
                            # Fim do streaming - verificar se há mensagem no evento done
                            logger.info("Evento 'done' recebido")
                            
                            # Às vezes a mensagem vem no evento done
                            if "message" in event_data and not agent_message:
                                msg = event_data["message"]
                                if isinstance(msg, str):
                                    agent_message = msg
                                elif isinstance(msg, dict) and "content" in msg:
                                    if isinstance(msg["content"], str):
                                        agent_message = msg["content"]
                                    elif isinstance(msg["content"], list) and len(msg["content"]) > 0:
                                        content_item = msg["content"][0]
                                        if isinstance(content_item, dict) and "text" in content_item:
                                            agent_message = content_item["text"]
                            
                            done_received = True
                            logger.info("Streaming concluído")
                            break
                        
                        elif event_type == "error":
                            # Erro no streaming
                            error_msg = event_data.get("error", "Erro desconhecido")
                            logger.error(f"Erro no streaming: {error_msg}")
                            raise Exception(f"Erro do agente: {error_msg}")
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Erro ao decodificar JSON: {e}, linha: {line[:100] if line else 'vazia'}")
                    except Exception as e:
                        logger.error(f"Erro ao processar linha do streaming: {e}")
                        
            except Exception as e:
                logger.error(f"Erro no loop de streaming: {e}")
            finally:
                response.close()
            
            if not done_received:
                logger.warning("Streaming finalizado sem receber evento 'done'")
            
            if not agent_message:
                logger.warning("Nenhuma mensagem recebida do streaming")
                agent_message = "Desculpe, não recebi resposta do agente."
            
            logger.info(f"Mensagem recebida com sucesso. Thread ID: {thread_id}")
            logger.info(f"Resposta: {agent_message[:100]}...")
            
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
        # A API cria automaticamente um thread_id na primeira mensagem
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