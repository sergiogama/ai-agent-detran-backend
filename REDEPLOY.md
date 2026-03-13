# 🚀 Redeploy do Backend com Correção de Autenticação

## Problema Identificado

O backend deployado no Code Engine não tinha os endpoints de autenticação funcionando porque:
1. O `auth_service.py` original usava o driver nativo `ibm-db` que pode falhar no Code Engine
2. Foi criado um novo `auth_service_rest.py` que usa a API REST do Db2 (que já está funcionando)

## Arquivos Modificados

1. **`backend/services/auth_service_rest.py`** (NOVO)
   - Serviço de autenticação usando Db2ServiceRest
   
2. **`backend/api/auth_routes.py`** (MODIFICADO)
   - Suporte para fallback entre driver nativo e REST API
   
3. **`backend/main.py`** (MODIFICADO)
   - Inicialização do AuthServiceRest com injeção de dependência

## Como Fazer o Redeploy

### Opção 1: Via GitHub (Recomendado)

1. **Commit e push das alterações:**
   ```bash
   cd backend
   git add .
   git commit -m "fix: Adicionar suporte REST para autenticação"
   git push origin main
   ```

2. **Redeploy no Code Engine:**
   - O Code Engine detectará automaticamente as mudanças no GitHub
   - Ou force um novo build manualmente no console

### Opção 2: Via IBM Cloud CLI

```bash
# 1. Build da nova imagem
docker build -t detran-backend:latest .

# 2. Tag para IBM Container Registry
docker tag detran-backend:latest icr.io/<seu-namespace>/detran-backend:latest

# 3. Push para registry
docker push icr.io/<seu-namespace>/detran-backend:latest

# 4. Update da aplicação no Code Engine
ibmcloud ce application update detran-api \
  --image icr.io/<seu-namespace>/detran-backend:latest
```

### Opção 3: Rebuild Manual no Console

1. Acesse IBM Cloud Console
2. Vá para Code Engine > Applications
3. Selecione sua aplicação `detran-api`
4. Clique em "Deploy" ou "Rebuild"
5. Aguarde o deploy completar

## Verificação Pós-Deploy

Após o redeploy, teste os endpoints:

```bash
# 1. Health check
curl https://ai-agent-detran.27d5zpps5ri0.us-east.codeengine.appdomain.cloud/health

# 2. Login (use um CPF válido do seu banco)
curl -X POST "https://ai-agent-detran.27d5zpps5ri0.us-east.codeengine.appdomain.cloud/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"cpf":"537.218.694-32","senha":"1111"}'
```

## Resposta Esperada do Login

```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "cpf": "537.218.694-32",
    "nome": "Nome do Condutor",
    "cnh": "12345678901",
    "categoria_cnh": "AB"
  }
}
```

## Frontend

Após o redeploy do backend, o frontend já está configurado para usar a URL da cloud:
```
VITE_API_URL=https://ai-agent-detran.27d5zpps5ri0.us-east.codeengine.appdomain.cloud
```

Basta executar:
```bash
cd frontend
npm install
npm run dev
```

## Troubleshooting

### Se o login ainda não funcionar:

1. **Verifique os logs do Code Engine:**
   ```bash
   ibmcloud ce app logs --name detran-api
   ```

2. **Verifique se o Db2 está conectado:**
   ```bash
   curl https://ai-agent-detran.27d5zpps5ri0.us-east.codeengine.appdomain.cloud/health
   ```
   Deve mostrar: `"db2": "connected"`

3. **Verifique se o CPF existe no banco:**
   ```bash
   curl "https://ai-agent-detran.27d5zpps5ri0.us-east.codeengine.appdomain.cloud/api/db2/condutor/cpf/537.218.694-32"
   ```

4. **Verifique se o campo SENHA existe:**
   - O condutor deve ter o campo `SENHA` no banco de dados
   - Execute o script `database/add_senha_field.sql` se necessário

## Notas Importantes

- ✅ O backend agora usa REST API para autenticação (mais compatível com Code Engine)
- ✅ Mantém compatibilidade com driver nativo se disponível
- ✅ Frontend já configurado para usar a URL da cloud
- ⚠️ Certifique-se que o campo SENHA existe no banco de dados
- ⚠️ Use CPF formatado (000.000.000-00) no login