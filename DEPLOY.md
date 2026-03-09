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

3. **Configure as variáveis de ambiente diretamente no deploy:**
   
   **IMPORTANTE:** Substitua TODOS os valores `sua-*` pelas suas credenciais reais!

5. **Deploy da aplicação com variáveis de ambiente:**
   ```bash
   ibmcloud ce application create \
     --name ai-aent-detran \
     --build-source https://github.com/sergiogama/ai-agent-detran-backend.git \
     --port 8080 \
     --min-scale 1 \
     --max-scale 5 \
     --cpu 1 \
     --memory 2G \
     --build-commit main \
     --build-context-dir . \
     --build-dockerfile Dockerfile \
     --env DB2_HOSTNAME=1bbf73c5-d84a-4bb0-85b9-ab1a4348f4a4.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud \
     --env DB2_PORT=32286 \
     --env DB2_DATABASE=bludb \
     --env DB2_USERNAME=ytp80931 \
     --env DB2_PASSWORD=srR0pacBaWO9DAJz \
     --env DB2_SECURITY=SSL \
     --env DB2_VERIFY_SSL=false \
     --env COS_API_KEY=sua-api-key \
     --env COS_INSTANCE_CRN=seu-crn \
     --env COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud \
     --env COS_BUCKET_NAME=seu-bucket \
     --env ORCHESTRATE_API_URL=sua-url \
     --env ORCHESTRATE_API_KEY=sua-api-key \
     --env ORCHESTRATE_AGENT_ID=seu-agent-id \
     --env BACKEND_HOST=0.0.0.0 \
     --env BACKEND_PORT=8080 \
     --env BACKEND_RELOAD=false
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
ibmcloud ce application get --name detran-api
```

### 2. Testar health check:
```bash
curl https://detran-api.xxx.us-south.codeengine.appdomain.cloud/health
```

### 3. Testar API:
```bash
curl https://detran-api.xxx.us-south.codeengine.appdomain.cloud/api/db2/health
```

### 4. Ver logs:
```bash
ibmcloud ce application logs --name detran-api
```

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
ibmcloud ce application update --name detran-api \
  --image us.icr.io/detran/detran-api:latest
```

## 📊 Monitoramento

### Ver status:
```bash
ibmcloud ce application get --name detran-api
```

### Ver logs em tempo real:
```bash
ibmcloud ce application logs --name detran-api --follow
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
ibmcloud ce application logs --name detran-api --tail 100

# Verificar eventos
ibmcloud ce application events --name detran-api
```

### Erro de conexão com Db2:
- Verifique credenciais no secret
- Confirme que `DB2_VERIFY_SSL=false`
- Teste conexão via console Db2

### Timeout:
- Aumente CPU/memória
- Aumente max-scale
- Verifique logs de performance

## 📚 Recursos

- [Code Engine Docs](https://cloud.ibm.com/docs/codeengine)
- [IBM Cloud CLI](https://cloud.ibm.com/docs/cli)
- [Container Registry](https://cloud.ibm.com/docs/Registry)