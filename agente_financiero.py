# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración basada en sus comentarios (Idealmente, mantenga esto en el archivo .env)
# AI_SEARCH_PROJECT_CONNECTION_ID="/subscriptions/ca42bd88.../connections/iasearchtest001freezw870h"

async def main() -> None:
    # Definición de la Herramienta de Búsqueda (RAG)
    # Configuramos el agente para usar su índice específico de Azure AI Search
    search_tool_definition = {
        "type": "azure_ai_search",
        "azure_ai_search": {
            "indexes": [
                {
                    # ID de conexión al recurso de búsqueda dentro del proyecto Foundry
                    "project_connection_id": os.environ.get("AI_SEARCH_PROJECT_CONNECTION_ID"),
                    "index_name": os.environ.get("AI_SEARCH_INDEX_NAME"),
                    # 'vector' es ideal para búsquedas semánticas financieras complejas
                    "query_type": "vector", 
                }
            ]
        },
    }

    # Instrucciones Especializadas (Persona Financiera)
    # Definimos reglas estrictas para evitar alucinaciones en datos sensibles.
    financial_persona = """
    Eres un Analista Financiero Senior experto en recuperación de información corporativa.
    Tu objetivo es extraer datos financieros precisos (Ingresos, EBITDA, Q3, Costos, etc.) 
    exclusivamente de los documentos proporcionados por la herramienta de búsqueda.

    REGLAS OPERATIVAS:
    1. Precisión Extrema: No asumas valores. Si el documento dice "1.2M", no digas "alrededor de un millón".
    2. Citas Obligatorias: Cada afirmación financiera debe tener una cita en formato: `[doc_id†source]`.
    3. Honestidad Intelectual: Si la información del "tercer trimestre de 2025" no está en los documentos, 
       responde: "No encontré información específica sobre ese periodo en la base de conocimiento".
    4. Contexto: Al responder sobre trimestres (Q3), verifica siempre el año fiscal en el documento fuente.
    """

    print(f"[SISTEMA] Iniciando Agente Financiero con Azure AI Search...")

    async with AzureCliCredential() as credential:
        # Creación del Agente utilizando el cliente de Azure AI Foundry
        async with AzureAIClient(async_credential=credential).create_agent(
            name="AgenteFinancieroTecpetrol2", 
            model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o"),
            instructions=financial_persona,
            tools=search_tool_definition,
        ) as agent:
            
            # Consulta de prueba específica financiera
            query = "Qué información tienes de tecpetrol sobre su desempeño financiero en el tercer trimestre?"
            
            print(f"\n[USUARIO]: {query}")
            print(f"[AGENTE]: Procesando búsqueda en índice '{os.environ.get('AI_SEARCH_INDEX_NAME')}'...\n")
            
            # Ejecución del agente
            result = await agent.run(query)
            
            # Presentación del resultado
            print(f"[RESPUESTA]:\n{result}")

if __name__ == "__main__":
    # Validación previa de variables críticas para AgentOps
    required_vars = ["AZURE_AI_PROJECT_ENDPOINT", "AI_SEARCH_PROJECT_CONNECTION_ID", "AI_SEARCH_INDEX_NAME"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        raise EnvironmentError(f"Faltan variables de entorno críticas para el agente: {missing}")
        
    asyncio.run(main())