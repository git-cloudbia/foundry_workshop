import os
import asyncio
from typing import Annotated, Any, Dict, List

# Importaciones del Framework MAF
from agent_framework import (
    ChatAgent, 
    SequentialBuilder, 
    WorkflowOutputEvent, 
    AgentRunUpdateEvent,    
    ai_function
)
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework import HostedCodeInterpreterTool
from azure.identity import DefaultAzureCredential, AzureCliCredential
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN ---
# Asegúrese de que las variables de entorno estén cargadas
ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

# =============================================================================
# 1. DEFINICIÓN DE HERRAMIENTAS (TOOLS)
# =============================================================================

# En MAF, definimos la búsqueda como una @ai_function para tipado seguro
# y fácil integración con el agente[cite: 4061].
@ai_function
async def search_tecpetrol_docs(query: str) -> str:
    """
    Busca información financiera y operativa en los documentos indexados de Tecpetrol.
    Utiliza Azure AI Search para recuperar fragmentos relevantes.
    """
    # NOTA: Aquí simulamos la llamada a la API de Search nativa usando la config que proveíste.
    # En un entorno real, usarías SearchClient de azure-search-documents o la integración nativa.
    # Para este ejemplo de Workflow, retornamos datos simulados para demostrar el flujo,
    # ya que la conexión real requiere el cliente de Search instanciado.
    
    print(f"\n[TOOL SEARCH] Buscando: {query}...")
    
    # Simulación de respuesta de Azure AI Search (RAG)
    return """
    [RESULTADOS DE BÚSQUEDA]
    Documento: Reporte_Q3_2025.pdf
    - Ingresos Operativos: $1,200 M
    - Costos Operativos: $850 M
    - Resultado Operativo Reportado: $350 M
    - Margen EBITDA estimado: 35%
    """

# =============================================================================
# 2. CONFIGURACIÓN DEL FLUJO DE TRABAJO
# =============================================================================

async def main():
    print("=== INICIANDO WORKFLOW SECUENCIAL: EXTRACTOR -> AUDITOR ===\n")

    # Inicialización del cliente de modelo (Azure OpenAI)
    # Usamos DefaultAzureCredential para autenticación segura y sin llaves
    client = AzureOpenAIChatClient(
        model_id=DEPLOYMENT,
        azure_endpoint=ENDPOINT,
        credential=AzureCliCredential() # O DefaultAzureCredential()
    )

    # --- AGENTE 1: EL EXTRACTOR ---
    # Este agente solo tiene la herramienta de búsqueda.
    extractor_agent = ChatAgent(
        name="Extractor",
        chat_client=client,
        instructions=(
            "Eres el Agente de Recuperación de Datos. "
            "Tu única tarea es buscar la información solicitada usando 'search_tecpetrol_docs'. "
            "No calcules nada, solo devuelve la información cruda encontrada."
        ),
        tools=[search_tecpetrol_docs]
    )

    # --- AGENTE 2: EL AUDITOR ---
    # Este agente recibe el contexto del anterior y tiene Code Interpreter.
    auditor_agent = ChatAgent(
        name="Auditor",
        chat_client=client,
        instructions=(
            "Eres el Auditor Cuantitativo. "
            "Analiza la información proporcionada por el agente anterior. "
            "Usa Python para verificar matemáticamente si las cifras cuadran (ej: Ingresos - Costos = Resultado). "
            "Reporta si el cálculo coincide con el reporte o si hay anomalías."
        ),
        tools=[HostedCodeInterpreterTool()] # Sandbox de Python nativo
    )

    # --- CONSTRUCCIÓN DEL WORKFLOW ---
    # Usamos SequentialBuilder para encadenar los agentes.
    # El flujo es: Usuario -> Extractor (Busca) -> Auditor (Verifica) -> Salida Final.
    workflow = (
        SequentialBuilder()
        .participants([extractor_agent, auditor_agent])
        .build()
    )

    # =========================================================================
    # 3. EJECUCIÓN
    # =========================================================================
    
    user_query = "Dime la información financiera del Q3 2025 y verifica si los costos e ingresos cuadran con el resultado."
    
    print(f"Usuario: {user_query}\n")

    # Ejecución en streaming para observar el pensamiento de los agentes
    async for event in workflow.run_stream(user_query):
        
        # Capturamos la salida parcial de los agentes (Pensamiento/Tokens)
        if isinstance(event, AgentRunUpdateEvent):
            # Imprimimos el nombre del agente y el contenido generado
            if event.data.text:
                print(f"[{event.source}]: {event.data.text}", end="", flush=True)
        
        # Capturamos la salida final del workflow
        elif isinstance(event, WorkflowOutputEvent):
            print(f"\n\n[WORKFLOW FINALIZADO]:\n{event.data}")

if __name__ == "__main__":
    asyncio.run(main())