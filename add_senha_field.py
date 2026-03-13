#!/usr/bin/env python3
"""
Script para adicionar campo SENHA na tabela CONDUTORES
Usa a API REST do DB2 para evitar problemas com REORG
"""

import os
import sys
from dotenv import load_dotenv

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.db2_service_rest import Db2ServiceRest

def main():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    print("=" * 60)
    print("Script para Adicionar Campo SENHA na Tabela CONDUTORES")
    print("=" * 60)
    print()
    
    # Configurar conexão
    try:
        db2 = Db2ServiceRest(
            hostname=os.getenv('DB2_HOSTNAME'),
            port=int(os.getenv('DB2_PORT', 50001)),
            database=os.getenv('DB2_DATABASE'),
            username=os.getenv('DB2_USERNAME'),
            password=os.getenv('DB2_PASSWORD'),
            security=os.getenv('DB2_SECURITY', 'SSL')
        )
        print("✓ Conexão com DB2 estabelecida")
        print()
    except Exception as e:
        print(f"❌ Erro ao conectar ao DB2: {e}")
        return 1
    
    # Verificar se o campo já existe
    print("Verificando se o campo SENHA já existe...")
    try:
        check_query = """
            SELECT COLNAME, TYPENAME, LENGTH 
            FROM SYSCAT.COLUMNS 
            WHERE TABNAME = 'CONDUTORES' 
            AND COLNAME = 'SENHA'
        """
        result = db2.execute_query(check_query)
        
        if result:
            print("⚠️  Campo SENHA já existe na tabela CONDUTORES")
            print(f"   Tipo: {result[0]['TYPENAME']}, Tamanho: {result[0]['LENGTH']}")
            print()
            
            # Perguntar se deseja atualizar os valores
            response = input("Deseja atualizar todos os registros com senha '1111'? (s/n): ")
            if response.lower() != 's':
                print("Operação cancelada.")
                return 0
            
            # Atualizar registros
            print("\nAtualizando registros com senha padrão '1111'...")
            try:
                update_query = "UPDATE CONDUTORES SET SENHA = '1111' WHERE SENHA IS NULL OR SENHA = ''"
                db2.execute_query(update_query)
                print("✓ Registros atualizados com sucesso")
            except Exception as e:
                print(f"❌ Erro ao atualizar registros: {e}")
                return 1
        else:
            print("✓ Campo SENHA não existe, prosseguindo com a criação...")
            print()
            
            # Adicionar coluna SENHA
            print("Adicionando coluna SENHA à tabela CONDUTORES...")
            try:
                alter_query = "ALTER TABLE CONDUTORES ADD COLUMN SENHA VARCHAR(255)"
                db2.execute_query(alter_query)
                print("✓ Coluna SENHA adicionada com sucesso")
                print()
            except Exception as e:
                print(f"❌ Erro ao adicionar coluna: {e}")
                print("\nTentando solução alternativa...")
                
                # Tentar sem especificar o tamanho
                try:
                    alter_query = "ALTER TABLE CONDUTORES ADD SENHA VARCHAR(255)"
                    db2.execute_query(alter_query)
                    print("✓ Coluna SENHA adicionada com sucesso (método alternativo)")
                    print()
                except Exception as e2:
                    print(f"❌ Erro na solução alternativa: {e2}")
                    return 1
            
            # Atualizar todos os registros com senha padrão
            print("Atualizando todos os registros com senha padrão '1111'...")
            try:
                update_query = "UPDATE CONDUTORES SET SENHA = '1111'"
                db2.execute_query(update_query)
                print("✓ Todos os registros atualizados com senha '1111'")
                print()
            except Exception as e:
                print(f"❌ Erro ao atualizar registros: {e}")
                return 1
    
    except Exception as e:
        print(f"❌ Erro ao verificar campo: {e}")
        return 1
    
    # Verificar resultado
    print("Verificando resultado final...")
    try:
        verify_query = "SELECT CPF, NOME, SENHA FROM CONDUTORES FETCH FIRST 5 ROWS ONLY"
        result = db2.execute_query(verify_query)
        
        if result:
            print("\n✓ Primeiros 5 registros:")
            print("-" * 60)
            for row in result:
                cpf = row.get('CPF', 'N/A')
                nome = row.get('NOME', 'N/A')
                senha = row.get('SENHA', 'N/A')
                print(f"CPF: {cpf:15} | Nome: {nome:20} | Senha: {senha}")
            print("-" * 60)
        else:
            print("⚠️  Nenhum registro encontrado")
    except Exception as e:
        print(f"❌ Erro ao verificar resultado: {e}")
        return 1
    
    print()
    print("=" * 60)
    print("✅ Campo SENHA adicionado e configurado com sucesso!")
    print("=" * 60)
    print()
    print("Próximos passos:")
    print("1. Inicie o backend: cd backend && python main.py")
    print("2. Inicie o frontend: cd frontend && npm run dev")
    print("3. Acesse: http://localhost:3000")
    print("4. Faça login com qualquer CPF cadastrado e senha: 1111")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())