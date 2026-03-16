"""
Serviço para IBM Db2 Warehouse usando REST API
Compatível com Apple Silicon (ARM64)
"""
import requests
import base64
from typing import List, Dict, Optional, Any
import logging
from datetime import datetime
import urllib3

# Desabilitar warnings de SSL quando verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class Db2ServiceRest:
    """Serviço para gerenciar operações com IBM Db2 Warehouse via REST API"""
    
    def __init__(
        self,
        hostname: str,
        port: int,
        database: str,
        username: str,
        password: str,
        security: str = "SSL",
        verify_ssl: bool = False
    ):
        """
        Inicializa o serviço Db2 via REST API
        
        Args:
            hostname: Hostname do Db2 Warehouse
            port: Porta de conexão
            database: Nome do banco de dados
            username: Usuário
            password: Senha
            security: Tipo de segurança (SSL)
            verify_ssl: Se True, verifica certificado SSL (padrão: False para compatibilidade)
        """
        self.hostname = hostname
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.security = security
        self.verify_ssl = verify_ssl
        
        # IBM Db2 on Cloud REST API v4
        # Documentação: https://cloud.ibm.com/apidocs/db2-on-cloud/db2-on-cloud-v4
        # REST API usa porta 443 (HTTPS padrão), não a porta 32286 (que é para conexão nativa)
        self.base_url = f"https://{hostname}/dbapi/v4"
        
        # Deployment ID (obrigatório no header X-Deployment-Id)
        self.deployment_id = database
        
        # Gerar Bearer token (IBM Cloud usa IAM token ou API key)
        # Por enquanto, vamos tentar Basic Auth primeiro
        credentials = f"{username}:{password}"
        self.auth_header = base64.b64encode(credentials.encode()).decode()
        self.bearer_token = None  # Será obtido via IAM se necessário
        
        logger.info(f"Db2 REST Service inicializado para database: {database}")
        logger.info(f"Base URL (REST API): {self.base_url}")
        logger.info(f"Porta nativa (não usada pela REST API): {port}")
        if not self.verify_ssl:
            logger.warning("SSL certificate verification is DISABLED. This is not recommended for production environments.")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Retorna headers para requisições
        Documentação oficial: https://cloud.ibm.com/apidocs/db2-on-cloud/db2-on-cloud-v4
        Requer: Bearer token + x-deployment-id (lowercase)
        """
        return {
            "Authorization": f"Basic {self.auth_header}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-deployment-id": self.database  # Obrigatório (lowercase conforme documentação)
        }
    
    def execute_query(self, query: str) -> List[Dict]:
        """
        Executa uma query SELECT via REST API
        
        Args:
            query: Query SQL
            
        Returns:
            Lista de dicionários com os resultados
        """
        try:
            # Endpoint correto segundo documentação v4
            url = f"{self.base_url}/sql_jobs"
            
            logger.info(f"🔄 Executando query via DB2 on Cloud v4 API")
            logger.info(f"📍 URL: {url}")
            
            payload = {
                "commands": query,
                "limit": 1000,
                "separator": ";",
                "stop_on_error": "yes"
            }
            
            logger.debug(f"Executando query via REST API: {url}")
            logger.debug(f"Payload: {payload}")
            
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                verify=self.verify_ssl,
                timeout=30
            )
            
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            
            if response.status_code == 201:
                job_data = response.json()
                job_id = job_data.get("id")
                
                # Aguardar conclusão do job
                result_url = f"{self.base_url}/sql_jobs/{job_id}"
                result_response = requests.get(
                    result_url,
                    headers=self._get_headers(),
                    verify=self.verify_ssl
                )
                
                if result_response.status_code == 200:
                    result_data = result_response.json()
                    results = result_data.get("results", [])
                    
                    if results and len(results) > 0:
                        rows = results[0].get("rows", [])
                        columns = results[0].get("columns", [])
                        
                        # Converter para lista de dicionários
                        formatted_results = []
                        for row in rows:
                            row_dict = {}
                            for i, col in enumerate(columns):
                                row_dict[col] = row[i] if i < len(row) else None
                            formatted_results.append(row_dict)
                        
                        logger.info(f"Query executada com sucesso. {len(formatted_results)} registros retornados")
                        return formatted_results
                    
                    return []
            
            logger.error(f"Erro na execução da query: {response.status_code}")
            logger.error(f"Response text: {response.text}")
            logger.error(f"URL tentada: {url}")
            logger.error(f"Headers enviados: {self._get_headers()}")
            return []
            
        except Exception as e:
            logger.error(f"Erro ao executar query via REST: {str(e)}")
            return []
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - CONDUTORES
    # ============================================
    
    def get_condutor_by_cpf(self, cpf: str) -> Optional[Dict]:
        """Busca condutor por CPF"""
        query = f"SELECT * FROM CONDUTORES WHERE CPF = '{cpf}'"
        results = self.execute_query(query)
        return results[0] if results else None
    
    def get_condutor_by_cnh(self, cnh: str) -> Optional[Dict]:
        """Busca condutor por CNH"""
        query = f"SELECT * FROM CONDUTORES WHERE CNH = '{cnh}'"
        results = self.execute_query(query)
        return results[0] if results else None
    
    def get_situacao_condutor(self, cpf: str) -> Optional[Dict]:
        """Obtém situação completa do condutor"""
        query = f"SELECT * FROM VW_SITUACAO_CONDUTORES WHERE CPF = '{cpf}'"
        results = self.execute_query(query)
        return results[0] if results else None
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - VEÍCULOS
    # ============================================
    
    def get_veiculo_by_placa(self, placa: str) -> Optional[Dict]:
        """Busca veículo por placa"""
        query = f"SELECT * FROM VEICULOS WHERE PLACA = '{placa}'"
        results = self.execute_query(query)
        return results[0] if results else None
    
    def get_veiculos_by_condutor(self, id_condutor: int) -> List[Dict]:
        """Lista veículos de um condutor"""
        query = f"SELECT * FROM VEICULOS WHERE ID_CONDUTOR = {id_condutor}"
        return self.execute_query(query)
    
    def get_situacao_licenciamento(self, placa: str) -> Optional[Dict]:
        """Obtém situação de licenciamento do veículo"""
        query = f"SELECT * FROM VW_SITUACAO_LICENCIAMENTO WHERE PLACA = '{placa}'"
        results = self.execute_query(query)
        return results[0] if results else None
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - MULTAS
    # ============================================
    
    def get_multas_by_veiculo(self, placa: str) -> List[Dict]:
        """Lista multas de um veículo"""
        query = f"""
            SELECT m.* 
            FROM MULTAS m
            INNER JOIN VEICULOS v ON m.ID_VEICULO = v.ID_VEICULO
            WHERE v.PLACA = '{placa}'
            ORDER BY m.DATA_INFRACAO DESC
        """
        return self.execute_query(query)
    
    def get_multas_pendentes_by_veiculo(self, placa: str) -> List[Dict]:
        """Lista multas pendentes de um veículo"""
        query = f"SELECT * FROM VW_MULTAS_PENDENTES WHERE PLACA = '{placa}'"
        return self.execute_query(query)
    
    def get_total_multas_pendentes(self, placa: str) -> Dict:
        """Calcula total de multas pendentes"""
        query = f"""
            SELECT 
                COUNT(*) AS TOTAL_MULTAS,
                COALESCE(SUM(VALOR_MULTA), 0) AS VALOR_TOTAL
            FROM MULTAS m
            INNER JOIN VEICULOS v ON m.ID_VEICULO = v.ID_VEICULO
            WHERE v.PLACA = '{placa}' AND m.STATUS_MULTA = 'PENDENTE'
        """
        results = self.execute_query(query)
        return results[0] if results else {"TOTAL_MULTAS": 0, "VALOR_TOTAL": 0}
    
    # ============================================
    # MÉTODOS ESPECÍFICOS - LICENCIAMENTO
    # ============================================
    
    def get_licenciamento_by_veiculo(self, placa: str, ano: int = None) -> Optional[Dict]:
        """Obtém licenciamento de um veículo"""
        if ano is None:
            ano = datetime.now().year
        
        query = f"""
            SELECT l.* 
            FROM LICENCIAMENTO l
            INNER JOIN VEICULOS v ON l.ID_VEICULO = v.ID_VEICULO
            WHERE v.PLACA = '{placa}' AND l.ANO_EXERCICIO = {ano}
        """
        results = self.execute_query(query)
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
            
            # Dados do proprietário via JOIN
            query = f"""
                SELECT c.* 
                FROM CONDUTORES c
                INNER JOIN VEICULOS v ON c.ID_CONDUTOR = v.ID_CONDUTOR
                WHERE v.PLACA = '{placa}'
            """
            proprietario_results = self.execute_query(query)
            proprietario = proprietario_results[0] if proprietario_results else None
            
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
            
            # Multas via JOIN
            query = f"""
                SELECT m.* 
                FROM MULTAS m
                INNER JOIN VEICULOS v ON m.ID_VEICULO = v.ID_VEICULO
                INNER JOIN CONDUTORES c ON v.ID_CONDUTOR = c.ID_CONDUTOR
                WHERE c.CPF = '{cpf}'
                ORDER BY m.DATA_INFRACAO DESC
            """
            multas = self.execute_query(query)
            
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
    
    def update_condutor_imagem(self, cpf: str, url_imagem: str) -> bool:
        """Atualiza URL da imagem CNH do condutor"""
        try:
            query = f"""
                UPDATE CONDUTORES 
                SET URL_IMAGEM_CNH = '{url_imagem}'
                WHERE CPF = '{cpf}'
            """
            self.execute_query(query)
            logger.info(f"URL da imagem CNH atualizada para CPF: {cpf}")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar URL da imagem: {str(e)}")
            return False