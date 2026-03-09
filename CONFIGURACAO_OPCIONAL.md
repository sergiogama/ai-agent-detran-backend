# ⚙️ Configuração Opcional - Backend Detran Agent

## 🎯 Visão Geral

O backend foi projetado para **iniciar sem nenhuma configuração**! Todos os serviços são opcionais e podem ser habilitados conforme necessário.

## 🚀 Como Funciona

### Inicialização Inteligente

1. **Backend inicia sempre** - Mesmo sem variáveis de ambiente
2. **Serviços são opcionais** - Cada serviço verifica suas configurações
3. **Endpoints protegidos** - Retornam erro 503 se o serviço não estiver configurado
4. **Health check informativo** - Mostra status de cada serviço

### Exemplo de Health Check

```bash
curl http://localhost:8080/health
```

**Resposta quando nada está configurado:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "services": {
    "cos": "not_configured",
    "orchestrate": "not_configured",
    "db2": "not_configured"
  }
}
```

**Resposta quando tudo está configurado:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "services": {
    "cos": "connected",
    "orchestrate": "connected",
    "db2": "connected"
  }
}
```

## 📋 Serviços Disponíveis

### 1. IBM Cloud Object Storage (COS)
**Usado para:** Upload de imagens de CNH

**Endpoints afetados:**
- `POST /api/upload` - Upload de imagens

**Variáveis necessárias (TODAS):**
```bash
COS_API_KEY=sua-api-key
COS_INSTANCE_CRN=seu-crn
COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud
COS_BUCKET_NAME=seu-bucket
```

**Comportamento sem configuração:**
- Endpoint retorna erro 503
- Mensagem: "COS Service não está configurado"

---

### 2. IBM Db2 Warehouse on Cloud
**Usado para:** Consultas ao banco de dados

**Endpoints afetados:**
- `GET /api/db2/health` - Health check do Db2
- `POST /api/db2/query` - Executar queries
- Todos os endpoints em `/api/db2/*`

**Variáveis necessárias (TODAS):**
```bash
DB2_HOSTNAME=seu-hostname.databases.appdomain.cloud
DB2_PORT=32286
DB2_DATABASE=bludb
DB2_USERNAME=seu-username
DB2_PASSWORD=sua-senha
DB2_SECURITY=SSL
DB2_VERIFY_SSL=false
```

**Comportamento sem configuração:**
- Endpoints Db2 podem retornar erro
- Health check mostra "not_configured"

---

### 3. IBM Watsonx Orchestrate
**Usado para:** Chat com agente AI

**Endpoints afetados:**
- `POST /api/session` - Criar sessão de chat
- `POST /api/chat` - Enviar mensagem
- `DELETE /api/session/{id}` - Deletar sessão
- `GET /api/session/{id}/history` - Histórico

**Variáveis necessárias (TODAS):**
```bash
ORCHESTRATE_API_URL=sua-url
ORCHESTRATE_API_KEY=sua-api-key
ORCHESTRATE_AGENT_ID=seu-agent-id
```

**Comportamento sem configuração:**
- Endpoints retornam erro 503
- Mensagem: "Orchestrate Service não está configurado"

---

## 🔧 Configuração Passo a Passo

### Opção 1: Configuração Local (.env)

1. **Copie o template:**
   ```bash
   cp .env.example .env
   ```

2. **Descomente e configure apenas o que você precisa:**
   ```bash
   # Para usar Db2, descomente estas linhas:
   DB2_HOSTNAME=seu-hostname.databases.appdomain.cloud
   DB2_PORT=32286
   DB2_DATABASE=bludb
   DB2_USERNAME=seu-username
   DB2_PASSWORD=sua-senha
   DB2_SECURITY=SSL
   DB2_VERIFY_SSL=false
   ```

3. **Inicie o backend:**
   ```bash
   python main.py
   ```

### Opção 2: Configuração no Code Engine

1. **Deploy básico (sem configuração):**
   ```bash
   ibmcloud ce application create \
     --name ai-agent-detran \
     --build-source https://github.com/seu-usuario/detran-backend.git \
     --port 8080
   ```

2. **Adicione serviços conforme necessário:**
   ```bash
   # Habilitar Db2
   ibmcloud ce application update --name ai-agent-detran \
     --env DB2_HOSTNAME=seu-hostname \
     --env DB2_PORT=32286 \
     --env DB2_DATABASE=bludb \
     --env DB2_USERNAME=seu-username \
     --env DB2_PASSWORD=sua-senha \
     --env DB2_SECURITY=SSL \
     --env DB2_VERIFY_SSL=false
   ```

## ✅ Verificação

### 1. Verificar quais serviços estão ativos:
```bash
curl http://localhost:8080/health
```

### 2. Testar serviço específico:

**COS:**
```bash
curl -X POST http://localhost:8080/api/upload \
  -F "file=@imagem.jpg"
```

**Db2:**
```bash
curl http://localhost:8080/api/db2/health
```

**Orchestrate:**
```bash
curl -X POST http://localhost:8080/api/session
```

### 3. Interpretar erros:

**Erro 503 - Service Unavailable:**
- O serviço não está configurado
- Configure as variáveis de ambiente necessárias

**Erro 500 - Internal Server Error:**
- O serviço está configurado mas há erro de conexão
- Verifique credenciais e conectividade

## 🎓 Exemplos de Uso

### Cenário 1: Desenvolvimento Local (apenas Db2)
```bash
# .env
DB2_HOSTNAME=localhost
DB2_PORT=50000
DB2_DATABASE=testdb
DB2_USERNAME=db2inst1
DB2_PASSWORD=password
DB2_SECURITY=SSL
DB2_VERIFY_SSL=false

# Outros serviços ficam comentados
# COS_API_KEY=...
# ORCHESTRATE_API_URL=...
```

### Cenário 2: Staging (Db2 + COS)
```bash
# .env
DB2_HOSTNAME=staging-db.cloud.ibm.com
DB2_PORT=32286
DB2_DATABASE=bludb
DB2_USERNAME=staging_user
DB2_PASSWORD=staging_pass
DB2_SECURITY=SSL
DB2_VERIFY_SSL=false

COS_API_KEY=staging-key
COS_INSTANCE_CRN=staging-crn
COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud
COS_BUCKET_NAME=staging-bucket

# Orchestrate não configurado
# ORCHESTRATE_API_URL=...
```

### Cenário 3: Produção (Todos os serviços)
```bash
# Configure todas as variáveis
DB2_HOSTNAME=prod-db.cloud.ibm.com
# ... todas as variáveis Db2

COS_API_KEY=prod-key
# ... todas as variáveis COS

ORCHESTRATE_API_URL=https://prod.watsonx-orchestrate.ibm.com
# ... todas as variáveis Orchestrate
```

## 🔍 Logs e Debugging

### Logs de Inicialização

**Serviço configurado com sucesso:**
```
INFO - COS Service inicializado com sucesso
INFO - Orchestrate Service inicializado com sucesso
INFO - Db2 REST Service inicializado com sucesso
```

**Serviço não configurado:**
```
WARNING - COS Service não configurado - variáveis de ambiente ausentes
WARNING - Orchestrate Service não configurado - variáveis de ambiente ausentes
WARNING - Db2 REST Service não configurado - variáveis de ambiente ausentes
```

**Erro na inicialização:**
```
WARNING - Não foi possível inicializar COS Service: [erro detalhado]
```

## 📚 Referências

- [.env.example](/.env.example) - Template de configuração
- [DEPLOY.md](/DEPLOY.md) - Guia de deploy no Code Engine
- [README.md](/README.md) - Documentação geral