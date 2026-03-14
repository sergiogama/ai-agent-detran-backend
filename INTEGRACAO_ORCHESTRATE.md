# Integração com IBM Watsonx Orchestrate

Este documento descreve como funciona a integração do chat do Detran com o IBM Watsonx Orchestrate.

## Visão Geral

O sistema utiliza o Watsonx Orchestrate para processar mensagens dos usuários e fornecer respostas contextualizadas sobre multas, CNH e legislação de trânsito. A integração é feita através de dois serviços principais:

1. **OrchestrateService** (`orchestrate_service.py`): Gerencia a comunicação com a API do Watsonx Orchestrate
2. **ChatService** (`chat_service.py`): Gerencia as conversas e coordena com o OrchestrateService

## Arquitetura

```
Frontend (Chat UI)
    ↓
API Routes (chat_routes.py)
    ↓
ChatService (chat_service.py)
    ↓
OrchestrateService (orchestrate_service.py)
    ↓
IBM Watsonx Orchestrate API
```

## Configuração Necessária

### Variáveis de Ambiente (.env)

```bash
# IBM Watsonx Orchestrate
ORCHESTRATE_AGENT_ID=019baa2f-38cd-4b32-a81c-420677ad72eb
ORCHESTRATE_API_URL=https://api.us-south.watson-orchestrate.cloud.ibm.com/instances/09455c86-884f-4d7c-a18d-755bee57b558
ORCHESTRATE_API_KEY=<sua-api-key-ibm-cloud>
```

### Requisitos

- **API Key IBM Cloud**: Necessária para autenticação IAM
- **Agent ID**: ID do agente configurado no Watsonx Orchestrate
- **Instance URL**: URL da instância do Watsonx Orchestrate

## OrchestrateService

### Responsabilidades

1. **Autenticação IAM**: Obtém e renova tokens de acesso automaticamente
2. **Comunicação com API**: Envia mensagens e recebe respostas via streaming
3. **Parsing de Respostas**: Extrai o texto das respostas em formato streaming

### Fluxo de Autenticação

```python
# 1. Obter token IAM usando API Key
POST https://iam.cloud.ibm.com/identity/token
Body: {
    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
    "apikey": "<API_KEY>"
}

# 2. Usar token nas requisições
Headers: {
    "Authorization": "Bearer <access_token>"
}
```

**Características:**
- Token válido por 1 hora
- Renovação automática 5 minutos antes de expirar
- Cache do token em memória

### Envio de Mensagens

#### Endpoint
```
POST /v1/orchestrate/runs?stream=true
```

#### Payload
```json
{
    "agent_id": "019baa2f-38cd-4b32-a81c-420677ad72eb",
    "message": {
        "role": "user",
        "content": [
            {
                "response_type": "text",
                "text": "[Usuário CPF: 123.456.789-00] Tenho multas pendentes?"
            }
        ]
    },
    "thread_id": "uuid-da-conversa"  // Opcional, para manter contexto
}
```

**Observações:**
- `agent_id`: Obrigatório para identificar qual agente usar
- `thread_id`: Opcional na primeira mensagem, obrigatório para manter contexto
- CPF do usuário incluído na mensagem para contexto

### Resposta em Streaming

A API retorna eventos em formato JSON Lines (um JSON por linha):

```json
{"id": "...", "event": "run.started", "data": {...}}
{"id": "...", "event": "message.started", "data": {...}}
{"id": "...", "event": "message.delta", "data": {"delta": {"role": "assistant", "content": [{"text": "Olá"}]}}}
{"id": "...", "event": "message.delta", "data": {"delta": {"role": "assistant", "content": [{"text": ", "}]}}}
{"id": "...", "event": "message.delta", "data": {"delta": {"role": "assistant", "content": [{"text": "Lucas"}]}}}
...
{"id": "...", "event": "message.completed", "data": {...}}
{"id": "...", "event": "done", "data": {"thread_id": "..."}}
```

#### Eventos Importantes

1. **run.started**: Início do processamento
2. **message.started**: Início da resposta
3. **message.delta**: Fragmento de texto da resposta
   - Estrutura: `{"delta": {"role": "assistant", "content": [{"text": "fragmento"}]}}`
