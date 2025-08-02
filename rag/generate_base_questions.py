# generate_base_questions.py
import sys
import os
import json
import re
from datetime import datetime

# Agregar el directorio rag al path para importar execute_rag
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from execute_rag import execute_rag_for_query

# Definir todos los temas por grado para Ciencia y Tecnología
TEMAS_CIENCIA_TECNOLOGIA = {
    "Primer Grado": [
        "Reconocemos las plantas como seres vivos",
        "Compartimos lo que sabemos sobre los animales",
        "Aprendemos sobre los alimentos y la función de nutrición",
        "Reconocemos los objetos como materia y experimentamos sus estados y mezclas",
        "Comprendemos que el sol es fuente de luz y calor",
        "Descubrimos que las fuerzas están presentes en las personas y en los animales",
        "Exploramos nuestro planeta Tierra",
        "Conocemos las funciones de relación y de reproducción"
    ],
    "Segundo Grado": [
        "Estudiamos las plantas y sus partes",
        "Conocemos los animales, su hábitat y su ciclo de vida",
        "Estudiamos los alimentos y la función de nutrición",
        "Comprendemos las propiedades de la materia y las mezclas",
        "Averiguamos sobre la energía y sus fuentes",
        "Experimentamos los efectos de la aplicación de las fuerzas en los objetos",
        "Conocemos la Tierra y sus movimientos",
        "Estudiamos las funciones de relación y reproducción"
    ],
    "Tercer Grado": [
        "Conocemos las plantas y su ciclo de vida",
        "Conocemos los animales invertebrados",
        "Reconocemos los alimentos y la función de nutrición",
        "Identificamos los materiales, sus tipos y su utilidad",
        "Estudiamos las formas de energía y el magnetismo",
        "Estudiamos las fuerzas y el movimiento",
        "Estudiamos cómo la Tierra produce recursos naturales",
        "Comprendemos las funciones de relación y reproducción"
    ],
    "Cuarto Grado": [
        "Exploramos los factores de crecimiento y las funciones de las plantas",
        "Sabemos más sobre los animales vertebrados",
        "Conocemos los alimentos y la función de nutrición",
        "Conocemos las propiedades de la materia",
        "Aprendemos sobre la energía, sus efectos y sus transformaciones",
        "Aprendemos sobre las fuerzas y las máquinas simples",
        "Aprendemos sobre la Tierra y el sistema solar",
        "Conocemos las funciones de relación y reproducción"
    ],
    "Quinto Grado": [
        "Hablamos sobre las plantas, su reproducción y su relación con el medio",
        "Conocemos los animales y su relación con el medio",
        "Conocemos los alimentos y la función de nutrición",
        "Conocemos los estados y los cambios de estado de la materia",
        "Conocemos la energía luminosa, sus características, propiedades y usos",
        "Conocemos las máquinas simples y las máquinas compuestas",
        "Conocemos los planetas que acompañan a la Tierra",
        "Conocemos las funciones de relación y reproducción"
    ],
    "Sexto Grado": [
        "Aprendemos sobre la diversidad de plantas que hay en el Perú",
        "Conocemos la diversidad de animales en el Perú",
        "Indagamos sobre los alimentos y la nutrición",
        "Exploramos los cambios de la materia",
        "Comprendemos el calor y el sonido como manifestaciones de la energía",
        "Aprendemos sobre las máquinas y los objetos tecnológicos de nuestro departamento",
        "Indagamos sobre la Tierra en el universo y su dinámica",
        "Conocemos las funciones de relación y de reproducción"
    ]
}

def clean_text_for_sql(text):
    """Limpia el texto para evitar problemas en SQL"""
    if text is None:
        return "NULL"
    # Escapar comillas simples
    text = text.replace("'", "''")
    # Limpiar caracteres especiales que pueden causar problemas
    text = text.replace("\n", " ").replace("\r", " ")
    # Limitar longitud para VARCHAR(255)
    if len(text) > 250:
        text = text[:247] + "..."
    return f"'{text}'"

