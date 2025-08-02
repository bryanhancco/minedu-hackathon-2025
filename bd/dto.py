from pydantic import BaseModel
from typing import Optional, Dict, List
from enum import Enum
from datetime import datetime

# Enums
class TipoPreguntaEnum(str, Enum):
    TEMA = "Tema"
    PERSONAJE = "Personaje"
    INVESTIGADOR = "Investigador"

class AreaEnum(str, Enum):
    CIENCIA_TECNOLOGIA = "Ciencia y Tecnologia"
    MATEMATICA = "Matematica"

class SexoEnum(str, Enum):
    FEMENINO = "Femenino"
    MASCULINO = "Masculino"

class GradoEnum(str, Enum):
    PRIMERO = "1er"
    SEGUNDO = "2do"
    TERCERO = "3er"
    CUARTO = "4to"
    QUINTO = "5to"
    SEXTO = "6to"

# DTOs de entrada (requests)
class EstudianteCreate(BaseModel):
    nombre: str
    sexo: SexoEnum
    grado: GradoEnum

class RespuestaCreate(BaseModel):
    id_pregunta: int
    id_estudiante: int
    resultado: bool
    tiempo_inicio_pregunta: datetime
    tiempo_envio_respuesta: datetime

# DTOs de salida (responses)
class TemaBasico(BaseModel):
    tema: str
    descripcion: Optional[str]
    imagen: Optional[str]

class PersonajeResponse(BaseModel):
    nombre: str
    descripcion: Optional[str]
    imagen: Optional[str]

class InvestigadorResponse(BaseModel):
    nombres: str
    sexo: SexoEnum
    descripcion: Optional[str]
    es_provincia: Optional[bool]
    enlace_renacyt: Optional[str]
    area: Optional[str]
    imagen: Optional[str]

class TemaDetallado(BaseModel):
    tema: str
    descripcion: Optional[str]
    imagen: Optional[str]
    personajes: List[PersonajeResponse]
    investigadores: List[InvestigadorResponse]

class PreguntaResponse(BaseModel):
    pregunta: str
    alternativa_a: Optional[str]
    alternativa_b: Optional[str]
    alternativa_c: Optional[str]
    alternativa_d: Optional[str]
    alternativa_correcta: int
    estado: bool = False  # True si el estudiante respondió correctamente AL MENOS UNA VEZ (ignora respuestas incorrectas)

class RespuestaEstudianteResponse(BaseModel):
    id_pregunta: int
    pregunta: str
    resultado: bool
    duracion: int  # En segundos

class EstudianteCreateResponse(BaseModel):
    id: int
    message: str = "Estudiante registrado exitosamente"

class EstudianteResponse(BaseModel):
    id: int
    nombre: str
    sexo: SexoEnum
    grado: GradoEnum

class EstudianteUpdate(BaseModel):
    nombre: str
    sexo: SexoEnum
    grado: GradoEnum

class PreguntaTemporal(BaseModel):
    pregunta: str
    alternativa_a: Optional[str]
    alternativa_b: Optional[str]
    alternativa_c: Optional[str]
    alternativa_d: Optional[str]
    alternativa_correcta: int

# DTOs para respuestas de API
class ApiResponse(BaseModel):
    data: Optional[List | Dict] = None
    message: str = "Success"
    status_code: int = 200