4. **message.completed**: Resposta completa
5. **done**: Fim do streaming, contém `thread_id` para próximas mensagens

### Código de Parsing

```python
for line in response.iter_lines():
    if line:
        data = json.loads(line.decode('utf-8'))
        event_type = data.get("event")
        event_data = data.get("data", {})
        
        if event_type == "message.delta":
            delta = event_data.get("delta", "")
            if isinstance(delta, dict):
                # Extrair texto de: {'role': 'assistant', 'content': [{'text': '...'}]}
                if "content" in delta and len(delta["content"]) > 0:
                    text = delta["content"][0].get("text", "")
                    agent_message += text
        
        elif event_type == "done":
            thread_id = event_data.get("thread_id")
            break
```

## ChatService

### Responsabilidades

1. **Gerenciamento de Conversas**: Cria e mantém conversas em memória
2. **Histórico de Mensagens**: Armazena mensagens do usuário e do agente
3. **Coordenação**: Integra com OrchestrateService e gerencia thread_id

### Estrutura de Conversa

```python
conversations = {
    "conversation_id": {
        "id": "uuid",
        "user_cpf": "123.456.789-00",
        "orchestrate_thread_id": "thread-uuid",  # ID do Orchestrate
        "messages": [
            {
                "role": "user",
                "content": "Tenho multas?",
                "timestamp": "2024-01-15T10:30:00"
            },
            {
                "role": "assistant",
                "content": "Sim, você tem 1 multa...",
                "timestamp": "2024-01-15T10:30:05"
            }
        ],
        "created_at": "2024-01-15T10:30:00"
    }
}
```

### Fluxo de Mensagem

```python
def send_message(message, conversation_id=None, user_cpf=None):
    # 1. Criar conversa se não existir
    if not conversation_id:
        conversation_id = create_conversation(user_cpf)
    
    # 2. Adicionar mensagem do usuário ao histórico
    conversations[conversation_id]["messages"].append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })
    
    # 3. Obter ou criar thread_id do Orchestrate
    orchestrate_thread_id = conversations[conversation_id].get("orchestrate_thread_id")
    
    # 4. Enviar para Orchestrate com contexto
    context = {"user_cpf": user_cpf}
    response = orchestrate_service.send_message(
        message=message,
        session_id=orchestrate_thread_id,
        context=context
    )
    
    # 5. Salvar thread_id retornado
    if response.get("session_id"):
        conversations[conversation_id]["orchestrate_thread_id"] = response["session_id"]
    
    # 6. Adicionar resposta do agente ao histórico
    conversations[conversation_id]["messages"].append({
        "role": "assistant",
        "content": response["message"],
        "timestamp": response["timestamp"]
    })
    
    return response
```

## Fluxo Completo de uma Mensagem

### 1. Usuário Envia Mensagem

```
POST /api/chat/message
Headers: Authorization: Bearer <jwt-token>
Body: {
    "message": "Tenho multas pendentes?",
    "conversation_id": null  // Primeira mensagem
}
```

### 2. Autenticação e Extração de CPF

```python
# chat_routes.py
user = get_current_user(authorization)  # Valida JWT
user_cpf = user.get("cpf")  # Extrai CPF do token
```

### 3. ChatService Processa

```python
# chat_service.py
conversation_id = create_conversation(user_cpf)  # Nova conversa
orchestrate_thread_id = None  # Primeira mensagem
```

### 4. OrchestrateService Envia para API

```python
# orchestrate_service.py
# 4.1. Obter token IAM
token = _get_iam_token()

# 4.2. Preparar payload
payload = {
    "agent_id": "019baa2f-38cd-4b32-a81c-420677ad72eb",
    "message": {
        "role": "user",
        "content": [{
            "response_type": "text",
            "text": "[Usuário CPF: 123.456.789-00] Tenho multas pendentes?"
        }]
    }
}

# 4.3. Enviar com streaming
response = requests.post(
    f"{api_url}/v1/orchestrate/runs?stream=true",
    json=payload,
    headers={"Authorization": f"Bearer {token}"},
    stream=True
)
```

