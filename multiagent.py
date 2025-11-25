import asyncio
import os
from typing import Annotated

from agent_framework import HostedCodeInterpreterTool
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE ENTORNO ---
# Asegúrate de tener esto en tu .env o exportado
# AZURE_AI_PROJECT_ENDPOINT="tu_endpoint_foundry"
# AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o"
# AI_SEARCH_PROJECT_CONNECTION_ID="/subscriptions/.../connections/iasearchtest001freezw870h"
# AI_SEARCH_INDEX_NAME="nombre-de-tu-indice-real"

# =============================================================================
# AGENTE 1: EL EXTRACTOR (Usando tu configuración Nativa de Search)
# =============================================================================

async def run_search_worker(query: str) -> str:
    """
    Instancia un agente efímero conectado nativamente a Azure AI Search
    para recuperar datos reales sin alucinaciones.
    """
    print(f"\n[SISTEMA] Iniciando Agente Extractor para: '{query}'...")
    
    instructions = """
    Eres el Agente de Recuperación de Datos de Tecpetrol.
    Tu ÚNICA función es buscar información en los documentos indexados.
    Cita siempre las fuentes como: `[doc_id†source]`.
    No interpretes, solo entrega la información cruda encontrada.
    """

    # Definición de la Tool tal cual la proporcionaste en tu ejemplo funcional
    search_tool_config = {
        "type": "azure_ai_search",
        "azure_ai_search": {
            "indexes": [
                {
                    "project_connection_id": os.environ["AI_SEARCH_PROJECT_CONNECTION_ID"],
                    "index_name": os.environ["AI_SEARCH_INDEX_NAME"],
                    "query_type": "vector", # O 'vector' si tu índice tiene vectores
                }
            ]
        },
    }

    async with AzureCliCredential() as credential:
        async with AzureAIClient(async_credential=credential).create_agent(
            name="Tecpetrol-Search-Worker",
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=search_tool_config, # <--- Tu configuración nativa aquí
        ) as agent:
            # Ejecutamos la consulta y devolvemos el resultado textual al orquestador
            response = await agent.run(query)
            return str(response.message.content)

# =============================================================================
# AGENTE 2: EL AUDITOR (Analista Matemático con Python)
# =============================================================================

async def run_audit_worker(contexto_financiero: str, tarea_calculo: str) -> str:
    """
    Instancia un agente efímero con Code Interpreter para validar números.
    """
    print(f"\n[SISTEMA] Iniciando Agente Auditor con Python Sandbox...")
    
    instructions = """
    Eres el Auditor Cuantitativo.
    Recibirás texto con datos financieros.
    TU TAREA:
    1. Escribe y ejecuta código Python para extraer los números del texto.
    2. Realiza los cálculos solicitados (sumas, márgenes, variaciones).
    3. Compara tus resultados con lo que dice el texto.
    4. Si hay discrepancia, repórtalo como "ANOMALÍA DETECTADA".
    """
    
    prompt_completo = f"""
    CONTEXTO (Datos extraídos):
    {contexto_financiero}
    
    TAREA DE CÁLCULO:
    {tarea_calculo}
    """

    async with AzureCliCredential() as credential:
        async with AzureAIClient(async_credential=credential).create_agent(
            name="Tecpetrol-Math-Auditor",
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            instructions=instructions,
            tools=HostedCodeInterpreterTool(), # <--- Python Sandbox real
        ) as agent:
            response = await agent.run(prompt_completo)
            return str(response.message.content)

# =============================================================================
# HERRAMIENTAS DEL ORQUESTADOR (Wrappers)
# =============================================================================

async def tool_consultar_datos(
    tema: Annotated[str, Field(description="El tema financiero a buscar (ej: 'EBITDA Q3 2025').")]
) -> str:
    """Llama al Agente Extractor para buscar en documentos reales."""
    return await run_search_worker(tema)

async def tool_auditar_datos(
    datos_texto: Annotated[str, Field(description="El texto con los datos financieros encontrados.")],
    calculo_requerido: Annotated[str, Field(description="Instrucción de qué validar (ej: 'Recalcular margen EBITDA').")]
) -> str:
    """Llama al Agente Auditor para ejecutar Python y verificar cifras."""
    return await run_audit_worker(datos_texto, calculo_requerido)

# =============================================================================
# AGENTE 3: EL ORQUESTADOR
# =============================================================================

async def main() -> None:
    print("=== SISTEMA MULTI-AGENTE FINANCIERO (Orquestador + RAG Nativo + Python) ===")

    orquestador_instructions = """
    Eres el Gerente de Finanzas de Tecpetrol.
    Tu objetivo es responder consultas complejas coordinando a tu equipo.
    
    TU EQUIPO (TOOLS):
    1. `tool_consultar_datos`: Úsalo para obtener información REAL de Azure AI Search.
    2. `tool_auditar_datos`: Úsalo SIEMPRE que obtengas números para verificar que sean consistentes.
    
    FLUJO DE TRABAJO:
    1. Analiza la pregunta.
    2. Pide los datos al Extractor.
    3. Envía esos datos al Auditor para que recalcule las métricas clave.
    4. Si el Auditor detecta una anomalía, avisa al usuario. Si no, presenta el resultado validado.
    """

    async with AzureCliCredential() as credential:
        async with AzureAIClient(async_credential=credential).create_agent(
            name="Tecpetrol-Orquestador",
            model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
            instructions=orquestador_instructions,
            tools=[tool_consultar_datos, tool_auditar_datos],
        ) as orquestador:
            
            # --- CONSULTA DE PRUEBA ---
            user_query = "Dime la información financiera del tercer trimestre de 2025. Verifica matemáticamente si las sumas de ingresos o costos cuadran con el resultado operativo."
            
            print(f"Usuario: {user_query}")
            print("Orquestador pensando... (Esto puede tomar unos segundos mientras coordina a los agentes)\n")
            
            # Usamos run_stream para ver la respuesta final generándose
            async for chunk in orquestador.run_stream(user_query):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n")

if __name__ == "__main__":
    asyncio.run(main())