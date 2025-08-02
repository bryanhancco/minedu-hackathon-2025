from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import sys
import os
import json
import re

# Agregar el directorio rag al path para importar funciones de RAG
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rag'))

from bd.dto import (
    EstudianteCreate, RespuestaCreate, TemaBasico, TemaDetallado,
    PreguntaResponse, RespuestaEstudianteResponse, EstudianteCreateResponse,
    TipoPreguntaEnum, GradoEnum, PersonajeResponse, InvestigadorResponse,
    EstudianteResponse, EstudianteUpdate, PreguntaTemporal, SexoEnum
)
from bd.bd_supabase import supabase
from datetime import datetime

try:
    from execute_rag import execute_rag_for_query
    print("[DEBUG] execute_rag_for_query importado exitosamente")
except ImportError as e:
    print(f"[ERROR] Error importando execute_rag_for_query: {e}")
    execute_rag_for_query = None
    
grado_translate = {
    "1er": "Primer Grado",
    "2do": "Segundo Grado",
    "3er": "Tercer Grado",
    "4to": "Cuarto Grado",
    "5to": "Quinto Grado",
    "6to": "Sexto Grado",
}

app = FastAPI(title="MINEDU RAG API", description="API para sistema educativo MINEDU", version="1.0.0")

# Configurar directorio de archivos estáticos para imágenes
images_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
if os.path.exists(images_directory):
    app.mount("/images", StaticFiles(directory=images_directory), name="images")
    print(f"[INFO] Directorio de imágenes configurado: {images_directory}")
else:
    print(f"[WARNING] Directorio de imágenes no encontrado: {images_directory}")

@app.get("/getTodosTemas", response_model=List[TemaBasico])
async def get_todos_temas(grado: GradoEnum):
    """
    Obtiene todos los temas de un grado específico
    """
    try:
        response = supabase.table("tema").select("nombre, descripcion, imagen").eq("grado", grado.value).execute()
        
        if not response.data:
            return []
        
        temas = []
        for tema in response.data:
            temas.append(TemaBasico(
                tema=tema["nombre"],
                descripcion=tema["descripcion"],
                imagen=tema["imagen"]
            ))
        
        return temas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/getTemaEspecifico", response_model=TemaDetallado)
