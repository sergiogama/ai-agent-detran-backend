# 🐳 Atualizar Backend no Docker

Guia para atualizar e reexecutar o backend que está rodando no Docker.

## 🔄 Atualização Rápida

### Opção 1: Rebuild Completo (Recomendado)

```bash
cd backend

# Parar containers
docker-compose down

# Rebuild da imagem
docker-compose build --no-cache

# Iniciar novamente
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### Opção 2: Restart Simples (se só mudou código Python)

```bash
cd backend

# Restart do container
docker-compose restart

# Ver logs
docker-compose logs -f
```

## 📋 Passo a Passo Detalhado

### 1. Verificar Containers Rodando

```bash
docker ps
```

Você deve ver algo como:
```
CONTAINER ID   IMAGE              COMMAND                  STATUS
abc123def456   backend_app        "python main.py"         Up 5 minutes
```

### 2. Parar o Backend

```bash
cd backend
docker-compose down
```

Ou se preferir parar sem remover:
```bash
docker-compose stop
```

### 3. Verificar Mudanças nos Arquivos

As mudanças que fizemos:
- ✅ `services/auth_service.py` - Corrigido nome da classe
- ✅ `api/auth_routes.py` - Nova API de autenticação
- ✅ `api/chat_routes.py` - Nova API de chat
- ✅ `services/chat_service.py` - Novo serviço de chat
- ✅ `main.py` - Adicionadas novas rotas
- ✅ `requirements.txt` - Adicionado PyJWT

### 4. Rebuild da Imagem Docker

```bash
cd backend

# Rebuild sem cache (garante que tudo seja atualizado)
docker-compose build --no-cache

# Ou rebuild normal (mais rápido)
docker-compose build
```

### 5. Iniciar o Backend Atualizado

```bash
# Iniciar em background
docker-compose up -d

# Ou iniciar em foreground (ver logs direto)
docker-compose up
```

### 6. Verificar se Está Rodando

```bash
# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Testar health endpoint
curl http://localhost:5000/health
```

## 🔍 Verificar Novas Rotas

### Testar API de Autenticação

```bash
# Testar login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"cpf":"11111111111","senha":"1111"}'
```

**Resposta esperada:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "cpf": "111.111.111-11",
    "nome": "João Silva",
    ...
  }
}
```

### Testar API de Chat

```bash
# Primeiro faça login e pegue o token
TOKEN="seu_token_aqui"

# Testar chat
curl -X POST http://localhost:5000/api/chat/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Olá, quero consultar minhas multas"}'
```

## 🐛 Solução de Problemas

### Container não inicia

```bash
# Ver logs de erro
docker-compose logs

# Ver logs específicos do app
docker-compose logs app
```

### Erro de dependências

```bash
# Entrar no container
docker-compose exec app bash

# Verificar se PyJWT está instalado
pip list | grep PyJWT

# Se não estiver, instalar
pip install PyJWT>=2.8.0
```

### Mudanças não aparecem

```bash
# Rebuild forçado sem cache
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Ver logs em tempo real

```bash
# Todos os serviços
docker-compose logs -f

# Apenas o app
docker-compose logs -f app

# Últimas 100 linhas
docker-compose logs --tail=100 app
```

## 📝 Comandos Úteis

### Gerenciamento de Containers

```bash
# Listar containers
docker ps

# Listar todos (incluindo parados)
docker ps -a

# Parar todos
docker-compose down

# Parar e remover volumes
docker-compose down -v

# Restart
docker-compose restart

# Restart de um serviço específico
docker-compose restart app
```

### Logs e Debug

```bash
# Ver logs
docker-compose logs

# Logs em tempo real
docker-compose logs -f

# Logs de um serviço
docker-compose logs app

# Últimas N linhas
docker-compose logs --tail=50 app
```

### Executar Comandos no Container

```bash
# Entrar no container
docker-compose exec app bash

# Executar comando direto
docker-compose exec app python test_login.py

# Adicionar campo senha
docker-compose exec app python add_senha_field.py
```

### Limpeza

```bash
# Remover containers parados
docker-compose down

# Remover imagens não usadas
docker image prune

# Limpeza completa (cuidado!)
docker system prune -a
```

## 🔄 Workflow Completo de Atualização

```bash
# 1. Ir para o diretório backend
cd backend

# 2. Parar containers
docker-compose down

# 3. Rebuild da imagem
docker-compose build --no-cache

# 4. Iniciar novamente
docker-compose up -d

# 5. Verificar logs
docker-compose logs -f

# 6. Testar health
curl http://localhost:5000/health

# 7. Testar login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"cpf":"11111111111","senha":"1111"}'
```

## 📊 Verificar Status

### Health Check

```bash
curl http://localhost:5000/health
```

### Endpoints Disponíveis

```bash
curl http://localhost:5000/
```

### Verificar Rotas

```bash
# Listar todas as rotas
docker-compose exec app python -c "
from main import app
for route in app.routes:
    print(f'{route.methods} {route.path}')
"
```

## 🎯 Checklist de Atualização

- [ ] Código atualizado localmente
- [ ] `docker-compose down` executado
- [ ] `docker-compose build --no-cache` executado
- [ ] `docker-compose up -d` executado
- [ ] Logs verificados (`docker-compose logs -f`)
- [ ] Health endpoint testado
- [ ] API de login testada
- [ ] API de chat testada
- [ ] Frontend conectando corretamente

## 🚀 Iniciar Frontend

Após atualizar o backend:

```bash
# Em outro terminal
cd frontend
npm run dev
```

Acesse: http://localhost:3000

## 📞 Suporte

Se tiver problemas:

1. Verifique os logs: `docker-compose logs -f`
2. Verifique se o container está rodando: `docker ps`
3. Teste o health endpoint: `curl http://localhost:5000/health`
4. Verifique as variáveis de ambiente no `.env`
5. Tente rebuild completo: `docker-compose down && docker-compose build --no-cache && docker-compose up -d`

## 💡 Dicas

- Use `docker-compose logs -f` para ver logs em tempo real
- Use `--no-cache` no build para garantir que tudo seja atualizado
- Sempre teste o health endpoint após atualizar
- Mantenha o `.env` atualizado com as configurações corretas
- Use `docker-compose exec app bash` para debug dentro do container