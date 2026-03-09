# 🚀 Guia de Deploy - IBM Code Engine

## 📋 Pré-requisitos

1. Conta IBM Cloud ativa
2. IBM Cloud CLI instalado
3. Code Engine plugin instalado
4. Serviços IBM Cloud configurados:
   - IBM Db2 Warehouse on Cloud
   - IBM Cloud Object Storage
   - IBM Watsonx Orchestrate

## 🔧 Preparação

### 1. Instalar IBM Cloud CLI

```bash
# Mac
curl -fsSL https://clis.cloud.ibm.com/install/osx | sh

# Linux
curl -fsSL https://clis.cloud.ibm.com/install/linux | sh

# Windows
# Baixe de: https://cloud.ibm.com/docs/cli
```

### 2. Instalar Code Engine Plugin

```bash
ibmcloud plugin install code-engine
```

### 3. Login no IBM Cloud

```bash
# Login com SSO
ibmcloud login --sso

# Se você tem múltiplas contas, liste-as
ibmcloud account list

# Selecione a conta específica (substitua ACCOUNT_ID pelo ID da sua conta)
ibmcloud target -c 2947177 # ou 1a9b6695641d440ab608e91ee889281f ou itz-watsonx-028

# Ou selecione por nome da conta
ibmcloud target -c "itz-watsonx-028"

# Depois, selecione região e resource group
ibmcloud target -r us-south -g Default

# Verificar configuração atual
ibmcloud target
```

**Exemplo com múltiplas contas:**
```bash
# 1. Login
ibmcloud login --sso

# 2. Listar contas disponíveis
ibmcloud account list
# Output:
# Account GUID                          Name                    State
# abc123...                             Minha Conta Pessoal     ACTIVE
# def456...                             Empresa XYZ             ACTIVE

# 3. Selecionar conta específica
ibmcloud target -c abc123...

# 4. Selecionar região e resource group
ibmcloud target -r us-south -g Default
```

## 📦 Deploy via GitHub

### Opção 1: Deploy Automático (Recomendado)

1. **Faça push do código para GitHub:**
   ```bash
   cd backend
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/seu-usuario/detran-backend.git
   git push -u origin main
   ```

2. **Crie o projeto no Code Engine:**
   ```bash
   ibmcloud ce project create --name ai-agent-detran
   ibmcloud ce project select --name ai-agent-detran
   ```

3. **Deploy MÍNIMO (sem variáveis de ambiente):**
   
   O backend agora inicia mesmo sem configuração! Você pode fazer deploy básico e configurar depois:
   
   ```bash
   ibmcloud ce application create \
     --name ai-agent-detran \
     --build-source https://github.com/seu-usuario/detran-backend.git \
     --port 8080 \
     --min-scale 1 \
     --max-scale 5 \
     --cpu 1 \
     --memory 2G \
     --build-commit main \
     --build-context-dir . \
     --build-dockerfile Dockerfile
   ```

4. **Configurar variáveis de ambiente (OPCIONAL):**
   
   Configure apenas os serviços que você precisa usar. Cada grupo de variáveis habilita um serviço específico:

   **Para habilitar Db2 (consultas ao banco):**
   ```bash
   ibmcloud ce application update --name ai-agent-detran \
     --env DB2_HOSTNAME=seu-hostname.databases.appdomain.cloud \
     --env DB2_PORT=32286 \
     --env DB2_DATABASE=bludb \
     --env DB2_USERNAME=seu-username \
     --env DB2_PASSWORD=sua-senha \
     --env DB2_SECURITY=SSL \
     --env DB2_VERIFY_SSL=false
   ```

   **Para habilitar COS (upload de imagens):**
   ```bash
   ibmcloud ce application update --name ai-agent-detran \
     --env COS_API_KEY=sua-api-key \
     --env COS_INSTANCE_CRN=seu-crn \
     --env COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud \
     --env COS_BUCKET_NAME=seu-bucket
   ```

   **Para habilitar Watsonx Orchestrate (chat com agente):**
   ```bash
   ibmcloud ce application update --name ai-agent-detran \
     --env ORCHESTRATE_API_URL=sua-url \
     --env ORCHESTRATE_API_KEY=sua-api-key \
     --env ORCHESTRATE_AGENT_ID=seu-agent-id
   ```

5. **Deploy COMPLETO (com todas as variáveis):**
   
   Se você já tem todas as credenciais, pode configurar tudo de uma vez:
   
   ```bash
   ibmcloud ce application create \
     --name ai-agent-detran \
     --build-source https://github.com/seu-usuario/detran-backend.git \
     --port 8080 \
     --min-scale 1 \
     --max-scale 5 \
     --cpu 1 \
     --memory 2G \
     --build-commit main \
     --build-context-dir . \
     --build-dockerfile Dockerfile \
     --env DB2_HOSTNAME=seu-hostname.databases.appdomain.cloud \
     --env DB2_PORT=32286 \
     --env DB2_DATABASE=bludb \
     --env DB2_USERNAME=seu-username \
     --env DB2_PASSWORD=sua-senha \
     --env DB2_SECURITY=SSL \
     --env DB2_VERIFY_SSL=false \
     --env COS_API_KEY=sua-api-key \
     --env COS_INSTANCE_CRN=seu-crn \
     --env COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud \
     --env COS_BUCKET_NAME=seu-bucket \
     --env ORCHESTRATE_API_URL=sua-url \
     --env ORCHESTRATE_API_KEY=sua-api-key \
     --env ORCHESTRATE_AGENT_ID=seu-agent-id
   ```

### Opção 2: Deploy via Container Registry

