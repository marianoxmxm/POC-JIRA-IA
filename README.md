
# Smart ITSM Core - IA Local para Jira Service Management

## 1. Contexto y Problemática Operativa
Las organizaciones enfrentan ineficiencias críticas derivadas de la gestión manual de incidentes sobre **Jira Service Management Data Center**:

* **Despacho Lento y Erróneo:** La clasificación inicial de los tickets depende del criterio humano expuesto a fatiga y diferencias de conocimiento técnico, provocando asignaciones incorrectas a los grupos de soporte (*Infraestructura, Redes, IAM, Aplicaciones*), retrabajo y un alto índice de rebote de tickets.
* **Dependencia del Conocimiento Individual:** La calidad de la derivación disminuye drásticamente si los analistas más experimentados no están disponibles para realizar el triaje inicial.
* **Cuellos de Botella por Información Precaria:** Un volumen masivo de tickets ingresa con descripciones vacías o ambiguas (ej: *"no funciona"*, *"da error"*). Esto detiene el flujo operativo, forzando a un analista técnico a formular repreguntas manuales y esperar respuestas, aumentando exponencialmente el MTTR (Mean Time to Resolution).

### La Solución
Este proyecto propone un **Orquestador de IA On-Premise (Costo $0)** desacoplado de Jira, diseñado bajo una arquitectura guiada por eventos. Su objetivo es automatizar el triaje y la interacción con el usuario mediante modelos de lenguaje locales (SLMs), garantizando privacidad absoluta de los datos de la organizacion.

---

## 2. Visión del Proyecto y Roadmap Evolutivo

El sistema está diseñado para madurar de forma progresiva en tres niveles de capacidad técnica:

```
  +--------------------------------------------------------+
  |  NIVEL 1: MVP - Clasificación e Ingesta Asincrónica     | -> [ESTADO: IMPLEMENTADO]
  |  - Extracción y análisis de Summary + Description.      |
  |  - Determinación de Categoría y Grupo de Soporte.       |
  |  - Cálculo de Umbral de Confianza (Thresholding).       |
  +--------------------------------------------------------+
                             │
                             ▼
  +--------------------------------------------------------+
  |  NIVEL 2: Enriquecimiento e Interacción Automática     | -> [ESTADO: EN PLANIFICACIÓN]
  |  - Evaluación de completitud del ticket mediante LLM.  |
  |  - Detección de tickets vacíos o con datos precarios.  |
  |  - Repregunta automatizada y cambio de estado en Jira.  |
  +--------------------------------------------------------+
                             │
                             ▼
  +--------------------------------------------------------+
  |  NIVEL 3: Diagnóstico Avanzado y Auto-Resolución       | -> [ESTADO: BACKLOG]
  |  - Motor RAG (Búsqueda semántica de casos históricos). |
  |  - Sugerencia de remediación para el técnico.          |
  |  - Resolución automática vía ejecución de scripts/APIs. |
  +--------------------------------------------------------+

```

### Objetivos por Nivel

#### Nivel 1: Clasificación Inteligente (MVP)

* **Objetivo:** Mitigar el retraso de despacho y la dependencia de conocimiento individual.
* **Mecanismo:** El modelo analiza el payload del ticket entrante, infiere la categoría y calcula un porcentaje de confianza. Si supera el umbral configurado ($> 0.80$), el ticket se auto-rutea. Si es menor, se marca para revisión manual del Service Desk.

#### Nivel 2: Detección y Enriquecimiento de Tickets Precarios

* **Objetivo:** Eliminar el tiempo muerto causado por tickets sin información técnica útil.
* **Mecanismo:** Si el ticket es catalogado como ambiguo, el sistema bloquea el escalamiento a niveles técnicos superiores, pasa el ticket automáticamente a un estado intermedio (*"En Espera de Información"*) e inyecta un comentario estructurado exigiendo los datos mínimos requeridos según la categoría inferida.

#### Nivel 3: Diagnóstico por Similitud y Auto-Resolución (Closed-Loop)

* **Objetivo:** Automatizar la resolución de casos repetitivos e incidentes masivos.
* **Mecanismo:** Implementación de una base de datos vectorial para buscar incidentes similares históricos. Para solicitudes estándar (ej: reseteo de claves corporativas), el sistema invoca *endpoints* e interfaces internas para resolver el problema de raíz sin intervención humana.

---

## 3. Estructura del Repositorio