### 5. Processar Streaming

```python
agent_message = ""
thread_id = None

for line in response.iter_lines():
    data = json.loads(line)
    
    if data["event"] == "message.delta":
        # Acumular fragmentos de texto
        text = extract_text_from_delta(data["data"]["delta"])
        agent_message += text
    
    elif data["event"] == "done":
        # Obter thread_id para próximas mensagens
        thread_id = data["data"]["thread_id"]
        break
```

### 6. Retornar Resposta

```python
return {
    "conversation_id": conversation_id,
    "message": agent_message,  # Texto completo da resposta
    "timestamp": datetime.now().isoformat()
}
```

### 7. Frontend Exibe

```javascript
// Resposta recebida
{
    "conversation_id": "uuid",
    "message": "Olá, Lucas! Sim, você tem 1 multa pendente...",
    "timestamp": "2024-01-15T10:30:05"
}
```

## Mensagens Subsequentes

Para manter o contexto da conversa:

```python
# Segunda mensagem do usuário
POST /api/chat/message
Body: {
    "message": "Qual o valor total?",
    "conversation_id": "uuid-da-conversa-anterior"
}

# ChatService usa o thread_id salvo
orchestrate_thread_id = conversations[conversation_id]["orchestrate_thread_id"]

# OrchestrateService envia com thread_id
payload = {
    "agent_id": "...",
    "thread_id": orchestrate_thread_id,  # Mantém contexto
    "message": {...}
}
```

## Tratamento de Erros

### Erro de Autenticação (401)
```python
# Token IAM expirado ou inválido
# Solução: Renovar token automaticamente
if response.status_code == 401:
    self.access_token = None  # Forçar renovação
    token = self._get_iam_token()
```

### Erro de Validação (422)
```python
# Payload inválido
# Verificar: agent_id, estrutura da mensagem, thread_id
```

### Timeout
```python
# Streaming muito longo
# Configurar timeout adequado (60s)
response = requests.post(..., timeout=60, stream=True)
```

## Boas Práticas

1. **Sempre incluir agent_id**: Obrigatório para identificar o agente
2. **Manter thread_id**: Essencial para contexto entre mensagens
3. **Incluir CPF na mensagem**: Permite ao agente consultar dados do usuário
4. **Processar streaming corretamente**: Acumular deltas para texto completo
5. **Renovar token IAM**: Implementar cache e renovação automática
6. **Tratar erros gracefully**: Retornar mensagens amigáveis ao usuário

## Debugging

### Logs Importantes

```python
# OrchestrateService
logger.info(f"Token IAM obtido com sucesso")
logger.info(f"Enviando mensagem para Orchestrate: {message[:50]}...")
logger.info(f"Agent ID: {self.agent_id}")
logger.info(f"Status da resposta: {response.status_code}")
logger.info(f"Streaming concluído")
logger.info(f"Thread ID: {thread_id}")

# ChatService
logger.info(f"Nova conversa criada: {conversation_id}")
logger.info(f"Thread ID salvo: {orchestrate_thread_id}")
logger.info(f"Resposta recebida do Orchestrate: {agent_response[:50]}...")
```

### Verificar Integração

```bash
# Ver logs do backend
cd backend && docker-compose logs -f backend

# Testar autenticação IAM
curl -X POST https://iam.cloud.ibm.com/identity/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=<API_KEY>"

# Testar endpoint do Orchestrate
curl -X POST "<ORCHESTRATE_API_URL>/v1/orchestrate/runs?stream=true" \
  -H "Authorization: Bearer <IAM_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"<AGENT_ID>","message":{"role":"user","content":[{"response_type":"text","text":"Olá"}]}}'
```

## Referências

- [IBM Watsonx Orchestrate API Documentation](https://developer.ibm.com/apis/catalog/watsonorchestrate--custom-assistants/)
- [IBM Cloud IAM Authentication](https://cloud.ibm.com/docs/account?topic=account-iamoverview)
- Código fonte: `backend/services/orchestrate_service.py`
- Código fonte: `backend/services/chat_service.py`