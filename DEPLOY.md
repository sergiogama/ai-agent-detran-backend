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
ibmcloud login --sso
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
   ibmcloud ce project create --name detran-project
   ibmcloud ce project select --name detran-project
   ```

3. **Crie secrets para credenciais sensíveis:**
   ```bash
   ibmcloud ce secret create --name detran-secrets \
     --from-literal DB2_PASSWORD=sua-senha \
     --from-literal DB2_USERNAME=seu-usuario \
     --from-literal COS_API_KEY=sua-api-key \
     --from-literal ORCHESTRATE_API_KEY=sua-api-key
   ```

4. **Crie configmap para outras variáveis:**
   ```bash
   ibmcloud ce configmap create --name detran-config \
     --from-literal DB2_HOSTNAME=seu-hostname.databases.appdomain.cloud \
     --from-literal DB2_PORT=32286 \
     --from-literal DB2_DATABASE=bludb \
     --from-literal DB2_SECURITY=SSL \
     --from-literal DB2_VERIFY_SSL=false \
     --from-literal COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud \
     --from-literal COS_BUCKET_NAME=seu-bucket \
     --from-literal COS_INSTANCE_CRN=seu-crn \
     --from-literal ORCHESTRATE_API_URL=sua-url \
     --from-literal ORCHESTRATE_AGENT_ID=seu-agent-id \
     --from-literal BACKEND_HOST=0.0.0.0 \
     --from-literal BACKEND_PORT=8080 \
     --from-literal BACKEND_RELOAD=false
   ```

5. **Deploy da aplicação:**
   ```bash
   ibmcloud ce application create \
     --name detran-api \
     --build-source https://github.com/seu-usuario/detran-backend \
     --build-context-dir backend \
     --port 8080 \
     --min-scale 1 \
     --max-scale 5 \
     --cpu 1 \
     --memory 2G \
     --env-from-configmap detran-config \
     --env-from-secret detran-secrets
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