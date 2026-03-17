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
            # Observado: até 152s em produção, então usamos 240s (4 minutos) com margem
            # timeout=(connect_timeout, read_timeout) - read_timeout se aplica a cada chunk
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=(30, 240),  # (30s connect, 240s read) - 4 minutos para cada chunk do streaming
                stream=True  # Streaming para processar linha por linha
            )
            
            # Timestamp 3: Após receber resposta HTTP
            t3_after_http = time.time()
            
            logger.info(f"Status da resposta: {response.status_code}")
            response.raise_for_status()
            
            # Processar resposta em streaming (linha por linha)
            agent_message = ""
            thread_id = session_id
            
            logger.info("🚀 Processando resposta em streaming...")
            
            try:
                # Processar cada linha do streaming
                line_count = 0
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    line_str = line.decode('utf-8').strip()
                    if not line_str:
                        continue
                    
                    line_count += 1
                    
                    try:
                        # Parse JSON de cada linha
                        event_data = json.loads(line_str)
                        event_type = event_data.get("event", "")
                        data = event_data.get("data", {})
                        
                        # Log apenas eventos importantes (não todos os deltas)
                        if event_type not in ["message.delta"]:
                            logger.info(f"📦 Event: '{event_type}', data_keys={list(data.keys())}")
                        
                        # Extrair thread_id se disponível
                        if "thread_id" in data and not thread_id:
                            thread_id = data["thread_id"]
                            logger.info(f"🔗 Thread ID: {thread_id}")
                        
                        # Processar eventos de mensagem
                        if event_type == "message.delta":
                            # Acumular deltas da mensagem (formato: data.delta.content[].text)
                            if "delta" in data:
                                delta = data["delta"]
                                if isinstance(delta, dict) and "content" in delta:
                                    content = delta["content"]
                                    if isinstance(content, list):
                                        for item in content:
                                            if isinstance(item, dict) and "text" in item:
                                                agent_message += item["text"]
                                    elif isinstance(content, str):
                                        agent_message += content
                        
                        elif event_type == "message.created":
                            # Mensagem completa criada (formato: data.message.content[].text)
                            if "message" in data:
                                msg = data["message"]
                                if isinstance(msg, dict) and "content" in msg:
                                    content = msg["content"]
                                    if isinstance(content, list):
                                        # Limpar mensagem anterior e usar a versão completa
                                        agent_message = ""
                                        for item in content:
                                            if isinstance(item, dict) and "text" in item:
                                                agent_message += item["text"]
                                    elif isinstance(content, str):
                                        agent_message = content
                            logger.info(f"✅ Mensagem completa recebida (len={len(agent_message)})")
                        
                        elif event_type == "done":
                            logger.info("✅ Streaming concluído")
                            break
                            
                    except json.JSONDecodeError:
                        # Linha não é JSON válido, ignorar silenciosamente
                        continue
                        
            except Exception as e:
                logger.error(f"💥 Erro ao processar streaming: {e}", exc_info=True)
            
            if not agent_message:
                logger.error("❌ CRÍTICO: Nenhuma mensagem capturada da resposta!")
                logger.error(f"   Thread ID: {thread_id}")
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