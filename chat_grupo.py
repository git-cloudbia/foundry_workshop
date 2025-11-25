import os
import asyncio
from agent_framework import ChatAgent, GroupChatBuilder, WorkflowOutputEvent, AgentRunUpdateEvent
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential, DefaultAzureCredential
from agent_framework import FileCheckpointStorage # Necesario para persistencia
# from agent_framework.observability import setup_observability # Comentado para evitar errores si no hay servidor OTLP
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# 1. Configuración de AgentOps: Observabilidad
# NOTA: Solo descomente la siguiente línea si tiene un servidor OTLP (como Aspire Dashboard) corriendo en el puerto 4317.
# De lo contrario, generará los errores de conexión que experimentó[cite: 3279].
# setup_observability(otlp_endpoint="http://localhost:4317")

async def main():
    # 2. Configuración del Cliente del Modelo
    # Usamos DefaultAzureCredential para mayor flexibilidad en autenticación local/nube[cite: 4190].
    client = AzureOpenAIChatClient(credential=DefaultAzureCredential())

    # 3. Definición de Agentes Especializados
    # Agente 1: Investigador [cite: 4044]
    researcher = ChatAgent(
        name="Researcher",
        chat_client=client,
        instructions="Eres un investigador experto. Tu trabajo es buscar hechos concretos y datos sobre el tema solicitado. Sé breve y preciso."
    )

    # Agente 2: Escritor [cite: 4044]
    writer = ChatAgent(
        name="Writer",
        chat_client=client,
        instructions="Eres un redactor creativo. Tomas los datos del investigador y creas narrativa atractiva. No inventes hechos, usa lo que te da el investigador."
    )

    # Agente 3: Revisor [cite: 4044]
    reviewer = ChatAgent(
        name="Reviewer",
        chat_client=client,
        instructions="Eres un editor estricto. Revisas el texto del Escritor. Si faltan datos, pide al Investigador. Si el texto es aburrido, pide al Escritor que mejore. Aprueba solo cuando sea perfecto."
    )

    # 4. Construcción del Flujo de Trabajo
    # Utilizamos un gestor basado en prompts para orquestar dinámicamente los turnos[cite: 4428].
    checkpoint_storage = FileCheckpointStorage(storage_path="/app/data/checkpoints")

    workflow = (
        GroupChatBuilder()
        .set_prompt_based_manager(
            chat_client=client,
            display_name="Coordinator",
            instructions="Coordina la conversación..."
        )
        .participants([researcher, writer, reviewer])
        .with_max_rounds(12)
        .with_checkpointing(checkpoint_storage) # <--- HABILITAR PERSISTENCIA [cite: 4562]
        .build()
    )

    # 5. Ejecución del Flujo de Trabajo
    print(f"Iniciando orquestación de Chat Grupal compleja...")
    task_input = "Investiga sobre el impacto de la computación cuántica en la criptografía y escribe un resumen breve."

    # Se utiliza 'run_stream' para procesamiento en tiempo real[cite: 4055].
    async for event in workflow.run_stream(task_input):
        # Manejo del resultado final
        if isinstance(event, WorkflowOutputEvent):
            # CORRECCIÓN: Accedemos al contenido del mensaje en lugar de imprimir el objeto
            # Dependiendo de la estructura exacta del mensaje final, accedemos a .text o iteramos el contenido.
            final_data = event.data
            if hasattr(final_data, 'text'):
                print(f"\n[RESULTADO FINAL]: {final_data.text}")
            else:
                print(f"\n[RESULTADO FINAL (Raw)]: {final_data}")

        # Manejo de streaming de tokens y actualizaciones de agentes
        elif hasattr(event, 'data') and hasattr(event, 'source'):
             # Filtramos para mostrar solo texto relevante y evitar ruido excesivo
             data_str = str(event.data)
             if "text=" in data_str: 
                 # Extracción simple para log de depuración
                 print(f"[{event.source} Activo] Procesando...")

if __name__ == "__main__":
    asyncio.run(main())