1. **Build e push da imagem:**
   ```bash
   # Login no IBM Container Registry
   ibmcloud cr login
   
   # Criar namespace (se não existir)
   ibmcloud cr namespace-add detran
   
   # Build da imagem
   docker build -t us.icr.io/detran/detran-api:latest .
   
   # Push da imagem
   docker push us.icr.io/detran/detran-api:latest
   ```

2. **Deploy da imagem:**
   ```bash
   ibmcloud ce application create \
     --name detran-api \
     --image us.icr.io/detran/detran-api:latest \
     --port 8080 \
     --min-scale 1 \
     --max-scale 5 \
     --cpu 1 \
     --memory 2G \
     --env-from-configmap detran-config \
     --env-from-secret detran-secrets \
     --registry-secret icr-secret
   ```

## 🌐 Deploy via Console Web

1. Acesse: https://cloud.ibm.com/codeengine
2. Crie um novo projeto ou selecione existente
3. Clique em "Create" → "Application"
4. Configure:
   - **Name:** detran-api
   - **Code:** Selecione seu repositório GitHub
   - **Branch:** main
   - **Context directory:** backend
   - **Dockerfile:** Dockerfile
5. Configure recursos:
   - **CPU:** 1 vCPU
   - **Memory:** 2 GB
   - **Min instances:** 1
   - **Max instances:** 5
   - **Port:** 8080
6. Adicione variáveis de ambiente (use secrets para senhas)
7. Clique em "Create"

## ✅ Verificação

### 1. Obter URL da aplicação:
```bash
ibmcloud ce application get --name ai-agent-detran
```

### 2. Testar health check:
```bash
curl https://ai-agent-detran.xxx.us-south.codeengine.appdomain.cloud/health
```

**Resposta esperada:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "services": {
    "cos": "connected",           // ou "not_configured"
    "orchestrate": "connected",   // ou "not_configured"
    "db2": "connected"            // ou "not_configured"
  }
}
```

### 3. Testar API Db2 (se configurado):
```bash
curl https://ai-agent-detran.xxx.us-south.codeengine.appdomain.cloud/api/db2/health
```

### 4. Ver logs:
```bash
ibmcloud ce application logs --name ai-agent-detran
```

**O que procurar nos logs:**
- ✅ `COS Service inicializado com sucesso` - COS configurado
- ✅ `Orchestrate Service inicializado com sucesso` - Orchestrate configurado
- ✅ `Db2 REST Service inicializado com sucesso` - Db2 configurado
- ⚠️ `COS Service não configurado` - COS não disponível (normal se não configurado)
- ⚠️ `Orchestrate Service não configurado` - Orchestrate não disponível (normal se não configurado)
- ⚠️ `Db2 REST Service não configurado` - Db2 não disponível (normal se não configurado)

## 🔄 Atualização

### Atualizar código:
```bash
# Commit e push das mudanças
git add .
git commit -m "Update"
git push

# Code Engine fará rebuild automático
```

### Atualizar manualmente:
```bash
ibmcloud ce application update --name ai-agent-detran \
  --image us.icr.io/detran/detran-api:latest
```

### Adicionar/Atualizar variáveis de ambiente:
```bash
# Adicionar uma variável
ibmcloud ce application update --name ai-agent-detran \
  --env NOVA_VAR=valor

# Remover uma variável
ibmcloud ce application update --name ai-agent-detran \
  --env-rm NOME_VAR
```

## 📊 Monitoramento

### Ver status:
```bash
ibmcloud ce application get --name ai-agent-detran
```

### Ver logs em tempo real:
```bash
ibmcloud ce application logs --name ai-agent-detran --follow
```

### Ver métricas:
- Acesse o console: https://cloud.ibm.com/codeengine
- Selecione sua aplicação
- Veja CPU, memória, requests, etc.

## 🔐 Segurança

1. **Nunca commite credenciais**
   - Use secrets do Code Engine
   - Mantenha `.env` no `.gitignore`

2. **Configure CORS adequadamente**
   - Atualize `CORS_ORIGINS` no configmap
   - Adicione apenas domínios confiáveis

3. **Use HTTPS**
   - Code Engine fornece HTTPS automaticamente
   - Configure custom domain se necessário

## 💰 Custos

- **Free tier:** 100.000 vCPU-segundos/mês
- **Após free tier:** ~$0.000024/vCPU-segundo
- **Estimativa:** ~$10-30/mês para uso moderado

## 🆘 Troubleshooting

### Aplicação não inicia:
```bash
# Ver logs detalhados
ibmcloud ce application logs --name ai-agent-detran --tail 100

# Verificar eventos
ibmcloud ce application events --name ai-agent-detran
```

### Erro "AttributeError: 'NoneType' object has no attribute":
- ✅ **RESOLVIDO!** O backend agora inicia sem variáveis de ambiente
- Configure apenas os serviços que você precisa usar
- Verifique o `/health` para ver quais serviços estão disponíveis

### Erro de conexão com Db2:
- Verifique se TODAS as variáveis Db2 estão configuradas
- Confirme que `DB2_VERIFY_SSL=false`
- Teste conexão via console Db2

### Serviço retorna erro 503:
- O serviço não está configurado (variáveis de ambiente ausentes)
- Configure as variáveis necessárias para aquele serviço
- Exemplo: Para usar `/api/upload`, configure todas as variáveis COS

### Timeout:
- Aumente CPU/memória
- Aumente max-scale
- Verifique logs de performance

## 📚 Recursos

- [Code Engine Docs](https://cloud.ibm.com/docs/codeengine)
- [IBM Cloud CLI](https://cloud.ibm.com/docs/cli)
- [Container Registry](https://cloud.ibm.com/docs/Registry)