async def get_tema_especifico(grado: GradoEnum, id_tema: int):
    """
    Obtiene un tema específico con sus personajes e investigadores
    """
    try:
        # Obtener tema
        tema_response = supabase.table("tema").select("nombre, descripcion, imagen").eq("grado", grado.value).eq("id", id_tema).execute()
        
        if not tema_response.data:
            raise HTTPException(status_code=404, detail="Tema no encontrado")
        
        tema_data = tema_response.data[0]
        
        # Obtener personajes
        personajes_response = supabase.table("personaje").select("nombre, descripcion, imagen").eq("id_tema", id_tema).execute()
        personajes = []
        if personajes_response.data:
            for personaje in personajes_response.data:
                personajes.append(PersonajeResponse(
                    nombre=personaje["nombre"],
                    descripcion=personaje["descripcion"],
                    imagen=personaje["imagen"]
                ))
        
        # Obtener investigadores
        investigadores_response = supabase.table("investigador").select("nombres, sexo, descripcion, es_provincia, enlace_renacyt, area, imagen").eq("id_tema", id_tema).execute()
        investigadores = []
        if investigadores_response.data:
            for investigador in investigadores_response.data:
                investigadores.append(InvestigadorResponse(
                    nombres=investigador["nombres"],
                    sexo=investigador["sexo"],
                    descripcion=investigador["descripcion"],
                    es_provincia=investigador["es_provincia"],
                    enlace_renacyt=investigador["enlace_renacyt"],
                    area=investigador["area"],
                    imagen=investigador["imagen"]
                ))
        
        return TemaDetallado(
            tema=tema_data["nombre"],
            descripcion=tema_data["descripcion"],
            imagen=tema_data["imagen"],
            personajes=personajes,
            investigadores=investigadores
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/getAllPreguntas", response_model=List[PreguntaResponse])
async def get_all_preguntas(tipo: TipoPreguntaEnum, id_tipo: str, id_estudiante: int):
    """
    Obtiene todas las preguntas de un tipo específico con estado basado en si el estudiante las respondió correctamente
    """
    try:
        # Obtener todas las preguntas del tipo especificado
        preguntas_response = supabase.table("pregunta").select("id, pregunta, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_correcta").eq("tipo", tipo.value).eq("id_tipo", id_tipo).execute()
        
        if not preguntas_response.data:
            return []
        
        preguntas = []
        for pregunta in preguntas_response.data:
            # Verificar si el estudiante respondió correctamente esta pregunta AL MENOS UNA VEZ
            # (puede haber múltiples respuestas incorrectas, pero si al menos una es correcta, estado = True)
            respuesta_correcta = supabase.table("respuesta").select("id").eq("id_pregunta", pregunta["id"]).eq("id_estudiante", id_estudiante).eq("resultado", True).execute()
            
            # El estado es True si existe al menos una respuesta correcta para esta pregunta
            # Sin importar cuántas respuestas incorrectas haya tenido antes
            estado_respondida_correctamente = len(respuesta_correcta.data) > 0
            
            preguntas.append(PreguntaResponse(
                pregunta=pregunta["pregunta"],
                alternativa_a=pregunta["alternativa_a"],
                alternativa_b=pregunta["alternativa_b"],
                alternativa_c=pregunta["alternativa_c"],
                alternativa_d=pregunta["alternativa_d"],
                alternativa_correcta=pregunta["alternativa_correcta"],
                estado=estado_respondida_correctamente
            ))
        
        return preguntas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/getPreguntasPaginado", response_model=List[PreguntaResponse])
async def get_preguntas_paginado(tipo: TipoPreguntaEnum, id_tipo: str, paginado: int = Query(..., ge=1), id_estudiante: int = Query(...)):
    """
    Obtiene preguntas paginadas de un tipo específico con estado basado en si el estudiante las respondió correctamente
    """
    try:
        # Configurar paginación (10 preguntas por página)
        page_size = 5
        offset = (paginado - 1) * page_size
        
        # Obtener preguntas paginadas del tipo especificado
        preguntas_response = supabase.table("pregunta").select("id, pregunta, alternativa_a, alternativa_b, alternativa_c, alternativa_d, alternativa_correcta").eq("tipo", tipo.value).eq("id_tipo", id_tipo).range(offset, offset + page_size - 1).execute()
        
        if not preguntas_response.data:
            return []
        
        preguntas = []
        for pregunta in preguntas_response.data:
            # Verificar si el estudiante respondió correctamente esta pregunta AL MENOS UNA VEZ
            # (puede haber múltiples respuestas incorrectas, pero si al menos una es correcta, estado = True)
            respuesta_correcta = supabase.table("respuesta").select("id").eq("id_pregunta", pregunta["id"]).eq("id_estudiante", id_estudiante).eq("resultado", True).execute()
            
            # El estado es True si existe al menos una respuesta correcta para esta pregunta
            # Sin importar cuántas respuestas incorrectas haya tenido antes
            estado_respondida_correctamente = len(respuesta_correcta.data) > 0
            
            preguntas.append(PreguntaResponse(
                pregunta=pregunta["pregunta"],
                alternativa_a=pregunta["alternativa_a"],
                alternativa_b=pregunta["alternativa_b"],
                alternativa_c=pregunta["alternativa_c"],
                alternativa_d=pregunta["alternativa_d"],
                alternativa_correcta=pregunta["alternativa_correcta"],
                estado=estado_respondida_correctamente
            ))
        
        return preguntas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/getAllRespuestas", response_model=List[RespuestaEstudianteResponse])
async def get_all_respuestas(id_estudiante: int):
    """
    Obtiene todas las respuestas de un estudiante específico
    """
    try:
        # Hacer join entre Respuesta y Pregunta para obtener el texto de la pregunta
        response = supabase.table("respuesta").select("id_pregunta, resultado, tiempo_inicio_pregunta, tiempo_envio_respuesta, Pregunta(pregunta)").eq("id_estudiante", id_estudiante).execute()
        
        if not response.data:
            return []
        
        respuestas = []
        for respuesta in response.data:
            # Calcular duración en segundos
            inicio = datetime.fromisoformat(respuesta["tiempo_inicio_pregunta"].replace('Z', '+00:00'))
            envio = datetime.fromisoformat(respuesta["tiempo_envio_respuesta"].replace('Z', '+00:00'))
            duracion = int((envio - inicio).total_seconds())
            
            respuestas.append(RespuestaEstudianteResponse(
                id_pregunta=respuesta["id_pregunta"],
                pregunta=respuesta["Pregunta"]["pregunta"],
                resultado=respuesta["resultado"],
                duracion=duracion
            ))
        
        return respuestas
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/enviarRespuesta")
async def enviar_respuesta(respuesta: RespuestaCreate):
    """
    Envía una respuesta de un estudiante
    """
    try:
        response = supabase.table("respuesta").insert({
            "id_pregunta": respuesta.id_pregunta,
            "id_estudiante": respuesta.id_estudiante,
            "resultado": respuesta.resultado,
            "tiempo_inicio_pregunta": respuesta.tiempo_inicio_pregunta.isoformat(),
            "tiempo_envio_respuesta": respuesta.tiempo_envio_respuesta.isoformat()
        }).execute()
        
        if response.data:
            return JSONResponse(content={"message": "Respuesta enviada exitosamente"}, status_code=201)
        else:
            raise HTTPException(status_code=400, detail="Error al enviar la respuesta")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/registrarEstudiante", response_model=EstudianteCreateResponse)
async def registrar_estudiante(estudiante: EstudianteCreate):
    """
    Registra un nuevo estudiante
    """
    try:
        response = supabase.table("estudiante").insert({
            "nombre": estudiante.nombre,
            "sexo": estudiante.sexo.value,
            "grado": estudiante.grado.value
        }).execute()
        
        if response.data:
            nuevo_id = response.data[0]["id"]
            return EstudianteCreateResponse(id=nuevo_id)
        else:
            raise HTTPException(status_code=400, detail="Error al registrar el estudiante")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/listarTodosEstudiantes", response_model=List[EstudianteResponse])
async def listar_todos_estudiantes():
    """
    Obtiene todos los estudiantes registrados
    """
    try:
        response = supabase.table("estudiante").select("id, nombre, sexo, grado").execute()
        
        if not response.data:
            return []
        
        estudiantes = []
        for estudiante in response.data:
            estudiantes.append(EstudianteResponse(
                id=estudiante["id"],
                nombre=estudiante["nombre"],
                sexo=estudiante["sexo"],
                grado=estudiante["grado"]
            ))
        
        return estudiantes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/listarEstudiantesFiltrados", response_model=List[EstudianteResponse])
async def listar_estudiantes_filtrados(
    grado: Optional[GradoEnum] = Query(None, description="Filtrar por grado"),
    sexo: Optional[SexoEnum] = Query(None, description="Filtrar por sexo")
):
    """
    Obtiene estudiantes filtrados por grado y/o sexo
    """
    try:
        query = supabase.table("estudiante").select("id, nombre, sexo, grado")
        
        if grado:
            query = query.eq("grado", grado.value)
        
        if sexo:
            query = query.eq("sexo", sexo.value)
        
        response = query.execute()
        
        if not response.data:
            return []
        
        estudiantes = []
        for estudiante in response.data:
            estudiantes.append(EstudianteResponse(
                id=estudiante["id"],
                nombre=estudiante["nombre"],
                sexo=estudiante["sexo"],
                grado=estudiante["grado"]
            ))
        
        return estudiantes
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/getDatosEstudiante/{id_estudiante}", response_model=EstudianteResponse)
async def get_datos_estudiante(id_estudiante: int):
    """
    Obtiene los datos de un estudiante específico
    """
    try:
        response = supabase.table("estudiante").select("id, nombre, sexo, grado").eq("id", id_estudiante).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        estudiante_data = response.data[0]
        
        return EstudianteResponse(
            id=estudiante_data["id"],
            nombre=estudiante_data["nombre"],
            sexo=estudiante_data["sexo"],
            grado=estudiante_data["grado"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.put("/actualizarDatosEstudiante/{id_estudiante}", response_model=EstudianteResponse)
async def actualizar_datos_estudiante(id_estudiante: int, estudiante_update: EstudianteUpdate):
    """
    Actualiza los datos de un estudiante específico
    """
    try:
        # Verificar que el estudiante existe
        existing_response = supabase.table("estudiante").select("id").eq("id", id_estudiante).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Actualizar datos
        response = supabase.table("estudiante").update({
            "nombre": estudiante_update.nombre,
            "sexo": estudiante_update.sexo.value,
            "grado": estudiante_update.grado.value
        }).eq("id", id_estudiante).execute()
        
        if response.data:
            estudiante_actualizado = response.data[0]
            return EstudianteResponse(
                id=estudiante_actualizado["id"],
                nombre=estudiante_actualizado["nombre"],
                sexo=estudiante_actualizado["sexo"],
                grado=estudiante_actualizado["grado"]
            )
        else:
            raise HTTPException(status_code=400, detail="Error al actualizar el estudiante")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.delete("/eliminarEstudiante/{id_estudiante}")
async def eliminar_estudiante(id_estudiante: int):
    """
    Elimina un estudiante específico
    """
    try:
        # Verificar que el estudiante existe
        existing_response = supabase.table("estudiante").select("id").eq("id", id_estudiante).execute()
        
        if not existing_response.data:
            raise HTTPException(status_code=404, detail="Estudiante no encontrado")
        
        # Eliminar estudiante
        response = supabase.table("estudiante").delete().eq("id", id_estudiante).execute()
        
        if response.data:
            return JSONResponse(content={"message": "Estudiante eliminado exitosamente"}, status_code=200)
        else:
            raise HTTPException(status_code=400, detail="Error al eliminar el estudiante")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/")
async def root():
    """
    Endpoint de salud de la API
    """
    return {"message": "MINEDU RAG API funcionando correctamente"}

@app.get("/images/list")
async def listar_imagenes():
    """
    Lista todas las imágenes disponibles en el directorio de imágenes
    """
    try:
        images_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), "images")
        
        if not os.path.exists(images_directory):
            raise HTTPException(status_code=404, detail="Directorio de imágenes no encontrado")
        
        # Extensiones de imagen permitidas
        extensiones_permitidas = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico'}
        
        imagenes = []
        for archivo in os.listdir(images_directory):
            if os.path.isfile(os.path.join(images_directory, archivo)):
                nombre, extension = os.path.splitext(archivo)
                if extension.lower() in extensiones_permitidas:
                    imagenes.append({
                        "nombre": archivo,
                        "url": f"/images/{archivo}",
                        "nombre_sin_extension": nombre,
                        "extension": extension
                    })
        
        return {
            "total": len(imagenes),
            "directorio": images_directory,
            "imagenes": imagenes
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Endpoint de diagnóstico para verificar la conexión a la base de datos
    """
    try:
        # Intentar una consulta simple para verificar la conexión
        response = supabase.table("tema").select("count", count="exact").execute()
        
        return {
            "status": "OK",
            "database": "Connected",
            "tables_accessible": True,
            "message": "Conexión a Supabase exitosa"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "database": "Failed",
            "tables_accessible": False,
            "error": str(e),
            "message": "Error de conexión a Supabase"
        }

@app.post("/generarNuevasPreguntas", response_model=List[PreguntaTemporal])
async def generar_nuevas_preguntas(
    tipo: TipoPreguntaEnum,
    id_tipo: str,
    cantidad: int = Query(..., ge=1, le=10, description="Cantidad de preguntas a generar (máximo 10)")
):
    """
    Genera nuevas preguntas temporales usando RAG (no se almacenan en base de datos)
    """
    try:
        # Verificar que la función RAG esté disponible
        if execute_rag_for_query is None:
            raise HTTPException(status_code=503, detail="Servicio de generación de preguntas no disponible. Verifique que el módulo RAG esté instalado correctamente.")
        
        # Obtener información del tipo según el enumerador
        if tipo == TipoPreguntaEnum.TEMA:
            # Buscar el tema en la base de datos
            tema_response = supabase.table("tema").select("nombre, descripcion, grado").eq("id", id_tipo).execute()
            if not tema_response.data:
                raise HTTPException(status_code=404, detail="Tema no encontrado")
            
            tema_data = tema_response.data[0]
            query_context = f"Ciencia y Tecnología - {grado_translate[tema_data['grado']]} - {tema_data['nombre']}"
            
        elif tipo == TipoPreguntaEnum.PERSONAJE:
            # Buscar el personaje en la base de datos
            personaje_response = supabase.table("personaje").select("nombre, descripcion").eq("id", id_tipo).execute()
            if not personaje_response.data:
                raise HTTPException(status_code=404, detail="Personaje no encontrado")
            
            personaje_data = personaje_response.data[0]
            query_context = f"Personaje - {personaje_data['nombre']} - {personaje_data['descripcion']}"
            
        elif tipo == TipoPreguntaEnum.INVESTIGADOR:
            # Buscar el investigador en la base de datos
            investigador_response = supabase.table("investigador").select("nombres, descripcion, area").eq("id", id_tipo).execute()
            if not investigador_response.data:
                raise HTTPException(status_code=404, detail="Investigador no encontrado")
            
            investigador_data = investigador_response.data[0]
            query_context = f"Investigador - {investigador_data['nombres']} - {investigador_data['area']}"
        
        # Construir la query para RAG
        rag_query = f"{query_context} - {cantidad} preguntas"
        
        print(f"[DEBUG] Ejecutando RAG con query: {rag_query}")
        
        # Ejecutar RAG para generar preguntas
        try:
            rag_output = execute_rag_for_query(rag_query)
            print(f"[DEBUG] RAG output recibido: {str(rag_output)[:200]}...")
        except Exception as rag_error:
            print(f"[ERROR] Error en execute_rag_for_query: {str(rag_error)}")
            raise HTTPException(status_code=500, detail=f"Error ejecutando RAG: {str(rag_error)}")
        
        if not rag_output:
            raise HTTPException(status_code=500, detail="RAG no devolvió ningún resultado")
        
        # Parsear la salida del RAG para extraer preguntas
        try:
            preguntas_temporales = parse_rag_output_to_questions(str(rag_output), cantidad)
            print(f"[DEBUG] Se parsearon {len(preguntas_temporales)} preguntas")
        except Exception as parse_error:
            print(f"[ERROR] Error parseando RAG output: {str(parse_error)}")
            raise HTTPException(status_code=500, detail=f"Error procesando respuesta RAG: {str(parse_error)}")
        
        if not preguntas_temporales:
            raise HTTPException(status_code=500, detail="No se pudieron extraer preguntas del resultado de RAG")
        
        return preguntas_temporales
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

def parse_rag_output_to_questions(rag_output: str, cantidad: int) -> List[PreguntaTemporal]:
    """
    Parsea la salida del RAG para extraer preguntas en formato PreguntaTemporal
    El RAG puede devolver JSON o texto plano
    """
    try:
        preguntas = []
        rag_text = str(rag_output).strip()
        
        print(f"[DEBUG] Parseando RAG output de {len(rag_text)} caracteres")
        
        # Intentar primero con formato JSON
        json_start = rag_text.find('[')
        json_end = rag_text.rfind(']') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = rag_text[json_start:json_end]
            try:
                preguntas_data = json.loads(json_str)
                print(f"[DEBUG] JSON parseado exitosamente con {len(preguntas_data)} preguntas")
                
                for i, pregunta_json in enumerate(preguntas_data):
                    if i >= cantidad:
                        break
                        
                    pregunta_texto = pregunta_json.get('pregunta', f'Pregunta {i+1}')
                    alt_a = pregunta_json.get('alternativa_A', 'Opción A')
                    alt_b = pregunta_json.get('alternativa_B', 'Opción B')
                    alt_c = pregunta_json.get('alternativa_C', 'Opción C')
                    alt_d = pregunta_json.get('alternativa_D', 'Opción D')
                    alternativa_correcta = pregunta_json.get('alternativa_correcta', 1)
                    
                    # Validar alternativa_correcta
                    if not isinstance(alternativa_correcta, int) or alternativa_correcta < 1 or alternativa_correcta > 4:
                        alternativa_correcta = 1
                    
                    pregunta_temporal = PreguntaTemporal(
                        pregunta=pregunta_texto,
                        alternativa_a=alt_a,
                        alternativa_b=alt_b,
                        alternativa_c=alt_c,
                        alternativa_d=alt_d,
                        alternativa_correcta=alternativa_correcta
                    )
                    
                    preguntas.append(pregunta_temporal)
                
                if preguntas:
                    print(f"[DEBUG] Extraídas {len(preguntas)} preguntas del JSON")
                    return preguntas[:cantidad]
                    
            except json.JSONDecodeError as e:
                print(f"[DEBUG] Error decodificando JSON: {e}, intentando con patrones de texto")
        
        # Si JSON falló, intentar con patrones de texto
        print("[DEBUG] Intentando parseado con patrones de texto...")
        
        # Patrón más flexible para texto
        patron_pregunta = r'(\d+)\.?\s*(.+?)\n\s*[Aa]\)\s*(.+?)\n\s*[Bb]\)\s*(.+?)\n\s*[Cc]\)\s*(.+?)\n\s*[Dd]\)\s*(.+?)(?:\n.*?(?:Respuesta|Correcta?).*?([1-4ABCD]))?'
        
        matches = re.findall(patron_pregunta, rag_text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        
        for match in matches[:cantidad]:
            if len(match) >= 6:
                numero, pregunta_texto, alt_a, alt_b, alt_c, alt_d = match[:6]
                respuesta_correcta = match[6] if len(match) > 6 else '1'
                
                # Convertir respuesta correcta a número
                if respuesta_correcta.upper() in ['A', '1']:
                    alternativa_correcta = 1
                elif respuesta_correcta.upper() in ['B', '2']:
                    alternativa_correcta = 2
                elif respuesta_correcta.upper() in ['C', '3']:
                    alternativa_correcta = 3
                elif respuesta_correcta.upper() in ['D', '4']:
                    alternativa_correcta = 4
                else:
                    alternativa_correcta = 1
                
                pregunta_temporal = PreguntaTemporal(
                    pregunta=pregunta_texto.strip(),
                    alternativa_a=alt_a.strip(),
                    alternativa_b=alt_b.strip(),
                    alternativa_c=alt_c.strip(),
                    alternativa_d=alt_d.strip(),
                    alternativa_correcta=alternativa_correcta
                )
                
                preguntas.append(pregunta_temporal)
        
        if preguntas:
            print(f"[DEBUG] Extraídas {len(preguntas)} preguntas con patrones de texto")
            return preguntas[:cantidad]
        
        # Si nada funcionó, crear preguntas básicas como último recurso
        print("[DEBUG] No se pudieron extraer preguntas, generando preguntas básicas")
        for i in range(cantidad):
            pregunta_basica = PreguntaTemporal(
                pregunta=f"Pregunta {i+1} sobre el tema solicitado",
                alternativa_a="Opción A",
                alternativa_b="Opción B",
                alternativa_c="Opción C",
                alternativa_d="Opción D",
                alternativa_correcta=1
            )
            preguntas.append(pregunta_basica)
        
        return preguntas
        
    except Exception as e:
        print(f"[ERROR] Error en parse_rag_output_to_questions: {str(e)}")
        # Generar preguntas de emergencia
        return [
            PreguntaTemporal(
                pregunta=f"Pregunta temporal {i+1}",
                alternativa_a="Opción A",
                alternativa_b="Opción B",
                alternativa_c="Opción C",
                alternativa_d="Opción D",
                alternativa_correcta=1
            ) for i in range(cantidad)
        ]

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
