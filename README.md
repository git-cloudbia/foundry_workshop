# Agente Financiero Tecpetrol

Este proyecto implementa un Agente Financiero impulsado por IA que utiliza Azure AI Foundry y Azure AI Search para proporcionar información financiera precisa y contextualizada. El agente está diseñado para actuar como un Analista Financiero Senior, extrayendo datos de documentos corporativos indexados.

> Referencias: 
> - Juan Ignacio Etcheberry Mason https://www.linkedin.com/in/juan-ignacio-etcheberry-mason/
> - Microsoft Agent Framework Quick-Start Guide: https://learn.microsoft.com/en-us/agent-framework/tutorials/quick-start?pivots=programming-language-python
> - Microsoft Foundry SDKs and Endpoints: https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/sdk-overview?view=foundry-classic&pivots=programming-language-python
> - Azure AI Agent Examples: https://github.com/microsoft/agent-framework/blob/main/python/samples/getting_started/agents/azure_ai/README.md

## Características

*   **Búsqueda Semántica (RAG):** Utiliza Azure AI Search para recuperar documentos relevantes basados en consultas en lenguaje natural.
*   **Persona Especializada:** Configurado como un experto financiero que prioriza la precisión, las citas obligatorias y la honestidad intelectual.
*   **API REST:** Expone una interfaz API a través de FastAPI para integrar el agente en otras aplicaciones.
*   **Soporte de Despliegue:** Listo para ser desplegado en Azure Container Apps.

## Requisitos Previos

*   Python 3.9+
*   Cuenta de Azure con acceso a Azure AI Foundry y Azure AI Search.
*   Variables de entorno configuradas (ver `agente_financiero.py` y `deployment_guide.md`).

## Instalación

1.  Clona el repositorio:
    ```bash
    git clone <url-del-repositorio>
    cd <nombre-del-directorio>
    ```

2.  Crea un entorno virtual e instala las dependencias:
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  Configura las variables de entorno:
    Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:
    ```env
    AZURE_AI_PROJECT_ENDPOINT="<tu-endpoint-de-proyecto>"
    AI_SEARCH_PROJECT_CONNECTION_ID="<id-conexion-search>"
    AI_SEARCH_INDEX_NAME="<nombre-indice-search>"
    AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4o" # Opcional, por defecto gpt-4o
    ```

## Uso

### Ejecución Local (CLI)

Para ejecutar el agente directamente en la terminal:

```bash
python agente_financiero.py
```

### Ejecución de la API (FastAPI)

Para iniciar el servidor de la API:

```bash
uvicorn app:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`. Puedes acceder a la documentación interactiva en `http://127.0.0.1:8000/docs`.

#### Ejemplo de solicitud a la API:

```bash
curl -X POST "http://127.0.0.1:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "¿Cuáles fueron los ingresos del Q3?"}'
```

## Estructura del Proyecto

*   `agente_financiero.py`: Script principal que define la lógica del agente y permite la ejecución en CLI.
*   `app.py`: Aplicación FastAPI que expone el agente como un servicio web.
*   `deployment_guide.md`: Guía detallada para el despliegue en Azure.
*   `requirements.txt`: Lista de dependencias del proyecto.

## Despliegue

Consulta el archivo [deployment_guide.md](deployment_guide.md) para obtener instrucciones detalladas sobre cómo desplegar este agente en Azure Container Apps.
