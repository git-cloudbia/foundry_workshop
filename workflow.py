# Copyright (c) Microsoft. All rights reserved.

import asyncio

from agent_framework import AgentRunEvent, WorkflowBuilder
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential

"""
Escenario Avanzado: Pipeline de Creación de Contenido Técnico (Investigación -> Redacción -> Compliance)

Este ejemplo orquesta tres agentes especializados:
1. Researcher: Analiza el tema y extrae puntos clave técnicos.
2. Tech Writer: Redacta el artículo basándose únicamente en los hechos del investigador.
3. Compliance Officer: Valida que el contenido cumpla con las normas de seguridad y tono corporativo.

Purpose:
Demostrar una cadena de valor donde la salida de un agente se convierte en el contexto enriquecido del siguiente.
"""

async def main():
    # 1. Autenticación e Inicialización del Cliente
    # Usamos AzureCliCredential para un entorno de desarrollo seguro y estándar en Azure.
    chat_client = AzureOpenAIChatClient(credential=AzureCliCredential())

    # 2. Definición de Agentes (Segregación de Roles)

    # Agente 1: El Investigador
    # Su objetivo es "grounding" (anclar) la información antes de que se escriba nada creativo.
    researcher_agent = chat_client.create_agent(
        instructions=(
            "Eres un Investigador Técnico Senior de Azure."
            "Tu objetivo es identificar los hechos técnicos clave, especificaciones y beneficios tangibles del tema solicitado."
            "No escribas el artículo, solo genera una lista de 'Bullet Points' con datos técnicos precisos."
            "Output format: Lista concisa de hechos."
        ),
        name="researcher",
    )

    # Agente 2: El Escritor Técnico
    # Transforma los datos crudos en narrativa. Depende del input del Researcher.
    writer_agent = chat_client.create_agent(
        instructions=(
            "Eres un Escritor Técnico experto en Cloud Computing."
            "Tu tarea es tomar los puntos clave proporcionados por el investigador y redactar un borrador de blog técnico."
            "El tono debe ser profesional, directo y orientado a ingenieros."
            "Usa analogías si es necesario para explicar conceptos complejos."
        ),
        name="tech_writer",
    )

    # Agente 3: Oficial de Cumplimiento (Compliance)
    # Actúa como puerta de calidad final (Quality Gate).
    compliance_agent = chat_client.create_agent(
        instructions=(
            "Eres un Oficial de Cumplimiento y Seguridad (Compliance Officer)."
            "Revisa el borrador proporcionado por el escritor."
            "Reglas estrictas:"
            "1. Asegúrate de que no se hagan promesas de 'seguridad 100% garantizada' (imposible en seguridad)."
            "2. Verifica que el tono sea corporativo y respetuoso."
            "Si el texto pasa la revisión, responde con 'APPROVED:' seguido del texto final."
            "Si hay problemas, lista los cambios requeridos."
        ),
        name="compliance_officer",
    )

    # 3. Construcción del Workflow (Orquestación)
    # Diseñamos un flujo lineal: Researcher -> Tech Writer -> Compliance Officer
    # Esto asegura que el escritor no alucine datos (ya que recibe hechos del investigador)
    # y que nada salga sin revisión.
    workflow = (
        WorkflowBuilder()
        .set_start_executor(researcher_agent)
        .add_edge(researcher_agent, writer_agent)      # El output del Researcher pasa al Writer
        .add_edge(writer_agent, compliance_agent)      # El output del Writer pasa a Compliance
        .build()
    )

    # 4. Ejecución del Workflow
    # El prompt inicial dispara al primer nodo (Researcher).
    topic = "Explica las ventajas de usar Managed Identities en Azure para acceder a SQL Database sin credenciales."
    print(f"Iniciando Workflow para el tema: {topic}\n")
    
    events = await workflow.run(topic)

    # 5. Procesamiento de Eventos
    # Iteramos sobre los eventos para ver la traza de ejecución paso a paso.
    print(f"{'=' * 20} TRAZA DE EJECUCIÓN {'=' * 20}")
    for event in events:
        if isinstance(event, AgentRunEvent):
            # Imprimimos quién ejecutó la acción y cuál fue el resultado intermedio
            print(f"\n>>> Rol: {event.executor_id.upper()}")
            print(f"Output: {event.data}")

    print(f"\n{'=' * 60}\nResultado Final del Workflow: {events.get_outputs()}")
    print("Estado final:", events.get_final_state())

if __name__ == "__main__":
    asyncio.run(main())