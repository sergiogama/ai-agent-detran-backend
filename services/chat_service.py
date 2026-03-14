"""
Serviço de Chat
Gerencia interações com o agente Detran via watsonx Orchestrate
"""

import logging
import uuid
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Armazenamento em memória das conversas (em produção, usar banco de dados)
conversations = {}


class ChatService:
    """Serviço de chat com o agente Detran"""

    def __init__(self, orchestrate_service=None):
        """
        Inicializa o serviço de chat
        
        Args:
            orchestrate_service: Instância do OrchestrateService (opcional)
        """
        self.orchestrate_service = orchestrate_service
        if orchestrate_service:
            logger.info("ChatService inicializado com OrchestrateService")
        else:
            logger.warning("ChatService inicializado sem OrchestrateService - usando respostas simuladas")

    def create_conversation(self, user_cpf: str) -> str:
        """
        Cria uma nova conversa

        Args:
            user_cpf: CPF do usuário

        Returns:
            ID da conversa
        """
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = {
            "id": conversation_id,
            "user_cpf": user_cpf,
            "messages": [],
            "created_at": datetime.now().isoformat(),
        }
        logger.info(f"Nova conversa criada: {conversation_id} para usuário {user_cpf}")
        return conversation_id

    def send_message(
        self, message: str, conversation_id: Optional[str] = None, user_cpf: Optional[str] = None
    ) -> Dict:
        """
        Envia uma mensagem para o agente

        Args:
            message: Mensagem do usuário
            conversation_id: ID da conversa (opcional, cria nova se não fornecido)
            user_cpf: CPF do usuário (necessário se criar nova conversa)

        Returns:
            Resposta do agente com ID da conversa
        """
        try:
            # Cria nova conversa se necessário
            if not conversation_id:
                if not user_cpf:
                    raise ValueError("user_cpf é necessário para nova conversa")
                conversation_id = self.create_conversation(user_cpf)

            # Verifica se conversa existe
            if conversation_id not in conversations:
                raise ValueError(f"Conversa não encontrada: {conversation_id}")

            # Adiciona mensagem do usuário ao histórico
            user_message = {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            }
            conversations[conversation_id]["messages"].append(user_message)

            # Enviar mensagem para o agente via watsonx Orchestrate
            if self.orchestrate_service:
                try:
                    logger.info(f"Enviando mensagem para Orchestrate: {message[:50]}...")
                    
                    # Obter ou criar thread_id do Orchestrate
                    orchestrate_thread_id = conversations[conversation_id].get("orchestrate_thread_id")
                    
                    # Adicionar contexto do usuário
                    context = {
                        "user_cpf": user_cpf or conversations[conversation_id]["user_cpf"],
                        "conversation_id": conversation_id
                    }
                    
                    orchestrate_response = self.orchestrate_service.send_message(
                        message=message,
                        session_id=orchestrate_thread_id,
                        context=context
                    )
                    
                    # Salvar thread_id retornado pelo Orchestrate
                    if orchestrate_response.get("session_id"):
                        conversations[conversation_id]["orchestrate_thread_id"] = orchestrate_response["session_id"]
                        logger.info(f"Thread ID salvo: {orchestrate_response['session_id']}")
                    
                    agent_response = orchestrate_response.get("message", "Desculpe, não consegui processar sua mensagem.")
                    logger.info(f"Resposta recebida do Orchestrate: {agent_response[:50]}...")
                    
                except Exception as e:
                    logger.error(f"Erro ao chamar Orchestrate: {str(e)}")
                    agent_response = f"Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
            else:
                # Fallback para resposta simulada se Orchestrate não disponível
                logger.warning("Orchestrate não disponível, usando resposta simulada")
                agent_response = self._simulate_agent_response(message)

            # Adiciona resposta do agente ao histórico
            assistant_message = {
                "role": "assistant",
                "content": agent_response,
                "timestamp": datetime.now().isoformat(),
            }
            conversations[conversation_id]["messages"].append(assistant_message)

            logger.info(
                f"Mensagem processada na conversa {conversation_id}: {len(message)} chars"
            )

            return {
                "conversation_id": conversation_id,
                "message": agent_response,
                "timestamp": assistant_message["timestamp"],
            }

        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {str(e)}")
            raise

    def get_conversation_history(self, conversation_id: str) -> List[Dict]:
        """
        Obtém histórico de uma conversa

        Args:
            conversation_id: ID da conversa

        Returns:
            Lista de mensagens da conversa
        """
        if conversation_id not in conversations:
            raise ValueError(f"Conversa não encontrada: {conversation_id}")

        return conversations[conversation_id]["messages"]

    def _simulate_agent_response(self, message: str) -> str:
        """
        Simula resposta do agente (temporário até integração real)

        Args:
            message: Mensagem do usuário

        Returns:
            Resposta simulada
        """
        message_lower = message.lower()

        # Respostas simuladas baseadas em palavras-chave
        if "multa" in message_lower:
            return (
                "Para consultar suas multas, preciso do seu CPF. "
                "Você pode me fornecer seu CPF para que eu possa buscar suas multas?"
            )
        elif "cnh" in message_lower or "carteira" in message_lower:
            return (
                "Posso ajudá-lo com informações sobre sua CNH. "
                "Você gostaria de consultar os pontos na sua carteira ou verificar a situação da sua habilitação?"
            )
        elif "veículo" in message_lower or "carro" in message_lower:
            return (
                "Para consultar informações sobre seu veículo, preciso da placa. "
                "Qual é a placa do veículo que você deseja consultar?"
            )
        elif "legislação" in message_lower or "lei" in message_lower or "ctb" in message_lower:
            return (
                "📚 Consultando a Base de Conhecimento do CTB...\n\n"
                "Posso ajudá-lo com informações sobre o Código de Trânsito Brasileiro. "
                "Sobre qual assunto específico você gostaria de saber? "
                "(infrações, pontuação, categorias de CNH, etc.)"
            )
        else:
            return (
                "Olá! Sou o assistente virtual do Detran-SP. "
                "Posso ajudá-lo com:\n"
                "• Consulta de multas\n"
                "• Informações sobre CNH\n"
                "• Situação de veículos\n"
                "• Legislação de trânsito\n\n"
                "Como posso ajudá-lo hoje?"
            )