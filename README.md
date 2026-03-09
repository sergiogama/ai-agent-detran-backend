# 🚗 Detran Backend API

API REST para consulta de dados do DETRAN integrada com IBM Db2 e Watsonx Orchestrate.

## 🚀 Deploy no IBM Code Engine

### Pré-requisitos

- Conta IBM Cloud
- IBM Db2 Warehouse on Cloud configurado
- IBM Cloud Object Storage configurado
- IBM Watsonx Orchestrate configurado

### Passos para Deploy

1. **Fork/Clone este repositório**

2. **Configure as variáveis de ambiente no Code Engine:**
   ```bash
   # IBM Db2
   DB2_HOSTNAME=seu-hostname.databases.appdomain.cloud
   DB2_PORT=32286
   DB2_DATABASE=bludb
   DB2_USERNAME=seu-usuario
   DB2_PASSWORD=sua-senha
   DB2_SECURITY=SSL
   DB2_VERIFY_SSL=false
   
   # IBM COS
   COS_API_KEY=sua-api-key
   COS_INSTANCE_CRN=seu-crn
   COS_ENDPOINT=https://s3.br-sao.cloud-object-storage.appdomain.cloud
   COS_BUCKET_NAME=seu-bucket
   
   # Watsonx Orchestrate
   ORCHESTRATE_API_URL=sua-url
   ORCHESTRATE_API_KEY=sua-key
   ORCHESTRATE_AGENT_ID=seu-agent-id
   
   # Backend
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8080
   BACKEND_RELOAD=false
   ```

3. **Deploy via IBM Cloud CLI:**
   ```bash
   ibmcloud ce application create \
     --name detran-api \
     --image icr.io/seu-namespace/detran-api:latest \
     --port 8080 \
     --min-scale 1 \
     --max-scale 3 \
     --cpu 1 \
     --memory 2G \
     --env-from-configmap detran-config \
     --env-from-secret detran-secrets
   ```

4. **Ou deploy via Console:**
   - Acesse IBM Cloud Console
   - Vá para Code Engine
   - Crie uma nova Application
   - Conecte ao repositório GitHub
   - Configure as variáveis de ambiente
   - Deploy!

## 🏗️ Estrutura

```
backend/
├── api/                    # Rotas da API
│   ├── __init__.py
│   └── db2_routes.py
├── services/              # Lógica de negócio
│   ├── db2_service.py
│   └── db2_service_rest.py
├── config.py              # Configurações
├── main.py                # Aplicação FastAPI
├── requirements.txt       # Dependências
├── Dockerfile            # Container
└── .env.example          # Template de configuração
```

## 📡 Endpoints

### Health Check
```
GET /health
GET /api/db2/health
```

### Busca
```
GET /api/db2/search?termo={placa|cpf|cnh}
```

### Condutores
```
GET /api/db2/condutor/cpf/{cpf}
GET /api/db2/condutor/cnh/{cnh}
GET /api/db2/situacao/condutor/{cpf}
```

### Veículos
```
GET /api/db2/veiculo/placa/{placa}
GET /api/db2/situacao/licenciamento/{placa}
```

### Multas
```
GET /api/db2/multas/veiculo/{placa}
GET /api/db2/multas/condutor/{cpf}
```

### Upload
```
POST /api/upload
```

### Chat
```
POST /api/session
POST /api/chat
DELETE /api/session/{session_id}
GET /api/session/{session_id}/history
```

## 🔧 Desenvolvimento Local

### Com Docker (Recomendado)
```bash
docker build -t detran-api .
docker run -p 8080:8080 --env-file .env detran-api
```

### Sem Docker
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8080
```

## 📚 Documentação

Acesse `/docs` para documentação interativa (Swagger UI).

## 🔐 Segurança

- Nunca commite o arquivo `.env`
- Use secrets do Code Engine para credenciais
- Configure CORS adequadamente para produção
- Habilite HTTPS no Code Engine

## 📄 Licença

Copyright © 2024