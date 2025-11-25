import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent_framework.azure import AzureAIClient
from azure.identity.aio import AzureCliCredential, DefaultAzureCredential
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="Agente Financiero API")

class QueryRequest(BaseModel):
    query: str

@app.post("/ask")
async def ask_agent(request: QueryRequest):
    try:
        # Configuración de la herramienta de búsqueda
        search_tool_definition = {
            "type": "azure_ai_search",
            "azure_ai_search": {
                "indexes": [
                    {
                        "project_connection_id": os.environ.get("AI_SEARCH_PROJECT_CONNECTION_ID"),
                        "index_name": os.environ.get("AI_SEARCH_INDEX_NAME"),
                        "query_type": "vector", 
                    }
                ]
            },
        }

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

        # Usar DefaultAzureCredential para soportar tanto desarrollo local (CLI) como producción (Managed Identity)
        async with DefaultAzureCredential() as credential:
            async with AzureAIClient(async_credential=credential).create_agent(
                name="AgenteFinancieroTecpetrol", 
                model=os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4o"),
                instructions=financial_persona,
                tools=search_tool_definition,
            ) as agent:
                
                result = await agent.run(request.query)
                return {"response": str(result)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