```text
smart-itsm-core/
├── app/
│   ├── __init__.py
│   └── main.py             # Lógica del Orquestador FastAPI y Prompt Engineering
├── docker-compose.yml      # Orquestación de infraestructura local (Ollama + API)
├── Dockerfile              # Construcción y provisión de herramientas del contenedor (Python + Curl)
├── entrypoint.sh           # Script de control de inicialización y descarga automática de modelos
└── requirements.txt        # Dependencias de software core de Python

```

---

## 4. Arquitectura y Componentes Tecnológicos

La arquitectura se ejecuta de manera local y aislada para respetar restricciones corporativas on-premise:

1. **Jira Data Center Webhooks:** Intercepta el evento `IssueCreated` y despacha un HTTP POST asincrónico con los campos estructurados.
2. **Orquestador (FastAPI / Python 3.11):** Recibe las cargas de trabajo, centraliza las reglas de negocio y maneja los tiempos de espera (*timeouts*) de inferencia en CPU.
3. **Motor de Inferencia Local (Ollama):** Servidor local que aloja y expone los pesos del modelo de lenguaje.
4. **Modelo de Lenguaje (Llama 3.2 3B):** Modelo liviano optimizado para inferencia determinista (Temperatura 0.0) ejecutada directamente sobre la CPU del host.

---

## 5. Requisitos de Infraestructura

* **Sistema Operativo:** Linux (Kali Linux, Debian, Ubuntu o RHEL) con soporte Docker nativo.
* **Motor Docker:** Docker Engine v20.10+ y Docker Compose v2+.
* **Hardware Mínimo para PoC:** 4 Cores CPU dedicados al contenedor y 8 GB de memoria RAM disponibles de forma exclusiva para el proceso de inferencia.

---

## 6. Despliegue del Entorno (Paso a Paso)

### 1. Preparación del Host Linux

Asegúrate de tener el demonio de Docker corriendo y configurado para iniciarse con el sistema operativo:

```bash
sudo systemctl enable docker --now

```

### 2. Construcción de Imágenes e Inicio

Desde la raíz del proyecto ejecute el siguiente comando para compilar el orquestador (descargando e inyectando `curl` internamente) y encender el ecosistema:

```bash
sudo docker-compose build && sudo docker-compose up

```

*El script `entrypoint.sh` controlará que Ollama esté disponible y descargará el modelo de 2.0GB de forma automatizada. Al visualizar `Uvicorn running on http://0.0.0.0:8000`, la API estará lista.*

---

## 7. Protocolo de Pruebas y Validación de Inferencia

Abre una terminal secundaria en el host Kali Linux y ejecuta las siguientes solicitudes HTTP para validar la consistencia lógica del Nivel 1 y la preparación para el Nivel 2:

### Caso A: Entrada de Datos Insuficientes (Preparación Nivel 2)

```bash
curl -X POST http://localhost:8000/analizar-ticket \
-H "Content-Type: application/json" \
-d '{
  "issue_key": "INC-101",
  "summary": "No anda la app",
  "description": "Hola, necesito ayuda porque no me anda nada cuando quiero entrar."
}'

```

### Caso B: Entrada de Datos Suficientes para Auto-Ruteo (Nivel 1 Exitoso)

```bash
curl -X POST http://localhost:8000/analizar-ticket \
-H "Content-Type: application/json" \
-d '{
  "issue_key": "INC-102",
  "summary": "Error de login - Cuenta bloqueada en Active Directory",
  "description": "Al intentar ingresar a mi puesto de trabajo me sale un cartel que dice que superé el número máximo de intentos fallidos. Solicito el desbloqueo de mi usuario corporativo y reseteo de clave."
}'

```

---

## 8. Gobierno de Datos, Privacidad y Seguridad

* **Inferencia Local:** Los datos contenidos en el resumen y descripción de los incidentes se procesan exclusivamente dentro del espacio de memoria asignado en el host local. No hay llamadas a APIs de nube pública de terceros (OpenAI, Anthropic, etc.).
* **Aislamiento de Red:** El contenedor de Ollama no expone puertos hacia el exterior de la máquina si no se requiere, comunicándose únicamente con el orquestador mediante la red puente interna de Docker.

## 9. Licencia y Contacto

* **Licencia:** Distribuido bajo los términos de la Licencia [MIT](https://www.google.com/search?q=LICENSE).


