#!/usr/bin/env python3
"""
Script de teste completo do sistema de login
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db2_service_rest import Db2ServiceRest
from services.auth_service import AuthService

load_dotenv()

def test_database_connection():
    """Testa conexão com o banco de dados"""
    print("=" * 60)
    print("1. Testando Conexão com Banco de Dados")
    print("=" * 60)
    
    try:
        db2 = Db2ServiceRest(
            hostname=os.getenv('DB2_HOSTNAME'),
            port=int(os.getenv('DB2_PORT', 50001)),
            database=os.getenv('DB2_DATABASE'),
            username=os.getenv('DB2_USERNAME'),
            password=os.getenv('DB2_PASSWORD')
        )
        
        result = db2.execute_query("SELECT COUNT(*) as TOTAL FROM CONDUTORES")
        print(f"✓ Conexão OK - Total de condutores: {result[0]['TOTAL']}")
        return True
    except Exception as e:
        print(f"✗ Erro na conexão: {e}")
        return False

def test_senha_field():
    """Testa se o campo SENHA existe"""
    print("\n" + "=" * 60)
    print("2. Verificando Campo SENHA")
    print("=" * 60)
    
    try:
        db2 = Db2ServiceRest(
            hostname=os.getenv('DB2_HOSTNAME'),
            port=int(os.getenv('DB2_PORT', 50001)),
            database=os.getenv('DB2_DATABASE'),
            username=os.getenv('DB2_USERNAME'),
            password=os.getenv('DB2_PASSWORD')
        )
        
        result = db2.execute_query("SELECT CPF, NOME, SENHA FROM CONDUTORES FETCH FIRST 3 ROWS ONLY")
        
        if result and 'SENHA' in result[0]:
            print("✓ Campo SENHA existe")
            print("\nPrimeiros registros:")
            for row in result:
                print(f"  CPF: {row['CPF']}, Nome: {row['NOME']}, Senha: {row['SENHA']}")
            return True
        else:
            print("✗ Campo SENHA não existe")
            return False
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def test_auth_service():
    """Testa o serviço de autenticação"""
    print("\n" + "=" * 60)
    print("3. Testando Serviço de Autenticação")
    print("=" * 60)
    
    try:
        auth = AuthService()
        
        # Pegar primeiro CPF do banco
        db2 = Db2ServiceRest(
            hostname=os.getenv('DB2_HOSTNAME'),
            port=int(os.getenv('DB2_PORT', 50001)),
            database=os.getenv('DB2_DATABASE'),
            username=os.getenv('DB2_USERNAME'),
            password=os.getenv('DB2_PASSWORD')
        )
        
        result = db2.execute_query("SELECT CPF FROM CONDUTORES FETCH FIRST 1 ROW ONLY")
        if not result:
            print("✗ Nenhum condutor encontrado no banco")
            return False
        
        cpf = result[0]['CPF']
        print(f"Testando login com CPF: {cpf}")
        
        # Testar autenticação
        login_result = auth.login(cpf, "1111")
        
        if login_result:
            print("✓ Autenticação bem-sucedida")
            print(f"  Token: {login_result['access_token'][:50]}...")
            print(f"  Usuário: {login_result['user']['nome']}")
            return True
        else:
            print("✗ Autenticação falhou")
            return False
    except Exception as e:
        print(f"✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint():
    """Testa o endpoint da API"""
    print("\n" + "=" * 60)
    print("4. Testando Endpoint da API")
    print("=" * 60)
    
    try:
        # Verificar se backend está rodando
        response = requests.get("http://localhost:5000/health", timeout=5)
        if response.status_code != 200:
            print("✗ Backend não está respondendo corretamente")
            return False
        
        print("✓ Backend está rodando")
        
        # Pegar primeiro CPF do banco
        db2 = Db2ServiceRest(
            hostname=os.getenv('DB2_HOSTNAME'),
            port=int(os.getenv('DB2_PORT', 50001)),
            database=os.getenv('DB2_DATABASE'),
            username=os.getenv('DB2_USERNAME'),
            password=os.getenv('DB2_PASSWORD')
        )
        
        result = db2.execute_query("SELECT CPF FROM CONDUTORES FETCH FIRST 1 ROW ONLY")
        cpf = result[0]['CPF']
        
        # Testar login via API
        response = requests.post(
            "http://localhost:5000/api/auth/login",
            json={"cpf": cpf, "senha": "1111"},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✓ Login via API bem-sucedido")
            print(f"  Token recebido: {data['access_token'][:50]}...")
            return True
        else:
            print(f"✗ Login via API falhou: {response.status_code}")
            print(f"  Resposta: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Não foi possível conectar ao backend")
        print("  Certifique-se de que o backend está rodando: python main.py")
        return False
    except Exception as e:
        print(f"✗ Erro: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("TESTE COMPLETO DO SISTEMA DE LOGIN")
    print("=" * 60 + "\n")
    
    results = []
    
    results.append(("Conexão com Banco", test_database_connection()))
    results.append(("Campo SENHA", test_senha_field()))
    results.append(("Serviço de Autenticação", test_auth_service()))
    results.append(("Endpoint da API", test_api_endpoint()))
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{name:30} {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ TODOS OS TESTES PASSARAM!")
        print("=" * 60)
        print("\nO sistema está funcionando corretamente.")
        print("Você pode fazer login no frontend com qualquer CPF cadastrado e senha '1111'")
    else:
        print("✗ ALGUNS TESTES FALHARAM")
        print("=" * 60)
        print("\nVerifique os erros acima e corrija antes de usar o sistema.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())