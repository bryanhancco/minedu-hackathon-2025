-- Enum para tipo de pregunta
CREATE TYPE tipo_pregunta_enum AS ENUM ('Tema', 'Personaje', 'Investigador');
CREATE TYPE area_enum AS ENUM ('Ciencia y Tecnologia', 'Matematica');
CREATE TYPE sexo_enum AS ENUM ('Femenino', 'Masculino');
CREATE TYPE grado_enum AS ENUM ('1er', '2do', '3er', '4to', '5to', '6to');

CREATE TABLE Tema (
    id SERIAL PRIMARY KEY,
    area area_enum NOT NULL,
    grado grado_enum NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    descripcion VARCHAR(255),
    imagen VARCHAR(255)
);

CREATE TABLE Personaje (
    id SERIAL PRIMARY KEY,
    id_tema INTEGER NOT NULL REFERENCES Tema(id) ON DELETE CASCADE,
    nombre VARCHAR(255) NOT NULL,
    descripcion VARCHAR(255),
    imagen VARCHAR(255)
);

CREATE TABLE Investigador (
    id SERIAL PRIMARY KEY,
    id_tema INTEGER NOT NULL REFERENCES Tema(id) ON DELETE CASCADE,
    nombres VARCHAR(255) NOT NULL,
    sexo sexo_enum NOT NULL,
    descripcion VARCHAR(255),
    es_provincia BOOLEAN,
    enlace_renacyt VARCHAR(255),
    area VARCHAR(255),
    imagen VARCHAR(255)
);

CREATE TABLE Estudiante (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    sexo sexo_enum NOT NULL,
    grado grado_enum NOT NULL
);

CREATE TABLE Pregunta (
    id SERIAL PRIMARY KEY,
    tipo tipo_pregunta_enum NOT NULL,
    id_tipo VARCHAR(255) NOT NULL,
    pregunta VARCHAR(255) NOT NULL,
    alternativa_A VARCHAR(255),
    alternativa_B VARCHAR(255),
    alternativa_C VARCHAR(255),
    alternativa_D VARCHAR(255),
    alternativa_correcta INTEGER CHECK (alternativa_correcta BETWEEN 1 AND 4)
);

CREATE TABLE Respuesta (
    id SERIAL PRIMARY KEY,
    id_pregunta INTEGER NOT NULL REFERENCES Pregunta(id) ON DELETE CASCADE,
    id_estudiante INTEGER NOT NULL REFERENCES Estudiante(id) ON DELETE CASCADE,
    resultado BOOLEAN,
    tiempo_inicio_pregunta TIMESTAMP,
    tiempo_envio_respuesta TIMESTAMP
);

