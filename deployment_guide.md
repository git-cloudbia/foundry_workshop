# Guía de Despliegue - Agente Financiero

Esta guía detalla cómo ejecutar el Agente Financiero en un entorno local de desarrollo y cómo desplegarlo en producción utilizando Azure Container Apps.

## Prerrequisitos

- Docker instalado.
- Azure CLI instalado (`az login`).
- Un recurso de Azure AI Foundry y Azure AI Search configurados.
- Variables de entorno definidas en un archivo `.env` (ver `agente_financiero.py` para las variables requeridas).

## Desarrollo Local

1.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Ejecutar el servidor de desarrollo:**
    ```bash
    uvicorn app:app --reload
    ```

3.  **Probar el agente:**
    Abre tu navegador en `http://127.0.0.1:8000/docs` para usar la interfaz Swagger UI.
    O usa `curl`:
    ```bash
    curl -X POST "http://127.0.0.1:8000/ask" -H "Content-Type: application/json" -d '{"query": "¿Cuáles fueron los ingresos del Q3?"}'
    ```

## Despliegue en Producción (Azure Container Apps)

### 1. Construir la Imagen Docker

```bash
docker build -t agente-financiero:v1 .
```

### 2. Probar el Contenedor Localmente

```bash
docker run --env-file .env -p 8000:8000 agente-financiero:v1
```

### 3. Subir a Azure Container Registry (ACR)

Asumiendo que ya tienes un ACR creado:

```bash
az acr login --name {{ACR_NAME}}
docker tag agente-financiero:v1 {{ACR_REGISTRY}}/agente-financiero:v1
docker push {{ACR_REGISTRY}}/agente-financiero:v1
```

### 4. Desplegar en Azure Container Apps

Puedes hacerlo desde el portal de Azure o usando la CLI:

```bash
### 4. Desplegar en Azure Container Apps

Para que Container Apps pueda descargar la imagen, necesitamos habilitar el usuario administrador en el ACR (para entornos de desarrollo) o configurar una identidad gestionada.

**Opción A: Usando credenciales de administrador (Más rápido para Dev)**

1.  Habilitar usuario admin:
    ```bash
    az acr update -n acrfoundryde001 --admin-enabled true
    ```

2.  Obtener contraseña:
    ```bash
    az acr credential show --name acrfoundryde001 --query "passwords[0].value" -o tsv
    ```

3.  Crear la Container App (Reemplaza `{{ACR_PASSWORD}}` con el valor obtenido):
        ```bash
        az containerapp create \
            --name {{CONTAINERAPP_NAME}} \
            --resource-group {{RESOURCE_GROUP}} \
            --image {{ACR_REGISTRY}}/agente-financiero:v1 \
            --environment {{CONTAINERAPPS_ENVIRONMENT}} \
            --ingress external \
            --target-port 8000 \
            --registry-server {{ACR_REGISTRY}} \
            --registry-username {{ACR_USERNAME}} \
            --registry-password {{ACR_PASSWORD}} \
            --env-vars \
                AI_SEARCH_PROJECT_CONNECTION_ID={{AI_SEARCH_PROJECT_CONNECTION_ID}} \
                AI_SEARCH_INDEX_NAME={{AI_SEARCH_INDEX_NAME}} \
                AZURE_AI_PROJECT_ENDPOINT={{AZURE_AI_PROJECT_ENDPOINT}} \
                AZURE_AI_MODEL_DEPLOYMENT_NAME={{AZURE_AI_MODEL_DEPLOYMENT_NAME}}
        ```
```

    ```

### 5. Configurar Identidad Gestionada y Permisos

El error `DefaultAzureCredential failed` ocurre porque la Container App no tiene identidad para autenticarse contra los servicios de Azure AI.

1.  **Habilitar Identidad Gestionada (System Assigned):**
    ```bash
    az containerapp identity assign -n {{CONTAINERAPP_NAME}} -g {{RESOURCE_GROUP}} --system-assigned
    ```
    *Copia el `principalId` que aparece en la salida JSON (p. ej. `{{PRINCIPAL_ID}}`).*

2.  **Asignar Roles (RBAC):**
    Necesitas dar permisos a esa identidad sobre tus recursos. Reemplaza `<PRINCIPAL_ID>` con el ID copiado en el paso anterior.

    *   **Permiso sobre el Proyecto Azure AI Foundry:**
        (Rol: `Azure AI Project Contributor` para permitir crear agentes)
        ```bash
        az role assignment create --assignee {{PRINCIPAL_ID}} --role "Contributor" --scope /subscriptions/{{SUBSCRIPTION_ID}}/resourceGroups/{{RESOURCE_GROUP}}/providers/Microsoft.CognitiveServices/accounts/{{AZURE_COGNITIVE_ACCOUNT}}

        az role assignment create --assignee {{PRINCIPAL_ID}} --role "User IA Agent" --scope /subscriptions/{{SUBSCRIPTION_ID}}/resourceGroups/{{RESOURCE_GROUP}}/providers/Microsoft.CognitiveServices/accounts/{{AZURE_COGNITIVE_ACCOUNT}}
        ```

    *   **Permiso sobre Azure AI Search:**
        (Rol: `Search Index Data Reader` y `Search Service Contributor`)
        ```bash
        az role assignment create --assignee {{PRINCIPAL_ID}} --role "Search Index Data Reader" --scope /subscriptions/{{SUBSCRIPTION_ID}}/resourceGroups/{{RESOURCE_GROUP}}/providers/Microsoft.Search/searchServices/{{SEARCH_SERVICE_NAME}}
        ```
