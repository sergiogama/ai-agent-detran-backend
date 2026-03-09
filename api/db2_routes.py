"""
Rotas da API para consultas no Db2 Warehouse
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from services.db2_service import Db2Service
from config import settings

logger = logging.getLogger(__name__)

# Criar router
router = APIRouter(prefix="/api/db2", tags=["Db2 Warehouse"])

# Inicializar serviço Db2 com driver nativo
db2_service = Db2Service(
    hostname=settings.db2_hostname,
    port=settings.db2_port,
    database=settings.db2_database,
    username=settings.db2_username,
    password=settings.db2_password,
    security=settings.db2_security
)

logger.info("Db2 Service inicializado com driver nativo ibm_db")


@router.get("/search")
async def search(
    termo: str = Query(..., description="Placa, CPF ou CNH para buscar")
):
    """
    Busca genérica por placa, CPF ou CNH
    
    Args:
        termo: Placa (7 dígitos), CPF (11 dígitos) ou CNH (11 dígitos)
        
    Returns:
        Dados encontrados
    """
    try:
        resultado = db2_service.search(termo)
        
        if "erro" in resultado:
            raise HTTPException(status_code=404, detail=resultado["erro"])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro na busca: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro na busca: {str(e)}")


@router.get("/condutor/cpf/{cpf}")
async def get_condutor_by_cpf(cpf: str):
    """
    Busca condutor por CPF
    
    Args:
        cpf: CPF do condutor (11 dígitos)
        
    Returns:
        Dados completos do condutor
    """
    try:
        resultado = db2_service.get_dados_completos_condutor(cpf)
        
        if "erro" in resultado:
            raise HTTPException(status_code=404, detail=resultado["erro"])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar condutor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar condutor: {str(e)}")


@router.get("/condutor/cnh/{cnh}")
async def get_condutor_by_cnh(cnh: str):
    """
    Busca condutor por CNH
    
    Args:
        cnh: Número da CNH (11 dígitos)
        
    Returns:
        Dados completos do condutor
    """
    try:
        condutor = db2_service.get_condutor_by_cnh(cnh)
        
        if not condutor:
            raise HTTPException(status_code=404, detail="Condutor não encontrado")
        
        resultado = db2_service.get_dados_completos_condutor(condutor.get("CPF"))
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar condutor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar condutor: {str(e)}")


@router.get("/veiculo/placa/{placa}")
async def get_veiculo_by_placa(placa: str):
    """
    Busca veículo por placa
    
    Args:
        placa: Placa do veículo (7 caracteres)
        
    Returns:
        Dados completos do veículo
    """
    try:
        resultado = db2_service.get_dados_completos_veiculo(placa.upper())
        
        if "erro" in resultado:
            raise HTTPException(status_code=404, detail=resultado["erro"])
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar veículo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar veículo: {str(e)}")


@router.get("/multas/veiculo/{placa}")
async def get_multas_veiculo(
    placa: str,
    apenas_pendentes: bool = Query(False, description="Retornar apenas multas pendentes")
):
    """
    Lista multas de um veículo
    
    Args:
        placa: Placa do veículo
        apenas_pendentes: Se True, retorna apenas multas pendentes
        
    Returns:
        Lista de multas
    """
    try:
        if apenas_pendentes:
            multas = db2_service.get_multas_pendentes_by_veiculo(placa.upper())
        else:
            multas = db2_service.get_multas_by_veiculo(placa.upper())
        
        total = db2_service.get_total_multas_pendentes(placa.upper())
        
        return {
            "placa": placa.upper(),
            "multas": multas,
            "total_pendentes": total.get("TOTAL_MULTAS", 0),
            "valor_total_pendente": float(total.get("VALOR_TOTAL", 0))
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar multas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar multas: {str(e)}")


@router.get("/multas/condutor/{cpf}")
async def get_multas_condutor(cpf: str):
    """
    Lista multas de um condutor
    
    Args:
        cpf: CPF do condutor
        
    Returns:
        Lista de multas
    """
    try:
        multas = db2_service.get_multas_by_condutor(cpf)
        
        return {
            "cpf": cpf,
            "multas": multas,
            "total": len(multas)
        }
        
    except Exception as e:
        logger.error(f"Erro ao buscar multas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar multas: {str(e)}")


@router.get("/licenciamento/{placa}")
async def get_licenciamento(
    placa: str,
    ano: Optional[int] = Query(None, description="Ano do licenciamento")
):
    """
    Obtém situação de licenciamento de um veículo
    
    Args:
        placa: Placa do veículo
        ano: Ano do licenciamento (opcional, padrão: ano atual)
        
    Returns:
        Dados do licenciamento
    """
    try:
        licenciamento = db2_service.get_licenciamento_by_veiculo(placa.upper(), ano)
        
        if not licenciamento:
            raise HTTPException(
                status_code=404,
                detail=f"Licenciamento não encontrado para o ano {ano or 'atual'}"
            )
        
        return licenciamento
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar licenciamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar licenciamento: {str(e)}")


@router.get("/situacao/condutor/{cpf}")
async def get_situacao_condutor(cpf: str):
    """
    Obtém situação geral de um condutor
    
    Args:
        cpf: CPF do condutor
        
    Returns:
        Situação do condutor (CNH, pontos, multas, etc)
    """
    try:
        situacao = db2_service.get_situacao_condutor(cpf)
        
        if not situacao:
            raise HTTPException(status_code=404, detail="Condutor não encontrado")
        
        return situacao
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar situação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar situação: {str(e)}")


@router.get("/situacao/licenciamento/{placa}")
async def get_situacao_licenciamento(placa: str):
    """
    Obtém situação de licenciamento de um veículo
    
    Args:
        placa: Placa do veículo
        
    Returns:
        Situação do licenciamento
    """
    try:
        situacao = db2_service.get_situacao_licenciamento(placa.upper())
        
        if not situacao:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        
        return situacao
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar situação: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar situação: {str(e)}")


@router.get("/health")
async def health_check():
    """Verifica conexão com o Db2"""
    try:
        # Testar com uma query simples
        result = db2_service.execute_query("SELECT 1 FROM SYSIBM.SYSDUMMY1")
        return {"status": "connected", "database": settings.db2_database, "test": "ok"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Db2 não disponível: {str(e)}")