def extract_json_from_response(response_text):
    """Extrae el JSON de la respuesta del LLM"""
    try:
        # Buscar el JSON en la respuesta (puede estar entre backticks o no)
        json_match = re.search(r'(\[.*?\])', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        else:
            # Intentar parsear toda la respuesta como JSON
            return json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error parseando JSON: {e}")
        print(f"Respuesta recibida: {response_text[:500]}...")
        return None

def generate_questions_for_all_topics():
    """Genera preguntas para todos los temas y crea el archivo SQL"""
    
    sql_inserts = []
    sql_inserts.append("-- Inserciones generadas automáticamente para la tabla Pregunta")
    sql_inserts.append(f"-- Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_inserts.append("-- Tipo: Tema, Área: Ciencia y Tecnología")
    sql_inserts.append("")
    
    id_tipo = 1  # Contador para id_tipo
    total_questions = 0
    
    for grado, temas in TEMAS_CIENCIA_TECNOLOGIA.items():
        print(f"\n=== Procesando {grado} ===")
        
        for tema in temas:
            print(f"\nGenerando preguntas para: {tema}")
            
            # Construir la query para el RAG
            query = f"Ciencia y Tecnología - {grado} - {tema} - 5 preguntas"
            
            try:
                # Ejecutar RAG para obtener las preguntas
                response = execute_rag_for_query(query)
                
                if response:
                    # Extraer JSON de la respuesta
                    questions_data = extract_json_from_response(str(response))
                    
                    if questions_data and isinstance(questions_data, list):
                        print(f"✅ Generadas {len(questions_data)} preguntas para: {tema}")
                        
                        # Generar INSERTs para cada pregunta
                        for question in questions_data:
                            if all(key in question for key in ['pregunta', 'alternativa_A', 'alternativa_B', 'alternativa_C', 'alternativa_D', 'alternativa_correcta']):
                                
                                sql_insert = f"""INSERT INTO Pregunta (tipo, id_tipo, pregunta, alternativa_A, alternativa_B, alternativa_C, alternativa_D, alternativa_correcta) VALUES (
    'Tema',
    '{id_tipo}',
    {clean_text_for_sql(question['pregunta'])},
    {clean_text_for_sql(question['alternativa_A'])},
    {clean_text_for_sql(question['alternativa_B'])},
    {clean_text_for_sql(question['alternativa_C'])},
    {clean_text_for_sql(question['alternativa_D'])},
    {question['alternativa_correcta']}
);"""
                                sql_inserts.append(sql_insert)
                                total_questions += 1
                            else:
                                print(f"⚠️ Pregunta con formato incorrecto: {question}")
                    else:
                        print(f"❌ No se pudieron extraer preguntas para: {tema}")
                        # Agregar comentario en el SQL sobre el error
                        sql_inserts.append(f"-- ERROR: No se pudieron generar preguntas para '{tema}' (ID: {id_tipo})")
                else:
                    print(f"❌ No se recibió respuesta para: {tema}")
                    sql_inserts.append(f"-- ERROR: Sin respuesta para '{tema}' (ID: {id_tipo})")
                    
            except Exception as e:
                print(f"❌ Error procesando '{tema}': {str(e)}")
                sql_inserts.append(f"-- ERROR: Excepción al procesar '{tema}' (ID: {id_tipo}): {str(e)}")
            
            # Incrementar id_tipo para el siguiente tema
            id_tipo += 1
            sql_inserts.append("")  # Línea en blanco para separar temas
    
    # Escribir el archivo SQL
    output_file = "../bd/preguntas_generated.sql"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(sql_inserts))
        
        print(f"\n🎉 COMPLETADO!")
        print(f"📄 Archivo generado: {output_file}")
        print(f"📊 Total de preguntas generadas: {total_questions}")
        print(f"📚 Total de temas procesados: {id_tipo - 1}")
        
    except Exception as e:
        print(f"❌ Error escribiendo archivo: {str(e)}")

def main():
    print("🚀 Iniciando generación masiva de preguntas...")
    print("📚 Área: Ciencia y Tecnología")
    print("🎯 Grados: 1º a 6º")
    print("❓ Preguntas por tema: 5")
    print("=" * 50)
    
    generate_questions_for_all_topics()

if __name__ == "__main__":
    main()