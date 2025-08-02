# MINEDU RAG API

API REST para el sistema educativo MINEDU que integra RAG (Retrieval-Augmented Generation) para generar preguntas educativas.

## Instalación

1. Instalar dependencias:
```bash
pip install -r requirements.txt
```

2. Configurar variables de entorno:
```bash
# Crear archivo .env con:
SUPABASE_URL=tu_supabase_url
SUPABASE_API_KEY=tu_supabase_api_key
GOOGLE_API_KEY=tu_google_api_key
```

3. Ejecutar la API:
```bash
python run_api.py
```

4. **Verificar conexión a Supabase:**
```bash
# Testear la conexión
GET http://localhost:8000/health
```

> **⚠️ Problema de conexión?** Si obtienes errores de "relation does not exist", revisa el archivo `SOLUCION_SUPABASE.md` para resolver problemas de RLS y permisos.

La API estará disponible en: http://localhost:8000

## Documentación

Una vez ejecutada la API, puedes acceder a:
- Documentación interactiva: http://localhost:8000/docs
- Documentación alternativa: http://localhost:8000/redoc

## Endpoints

### GET /getTodosTemas
Obtiene todos los temas de un grado específico.
- **Parámetros**: `grado` (1er, 2do, 3er, 4to, 5to, 6to)
- **Respuesta**: Lista de temas con nombre, descripción e imagen

### GET /getTemaEspecifico
Obtiene un tema específico con sus personajes e investigadores.
- **Parámetros**: `grado`, `id_tema`
- **Respuesta**: Tema detallado con personajes e investigadores asociados

### GET /getAllPreguntas
Obtiene todas las preguntas de un tipo específico.
- **Parámetros**: `tipo` (Tema, Personaje, Investigador), `id_tipo`, `id_estudiante`
- **Respuesta**: Lista de preguntas con alternativas, respuesta correcta y estado (si el estudiante la respondió correctamente)

### GET /getPreguntasPaginado
Obtiene preguntas paginadas de un tipo específico.
- **Parámetros**: `tipo`, `id_tipo`, `paginado` (número de página), `id_estudiante`
- **Respuesta**: Lista paginada de preguntas (10 por página) con estado basado en respuestas del estudiante

### GET /getAllRespuestas
Obtiene todas las respuestas de un estudiante específico.
- **Parámetros**: `id_estudiante`
- **Respuesta**: Lista de respuestas con duración y resultado

### POST /enviarRespuesta
Envía una respuesta de un estudiante.
- **Body**: Objeto Respuesta con id_pregunta, id_estudiante, resultado, tiempos
- **Respuesta**: Código 201 si es exitoso

### POST /registrarEstudiante
Registra un nuevo estudiante.
- **Body**: Objeto Estudiante con nombre, sexo, grado
- **Respuesta**: ID del estudiante creado

## Estructura del Proyecto

```
MINEDU/
├── api/
│   └── api.py              # Endpoints de la API
├── bd/
│   ├── dto.py              # Modelos Pydantic
│   ├── bd_supabase.py      # Conexión a Supabase
│   ├── tables.sql          # Esquema de base de datos
│   ├── inserts.sql         # Datos de prueba
│   └── usp.sql             # Procedimientos almacenados
├── rag/
│   ├── process_data.py     # Procesamiento de PDFs
│   ├── execute_rag.py      # Ejecución de RAG
│   ├── loaders.py          # Cargadores de documentos
│   └── helper_utils.py     # Utilidades
├── files/                  # Archivos PDF educativos
├── chroma_storage/         # Base de datos vectorial
├── requirements.txt        # Dependencias
└── run_api.py             # Ejecutor de la API
```

## Base de Datos

La API utiliza Supabase como base de datos PostgreSQL con las siguientes tablas:
- **Tema**: Temas educativos por área y grado
- **Personaje**: Personajes asociados a temas
- **Investigador**: Investigadores asociados a temas
- **Estudiante**: Estudiantes registrados
- **Pregunta**: Preguntas generadas por RAG
- **Respuesta**: Respuestas de estudiantes a preguntas

## Integración RAG

El sistema utiliza:
- **ChromaDB**: Base de datos vectorial para almacenar embeddings de documentos PDF
- **Google Generative AI**: Para generar preguntas educativas contextualmente relevantes
- **LangChain**: Para orquestar el pipeline RAG

## Uso

1. Procesar documentos PDF educativos ejecutando `rag/process_data.py`
2. Ejecutar la API con `python run_api.py`
3. Usar los endpoints para obtener temas, preguntas y gestionar estudiantes
4. Generar preguntas personalizadas usando el sistema RAG integrado

## Deploy en Render

Para desplegar en Render como web service:

### 1. Configuración en Render Dashboard:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn api.api:app --host 0.0.0.0 --port $PORT`
- **Environment**: Python 3
- **Instance Type**: Free tier o superior

### 2. Variables de entorno requeridas:
```bash
SUPABASE_URL=tu_supabase_url
SUPABASE_API_KEY=tu_supabase_service_key
GOOGLE_API_KEY=tu_google_api_key
```

### 3. Archivos incluidos para Render:
- ✅ `Procfile` - Comando de inicio
- ✅ `runtime.txt` - Versión de Python
- ✅ `start.sh` - Script de inicio alternativo
- ✅ `package.json` - Metadatos del proyecto

### 4. URL de la API desplegada:
- Base URL: `https://tu-app.onrender.com`
- Documentación: `https://tu-app.onrender.com/docs`
- Health check: `https://tu-app.onrender.com/health`
