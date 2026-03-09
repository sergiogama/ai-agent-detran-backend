"""
Serviço para IBM Db2 Warehouse
"""
import ibm_db
import ibm_db_dbi
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Db2Service:
    """Serviço para gerenciar conexões e operações com IBM Db2 Warehouse"""
    
    def __init__(
        self,
        hostname: str,
        port: int,
        database: str,
        username: str,
        password: str,
        security: str = "SSL"
    ):
        """
        Inicializa o serviço Db2
        
        Args:
            hostname: Hostname do Db2 Warehouse
            port: Porta de conexão
            database: Nome do banco de dados
            username: Usuário
            password: Senha
            security: Tipo de segurança (SSL)
        """
        self.hostname = hostname
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.security = security
        self.connection = None
        
        logger.info(f"Db2 Service inicializado para database: {database}")
    
    def _get_connection_string(self) -> str:
        """Retorna a string de conexão"""
        return (
            f"DATABASE={self.database};"
            f"HOSTNAME={self.hostname};"
            f"PORT={self.port};"
            f"PROTOCOL=TCPIP;"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"SECURITY={self.security};"
        )
    
    def connect(self):
        """Estabelece conexão com o banco de dados"""
        try:
            conn_str = self._get_connection_string()
            self.connection = ibm_db.connect(conn_str, "", "")
            logger.info("Conexão com Db2 estabelecida com sucesso")
            return self.connection
        except Exception as e:
            logger.error(f"Erro ao conectar ao Db2: {str(e)}")
            raise Exception(f"Falha na conexão com Db2: {str(e)}")
    
    def disconnect(self):
        """Fecha a conexão com o banco de dados"""
        if self.connection:
            ibm_db.close(self.connection)
            self.connection = None
            logger.info("Conexão com Db2 fechada")
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Executa uma query SELECT e retorna os resultados
        
        Args:
            query: Query SQL
            params: Parâmetros da query (opcional)
            
        Returns:
            Lista de dicionários com os resultados
        """
        try:
            if not self.connection:
                self.connect()
            
            stmt = ibm_db.prepare(self.connection, query)
            
            if params:
                for i, param in enumerate(params, 1):
                    ibm_db.bind_param(stmt, i, param)
            
            ibm_db.execute(stmt)
            
            # Converter resultados para lista de dicionários
            results = []
            row = ibm_db.fetch_assoc(stmt)
            while row:
                results.append(dict(row))
                row = ibm_db.fetch_assoc(stmt)
            
            logger.info(f"Query executada com sucesso. {len(results)} registros retornados")
            return results
            
        except Exception as e:
            logger.error(f"Erro ao executar query: {str(e)}")
            raise Exception(f"Falha na execução da query: {str(e)}")
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """
        Executa uma query INSERT, UPDATE ou DELETE
        
        Args:
            query: Query SQL
            params: Parâmetros da query (opcional)
            
        Returns:
            Número de linhas afetadas
        """
        try:
            if not self.connection:
                self.connect()
            
            stmt = ibm_db.prepare(self.connection, query)
            
            if params:
                for i, param in enumerate(params, 1):
                    ibm_db.bind_param(stmt, i, param)
            
            ibm_db.execute(stmt)
            rows_affected = ibm_db.num_rows(stmt)
            
            logger.info(f"Update executado com sucesso. {rows_affected} linhas afetadas")
            return rows_affected
            
        except Exception as e:
            logger.error(f"Erro ao executar update: {str(e)}")
            raise Exception(f"Falha na execução do update: {str(e)}")
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - CONDUTORES
    # ============================================
    
    def get_condutor_by_cpf(self, cpf: str) -> Optional[Dict]:
        """Busca condutor por CPF"""
        query = "SELECT * FROM CONDUTORES WHERE CPF = ?"
        results = self.execute_query(query, (cpf,))
        return results[0] if results else None
    
    def get_condutor_by_cnh(self, cnh: str) -> Optional[Dict]:
        """Busca condutor por CNH"""
        query = "SELECT * FROM CONDUTORES WHERE CNH = ?"
        results = self.execute_query(query, (cnh,))
        return results[0] if results else None
    
    def get_situacao_condutor(self, cpf: str) -> Optional[Dict]:
        """Obtém situação completa do condutor"""
        query = "SELECT * FROM VW_SITUACAO_CONDUTORES WHERE CPF = ?"
        results = self.execute_query(query, (cpf,))
        return results[0] if results else None
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - VEÍCULOS
    # ============================================
    
    def get_veiculo_by_placa(self, placa: str) -> Optional[Dict]:
        """Busca veículo por placa"""
        query = "SELECT * FROM VEICULOS WHERE PLACA = ?"
        results = self.execute_query(query, (placa,))
        return results[0] if results else None
    
    def get_veiculos_by_condutor(self, id_condutor: int) -> List[Dict]:
        """Lista veículos de um condutor"""
        query = "SELECT * FROM VEICULOS WHERE ID_CONDUTOR = ?"
        return self.execute_query(query, (id_condutor,))
    
    def get_situacao_licenciamento(self, placa: str) -> Optional[Dict]:
        """Obtém situação de licenciamento do veículo"""
        query = "SELECT * FROM VW_SITUACAO_LICENCIAMENTO WHERE PLACA = ?"
        results = self.execute_query(query, (placa,))
        return results[0] if results else None
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - MULTAS
    # ============================================
    
    def get_multas_by_veiculo(self, placa: str) -> List[Dict]:
        """Lista multas de um veículo"""
        query = """
            SELECT m.* 
            FROM MULTAS m
            INNER JOIN VEICULOS v ON m.ID_VEICULO = v.ID_VEICULO
            WHERE v.PLACA = ?
            ORDER BY m.DATA_INFRACAO DESC
        """
        return self.execute_query(query, (placa,))
    
    def get_multas_pendentes_by_veiculo(self, placa: str) -> List[Dict]:
        """Lista multas pendentes de um veículo"""
        query = "SELECT * FROM VW_MULTAS_PENDENTES WHERE PLACA = ?"
        return self.execute_query(query, (placa,))
    
    def get_multas_by_condutor(self, cpf: str) -> List[Dict]:
        """Lista multas de um condutor"""
        query = """
            SELECT m.*
            FROM MULTAS m
            INNER JOIN VEICULOS v ON m.ID_VEICULO = v.ID_VEICULO
            INNER JOIN CONDUTORES c ON v.ID_CONDUTOR = c.ID_CONDUTOR
            WHERE c.CPF = ?
            ORDER BY m.DATA_INFRACAO DESC
        """
        return self.execute_query(query, (cpf,))
    
    def get_total_multas_pendentes(self, placa: str) -> Dict:
        """Calcula total de multas pendentes"""
        query = """
            SELECT 
                COUNT(*) AS TOTAL_MULTAS,
                COALESCE(SUM(VALOR_MULTA), 0) AS VALOR_TOTAL
            FROM MULTAS m
            INNER JOIN VEICULOS v ON m.ID_VEICULO = v.ID_VEICULO
            WHERE v.PLACA = ? AND m.STATUS_MULTA = 'PENDENTE'
        """
        results = self.execute_query(query, (placa,))
        return results[0] if results else {"TOTAL_MULTAS": 0, "VALOR_TOTAL": 0}
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - LICENCIAMENTO
    # ============================================
    
    def get_licenciamento_by_veiculo(self, placa: str, ano: int = None) -> Optional[Dict]:
        """Obtém licenciamento de um veículo"""
        if ano is None:
            ano = datetime.now().year
        
        query = """
            SELECT l.* 
            FROM LICENCIAMENTO l
            INNER JOIN VEICULOS v ON l.ID_VEICULO = v.ID_VEICULO
            WHERE v.PLACA = ? AND l.ANO_EXERCICIO = ?
        """
        results = self.execute_query(query, (placa, ano))
        return results[0] if results else None
    
    # ============================================
    # MÉTODOS DE CONSULTA INTEGRADA
    # ============================================
    
    def get_dados_completos_veiculo(self, placa: str) -> Dict:
        """
        Obtém todos os dados de um veículo incluindo:
        - Dados do veículo
        - Dados do proprietário
        - Multas pendentes
        - Situação de licenciamento
        """
        try:
            # Dados do veículo
            veiculo = self.get_veiculo_by_placa(placa)
            if not veiculo:
                return {"erro": "Veículo não encontrado"}
            
            # Dados do proprietário
            proprietario = self.get_condutor_by_cpf(veiculo.get("CPF"))
            
            # Multas
            multas_pendentes = self.get_multas_pendentes_by_veiculo(placa)
            total_multas = self.get_total_multas_pendentes(placa)
            
            # Licenciamento
            licenciamento = self.get_situacao_licenciamento(placa)
            
            return {
                "veiculo": veiculo,
                "proprietario": proprietario,
                "multas": {
                    "pendentes": multas_pendentes,
                    "total": total_multas.get("TOTAL_MULTAS", 0),
                    "valor_total": float(total_multas.get("VALOR_TOTAL", 0))
                },
                "licenciamento": licenciamento
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados completos do veículo: {str(e)}")
            return {"erro": str(e)}
    
    def get_dados_completos_condutor(self, cpf: str) -> Dict:
        """
        Obtém todos os dados de um condutor incluindo:
        - Dados do condutor
        - Veículos
        - Multas
        - Situação geral
        """
        try:
            # Dados do condutor
            condutor = self.get_condutor_by_cpf(cpf)
            if not condutor:
                return {"erro": "Condutor não encontrado"}
            
            # Situação geral
            situacao = self.get_situacao_condutor(cpf)
            
            # Veículos
            veiculos = self.get_veiculos_by_condutor(condutor.get("ID_CONDUTOR"))
            
            # Multas
            multas = self.get_multas_by_condutor(cpf)
            
            return {
                "condutor": condutor,
                "situacao": situacao,
                "veiculos": veiculos,
                "multas": multas
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter dados completos do condutor: {str(e)}")
            return {"erro": str(e)}
    
    # ============================================
    # MÉTODOS DE BUSCA GENÉRICA
    # ============================================
    
    def search(self, termo: str) -> Dict:
        """
        Busca genérica por placa, CPF ou CNH
        
        Args:
            termo: Termo de busca (placa, CPF ou CNH)
            
        Returns:
            Dados encontrados
        """
        termo = termo.replace("-", "").replace(".", "").strip().upper()
        
        # Tentar buscar como placa
        if len(termo) == 7:
            veiculo = self.get_dados_completos_veiculo(termo)
            if "erro" not in veiculo:
                return {"tipo": "veiculo", "dados": veiculo}
        
        # Tentar buscar como CPF
        if len(termo) == 11:
            condutor = self.get_dados_completos_condutor(termo)
            if "erro" not in condutor:
                return {"tipo": "condutor", "dados": condutor}
            
            # Tentar como CNH
            condutor_cnh = self.get_condutor_by_cnh(termo)
            if condutor_cnh:
                dados = self.get_dados_completos_condutor(condutor_cnh.get("CPF"))
                return {"tipo": "condutor", "dados": dados}
        
        return {"erro": "Nenhum registro encontrado"}