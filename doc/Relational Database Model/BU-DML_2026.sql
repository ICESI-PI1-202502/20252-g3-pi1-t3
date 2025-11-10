-- =========================
-- DML COMPLETO - PDF (2026-1)
-- Para PostgreSQL
-- =========================

BEGIN;

SET search_path TO public;
-- =========================
-- 1) BORRADO DE DATOS (orden seguro por FK)
-- Asegúrate de tener backups antes de ejecutar.
-- =========================
DELETE FROM clasificaciones;
DELETE FROM partidos;
DELETE FROM torneos_equipos;
DELETE FROM torneos;
DELETE FROM equipos_participantes;
DELETE FROM equipos;
DELETE FROM asistencias;
DELETE FROM participaciones;
DELETE FROM calificaciones_actividad;
DELETE FROM horarios_actividad;
DELETE FROM horarios_bloque;
DELETE FROM actividades;
DELETE FROM actividades_grupos;
DELETE FROM grupos_actividad;
DELETE FROM tipos_actividad;
DELETE FROM preferencias_actividades;
DELETE FROM preferencias;
DELETE FROM notificaciones;
DELETE FROM agenda_psicologos;
DELETE FROM citas;
DELETE FROM historial_citas;
DELETE FROM historial_participaciones;
DELETE FROM horarios_participante;
DELETE FROM inscripciones_psu;
DELETE FROM participantes;
DELETE FROM estados_asistencia;
DELETE FROM estados_participacion;
DELETE FROM estados_torneo;
DELETE FROM roles_participacion;
DELETE FROM disciplinas;
DELETE FROM grupos;
-- Nota: no borramos tablas de Django (auth_*, django_*) por seguridad.

-- =========================
-- 2) TABLAS AUXILIARES: TIPOS, GRUPOS, DISCIPLINAS, ROLES, ESTADOS
-- =========================

-- TIPOS DE ACTIVIDAD (mapping según categorías del PDF)
INSERT INTO tipos_actividad (id_tipo, nombre_tipo) OVERRIDING SYSTEM VALUE VALUES
(1, 'Artes Plásticas'),
(2, 'Artes Escénicas'),
(3, 'Artes Musicales'),
(4, 'Actividad Física y Salud'),
(5, 'Deportes de Conjunto'),
(6, 'Deportes Individuales'),
(7, 'Talleres Cortos'),
(8, 'Agenda Cultural y Deportiva');

-- GRUPOS (tabla grupos y grupos_actividad)
INSERT INTO grupos (id_grupo, nombre) VALUES
(1, 'Centro Artístico y Deportivo ICESI - CADI'), (2, 'Proyecto Social Universitario (PSU)');

-- Grupos de actividad (categorías detalladas)
INSERT INTO grupos_actividad (grupos_id_grupo, nombre, descripcion)
VALUES
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Artes Plásticas', 'Grupo general de actividades artísticas y de creatividad.'),
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Artes Escénicas', 'Baile, danza y expresión corporal.'),
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Artes Musicales', 'Clases y grupos musicales.'),
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Actividad Física y Salud', 'Actividades para la salud y condición física.'),
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Deportes de Conjunto', 'Actividades deportivas en equipo.'),
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Deportes Individuales', 'Actividades deportivas individuales.'),
((SELECT id_grupo FROM grupos WHERE nombre='Proyecto Social Universitario (PSU)'), 'Talleres Cortos', 'Talleres de corta duración.'),
((SELECT id_grupo FROM grupos WHERE nombre='Centro Artístico y Deportivo ICESI - CADI'), 'Agenda Cultural y Deportiva', 'Eventos y actividades puntuales.');

-- DISCIPLINAS (para deportes y torneos)
INSERT INTO disciplinas (nombre) VALUES
('Baloncesto'),
('Fútbol'),
('Tenis de Mesa'),
('Judo'),
('Natación'),
('Voleibol');

-- ROLES DE PARTICIPACIÓN
INSERT INTO roles_participacion (nombre) VALUES
('Asistente'),
('Instructor'),
('Representante');

-- ESTADOS (asistencia, participacion, torneo)
INSERT INTO estados_asistencia (nombre) VALUES
('Presente'),
('Ausente'),
('Justificada');

INSERT INTO estados_participacion (id_estado_participacion, nombre) OVERRIDING SYSTEM VALUE VALUES
(1, 'Inscrito'),
(2, 'Activo'),
(3, 'Retirado');

INSERT INTO estados_torneo (nombre) VALUES
('Programado'),
('En Curso'),
('Finalizado');

-- =========================
-- 3) ACTIVIDADES (todas las listadas en el PDF)
-- Insertamos con su tipo (tipos_actividad_id_tipo) y un aforo aproximado cuando aplica.
-- =========================

-- ARTES PLÁSTICAS
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Accesorios & Tejidos', 'Accesorios y tejidos - artes plásticas', 'S', 'P', 25, 1),
('Arte Fantástico', 'Arte fantástico - dibujo y pintura', 'S', 'P', 25, 1);

-- ARTES ESCÉNICAS - BAILE
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Baile (Nivel Formativo)', 'Clase de baile nivel formativo', 'S', 'P', 40, 2),
('Baile (Tango)', 'Clase de tango', 'S', 'P', 30, 2),
('Baile (Nivel Avanzado)', 'Clase de baile nivel avanzado', 'S', 'P', 40, 2),
('Baile (Grupo Representativo UNICESI BAILA)', 'Grupo representativo de baile', 'S', 'P', 40, 2),
('Danza Contemporánea (Nivel Formativo)', 'Danza contemporánea formativa', 'S', 'P', 30, 2),
('Danza Contemporánea (Nivel Avanzado)', 'Danza contemporánea avanzado', 'S', 'P', 30, 2);

-- ARTES MUSICALES (CLASES)
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Bajo', 'Clase de bajo', 'S', 'P', 15, 3),
('Guitarra Eléctrica', 'Clase de guitarra eléctrica', 'S', 'P', 15, 3),
('Piano', 'Clase de piano', 'S', 'P', 20, 3);

-- ARTES MUSICALES (GRUPOS)
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Coro', 'Grupo Coro', 'S', 'G', 30, 3),
('Grupo de Música de Cámara', 'Grupo música de cámara', 'S', 'G', 20, 3),
('Grupo de Rock', 'Grupo de Rock', 'S', 'G', 25, 3);

-- ACTIVIDAD FÍSICA Y SALUD
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Acondicionamiento FIT (Crossfit)', 'Crossfit - acondicionamiento', 'S', 'P', 40, 4),
('Entrenamiento Funcional', 'Entrenamiento funcional', 'S', 'P', 40, 4),
('Gimnasio', 'Acceso gimnasio', 'N', 'P', 200, 4);

-- DEPORTES DE CONJUNTO (Baloncesto)
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Baloncesto (Nivel Formativo)', 'Baloncesto nivel formativo', 'S', 'P', 20, 5),
('Baloncesto (Nivel Avanzado)', 'Baloncesto nivel avanzado', 'S', 'P', 20, 5);

-- FÚTBOL MASCULINO
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Fútbol Masculino (Formativo)', 'Fútbol masculino nivel formativo', 'S', 'P', 30, 5),
('Fútbol Masculino (Avanzado)', 'Fútbol masculino nivel avanzado', 'S', 'P', 30, 5);

-- DEPORTES INDIVIDUALES
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Ajedrez', 'Ajedrez', 'S', 'P', 30, 6),
('Judo', 'Judo', 'S', 'P', 25, 6),
('Natación (Formativo)', 'Natación nivel formativo', 'S', 'P', 30, 6),
('Natación (Avanzado)', 'Natación nivel avanzado', 'S', 'P', 30, 6);

-- TALLERES CORTOS
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Cerámica', 'Taller de cerámica (corto)', 'S', 'P', 20, 7),
('Voleibol Playa', 'Voleibol playa (taller corto)', 'S', 'P', 20, 7);

-- AGENDA CULTURAL Y DEPORTIVA (eventos)
INSERT INTO actividades (nombre, descripcion, requiere_inscripcion, modalidad, aforo, tipos_actividad_id_tipo)
VALUES
('Concierto BU - Acústico & Son de la U', 'Evento cultural', 'N', 'E', 500, 8),
('Concierto BU - Rock & Tambores', 'Evento cultural', 'N', 'E', 500, 8),
('Torneo Interno de Tenis de Mesa', 'Torneo interno de tenis de mesa', 'S', 'T', 50, 8);

-- =========================
-- 4) HORARIOS POR BLOQUE y HORARIOS_ACTIVIDAD
-- Usamos horarios_bloque como bloques reutilizables y horarios_actividad para días concretos.
-- dia_semana: 1=Lun ... 6=Sab
-- =========================

-- ---------- ARTES PLÁSTICAS ----------
-- Accesorios & Tejidos: MARTES 11:00 a 14:00 (203I) - profesora Margarita Gutiérrez
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Accesorios & Tejidos'), '11:00:00', '14:00:00', 'Margarita Gutiérrez', '203I');

-- Arte Fantástico: LUNES 12:00-15:00 (203I) y JUEVES 14:00-17:00 y VIERNES 12:00-15:00 (tres bloques)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico'), '12:00:00', '15:00:00', 'Javier Díaz', '203I'),
((SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico'), '14:00:00', '17:00:00', 'Javier Díaz', '203I');

-- Ahora horarios_actividad (día concreto)
-- Accesorios & Tejidos -> MARTES (2)
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Accesorios & Tejidos'),
 (SELECT id_horario_bloque FROM horarios_bloque hb WHERE hb.actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Accesorios & Tejidos') LIMIT 1),
 2, '11:00:00', '14:00:00', 'Margarita Gutiérrez', '203I');


-- Arte Fantástico -> LUNES (1), JUEVES (4), VIERNES (5)
-- Solo hay 2 bloques (12-15 y 14-17), así que usamos el primero dos veces
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
-- Lunes
((SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico'),
 (SELECT id_horario_bloque FROM horarios_bloque hb 
  WHERE hb.actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico')
  AND hora_inicio = '12:00:00' LIMIT 1),
 1, '12:00:00', '15:00:00', 'Javier Díaz', '203I'),

-- Jueves
((SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico'),
 (SELECT id_horario_bloque FROM horarios_bloque hb 
  WHERE hb.actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico')
  AND hora_inicio = '14:00:00' LIMIT 1),
 4, '14:00:00', '17:00:00', 'Javier Díaz', '203I'),

-- Viernes (mismo bloque que el lunes)
((SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico'),
 (SELECT id_horario_bloque FROM horarios_bloque hb 
  WHERE hb.actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico')
  AND hora_inicio = '12:00:00' LIMIT 1),
 5, '12:00:00', '15:00:00', 'Javier Díaz', '203I');

-- ---------- ARTES ESCÉNICAS (BAILE y DANZA) ----------
-- Baile (Nivel Formativo): MARTES 12:00-14:00 (103I) - Kevin Valencia; MIÉRCOLES 12:00-14:00 (116G)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Formativo)'), '12:00:00', '14:00:00', 'Kevin Valencia', '103I'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Formativo)'), '12:00:00', '14:00:00', 'Kevin Valencia', '116G');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque hb WHERE hb.actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Formativo)') ORDER BY id_horario_bloque LIMIT 1), 2, '12:00:00','14:00:00','Kevin Valencia','103I'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque hb WHERE hb.actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Formativo)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 3, '12:00:00','14:00:00','Kevin Valencia','116G');

-- Baile (Tango): JUEVES 12:00-14:00 (103I)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Tango)'), '12:00:00','14:00:00','Kevin Valencia','103I');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Tango)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baile (Tango)') LIMIT 1), 4, '12:00:00','14:00:00','Kevin Valencia','103I');

-- Baile (Nivel Avanzado): VIERNES 14:00-16:00 (Coliseo 2 Zona A) + Sesión especial Semana 7 (116G)
-- Guardamos ambos bloques, pero solo un registro de horario regular.

-- Bloques
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Avanzado)'), '14:00:00','16:00:00','Kevin Valencia','COLISEO 2 ZONA A'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Avanzado)'), '14:00:00','16:00:00','Kevin Valencia','116G (Semana 7)');

-- Horario regular (único registro por día y hora)
INSERT INTO horarios_actividad (
    actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar
)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Avanzado)'),
 (SELECT id_horario_bloque FROM horarios_bloque 
  WHERE actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Baile (Nivel Avanzado)')
  AND lugar='COLISEO 2 ZONA A' LIMIT 1),
 5, '14:00:00', '16:00:00', 'Kevin Valencia', 'COLISEO 2 ZONA A');


-- Baile (Grupo Representativo UNICESI BAILA): MARTES 14:00-16:00 (116G), JUEVES 14:00-17:00 (103I), VIERNES 17:00-20:00 (Coliseo 2 Zona A)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)'), '14:00:00','16:00:00','Maicol Steven Paredes','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)'), '14:00:00','17:00:00','Maicol Steven Paredes','103I'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)'), '17:00:00','20:00:00','Maicol Steven Paredes','COLISEO 2 ZONA A');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)') ORDER BY id_horario_bloque LIMIT 1), 2, '14:00:00','16:00:00','Maicol Steven Paredes','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 4, '14:00:00','17:00:00','Maicol Steven Paredes','103I'),
((SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baile (Grupo Representativo UNICESI BAILA)') ORDER BY id_horario_bloque OFFSET 2 LIMIT 1), 5, '17:00:00','20:00:00','Maicol Steven Paredes','COLISEO 2 ZONA A');

-- Danza Contemporánea (Formativo): MARTES 16:00-18:00, JUEVES 16:00-18:00 (116G) - Angelly Betancourth
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Formativo)'), '16:00:00','18:00:00','Angelly Betancourth','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Avanzado)'), '18:00:00','20:00:00','Angelly Betancourth','116G');

-- Insert horarios_actividad for Danza Contemporánea
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Formativo)') LIMIT 1), 2, '16:00:00','18:00:00','Angelly Betancourth','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Formativo)') LIMIT 1), 4, '16:00:00','18:00:00','Angelly Betancourth','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Avanzado)') LIMIT 1), 2, '18:00:00','20:00:00','Angelly Betancourth','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Danza Contemporánea (Nivel Avanzado)') LIMIT 1), 4, '18:00:00','20:00:00','Angelly Betancourth','116G');

-- ---------- ARTES MUSICALES (CLASES) ----------
-- Bajo: MARTES 10:00-12:00 (204I) Xavier Velasco; MIERCOLES 14:00-16:00
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Bajo'), '10:00:00','12:00:00','Xavier Velasco','204I'),
((SELECT id_actividad FROM actividades WHERE nombre='Bajo'), '14:00:00','16:00:00','Xavier Velasco','204I');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Bajo'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Bajo') ORDER BY id_horario_bloque LIMIT 1), 2, '10:00:00','12:00:00','Xavier Velasco','204I'),
((SELECT id_actividad FROM actividades WHERE nombre='Bajo'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Bajo') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 3, '14:00:00','16:00:00','Xavier Velasco','204I');

-- Guitarra Eléctrica: MIERCOLES 10:00-12:00; JUEVES 10:00-12:00 (201I) Rodolfo Ágredo
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Guitarra Eléctrica'), '10:00:00','12:00:00','Rodolfo Ágredo','201I');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Guitarra Eléctrica'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Guitarra Eléctrica') LIMIT 1), 3, '10:00:00','12:00:00','Rodolfo Ágredo','201I'),
((SELECT id_actividad FROM actividades WHERE nombre='Guitarra Eléctrica'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Guitarra Eléctrica') LIMIT 1), 4, '10:00:00','12:00:00','Rodolfo Ágredo','201I');

-- Piano: LUNES/MARTES/MIERCOLES/JUEVES 11:00-14:00 (114G) Fabián Orozco
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Piano'), '11:00:00','14:00:00','Fabián Orozco','114G');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Piano'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Piano') LIMIT 1), 1, '11:00:00','14:00:00','Fabián Orozco','114G'),
((SELECT id_actividad FROM actividades WHERE nombre='Piano'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Piano') LIMIT 1), 2, '11:00:00','14:00:00','Fabián Orozco','114G'),
((SELECT id_actividad FROM actividades WHERE nombre='Piano'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Piano') LIMIT 1), 3, '11:00:00','14:00:00','Fabián Orozco','114G'),
((SELECT id_actividad FROM actividades WHERE nombre='Piano'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Piano') LIMIT 1), 4, '11:00:00','14:00:00','Fabián Orozco','114G');

-- ARTES MUSICALES (GRUPOS) - CORO y GRUPOS
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Coro'), '16:00:00','19:00:00','Estefanía Díaz','114G'),
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Música de Cámara'), '11:00:00','13:00:00','Federico Cadena','112G'),
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Música de Cámara'), '11:00:00','13:00:00','Federico Cadena','116G'),
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock'), '17:00:00','19:00:00','Julián Eduardo Vargas','201I');

-- Coro: JUEVES 16:00-19:00 y VIERNES 16:00-19:00
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Coro'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Coro') LIMIT 1), 4, '16:00:00','19:00:00','Estefanía Díaz','114G'),
((SELECT id_actividad FROM actividades WHERE nombre='Coro'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Coro') LIMIT 1), 5, '16:00:00','19:00:00','Estefanía Díaz','114G');

-- Grupo de Música de Cámara: VIERNES 11:00-13:00 (112G), SÁBADO 11:00-13:00 (116G)
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Música de Cámara'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Grupo de Música de Cámara') ORDER BY id_horario_bloque LIMIT 1), 5, '11:00:00','13:00:00','Federico Cadena','112G'),
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Música de Cámara'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Grupo de Música de Cámara') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 6, '11:00:00','13:00:00','Federico Cadena','116G');

-- Grupo de Rock: LUNES 17:00-19:00 ; MIERCOLES 17:00-19:00
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock') LIMIT 1), 1, '17:00:00','19:00:00','Julián Eduardo Vargas','201I'),
((SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock') LIMIT 1), 3, '17:00:00','19:00:00','Julián Eduardo Vargas','201I');

-- ---------- ACTIVIDAD FÍSICA Y SALUD ----------
-- Acondicionamiento FIT (Crossfit): Lunes 17:00-19:00, Martes 11:00-13:00, Miércoles 17:00-19:00, Jueves 11:00-13:00, Viernes 11:00-13:00
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), '17:00:00','19:00:00','José Sánchez','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), '11:00:00','13:00:00','Fernando Gutiérrez','COLISEO 2 ZONA D');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)') ORDER BY id_horario_bloque LIMIT 1), 1, '17:00:00','19:00:00','José Sánchez','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 2, '11:00:00','13:00:00','Fernando Gutiérrez','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 3, '17:00:00','19:00:00','José Sánchez','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 4, '11:00:00','13:00:00','Fernando Gutiérrez','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Acondicionamiento FIT (Crossfit)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 5, '11:00:00','13:00:00','Fernando Gutiérrez','COLISEO 2 ZONA D');

-- Entrenamiento Funcional: LUNES 12:00-14:00 (Coliseo 2 Zona A), MARTES 12:00-14:00, MARTES 17:00-19:00, MIERCOLES 12:00-14:00, JUEVES 07:00-09:00, VIERNES 12:00-14:00
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), '12:00:00','14:00:00','Jose Alfredo Calderón','COLISEO 2 ZONA A'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), '17:00:00','19:00:00','Óscar Eduardo Patiño','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), '07:00:00','09:00:00','Óscar Eduardo Patiño','COLISEO 2 ZONA D');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional') ORDER BY id_horario_bloque LIMIT 1), 1, '12:00:00','14:00:00','Jose Alfredo Calderón','COLISEO 2 ZONA A'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional') ORDER BY id_horario_bloque LIMIT 1), 2, '12:00:00','14:00:00','Jose Alfredo Calderón','COLISEO 2 ZONA A'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 2, '17:00:00','19:00:00','Óscar Eduardo Patiño','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional') ORDER BY id_horario_bloque LIMIT 1), 3, '12:00:00','14:00:00','Jose Alfredo Calderón','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional') ORDER BY id_horario_bloque OFFSET 2 LIMIT 1), 4, '07:00:00','09:00:00','Óscar Eduardo Patiño','COLISEO 2 ZONA D'),
((SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Entrenamiento Funcional') ORDER BY id_horario_bloque LIMIT 1), 5, '12:00:00','14:00:00','Óscar Eduardo Patiño','COLISEO 2 ZONA A');

-- Gimnasio: LUNES a VIERNES 06:00-19:00; SÁBADO 08:00-11:00 (COLISEO 2 ZONA E) - instructores
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), '06:00:00','19:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E'),
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), '08:00:00','11:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Gimnasio') ORDER BY id_horario_bloque LIMIT 1), 1, '06:00:00','19:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E'),
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Gimnasio') ORDER BY id_horario_bloque LIMIT 1), 2, '06:00:00','19:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E'),
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Gimnasio') ORDER BY id_horario_bloque LIMIT 1), 3, '06:00:00','19:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E'),
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Gimnasio') ORDER BY id_horario_bloque LIMIT 1), 4, '06:00:00','19:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E'),
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Gimnasio') ORDER BY id_horario_bloque LIMIT 1), 5, '06:00:00','19:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E'),
((SELECT id_actividad FROM actividades WHERE nombre='Gimnasio'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Gimnasio') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 6, '08:00:00','11:00:00','Adriana Rodríguez / Germán Pinzón','COLISEO 2 ZONA E');

-- ---------- DEPORTES DE CONJUNTO (BALONCESTO) ----------
-- Baloncesto (Nivel Formativo): MARTES 14:00-16:00, JUEVES 14:00-16:00, SÁBADO 08:00-10:00 - COLISEO 1-MU1 - James Valdés
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)'), '14:00:00','16:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)'), '08:00:00','10:00:00','James Valdés','COLISEO 1-MU1');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)') ORDER BY id_horario_bloque LIMIT 1), 2, '14:00:00','16:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)') ORDER BY id_horario_bloque LIMIT 1), 4, '14:00:00','16:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 6, '08:00:00','10:00:00','James Valdés','COLISEO 1-MU1');

-- Baloncesto (Nivel Avanzado): LUNES 16:00-18:00; MARTES 12:00-14:00; JUEVES 12:00-14:00; VIERNES 16:00-18:00; SABADO 10:00-12:00
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), '16:00:00','18:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), '12:00:00','14:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), '10:00:00','12:00:00','James Valdés','COLISEO 1-MU1');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)') ORDER BY id_horario_bloque LIMIT 1), 1, '16:00:00','18:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 2, '12:00:00','14:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 4, '12:00:00','14:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)') ORDER BY id_horario_bloque LIMIT 1), 5, '16:00:00','18:00:00','James Valdés','COLISEO 1-MU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Avanzado)') ORDER BY id_horario_bloque OFFSET 2 LIMIT 1), 6, '10:00:00','12:00:00','James Valdés','COLISEO 1-MU1');

-- ---------- FÚTBOL MASCULINO ----------
-- Formativo (Fabio Zuluaga)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'), '11:30:00','13:30:00','Fabio Zuluaga','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'), '18:00:00','20:00:00','Fabio Zuluaga','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'), '08:00:00','10:00:00','Fabio Zuluaga','CANCHA-FU1');

-- Días de la semana asociados
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
-- Lunes
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)')
  ORDER BY id_horario_bloque LIMIT 1),
 1, '11:30:00','13:30:00','Fabio Zuluaga','CANCHA-FU1'),

-- Martes
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)')
  ORDER BY id_horario_bloque OFFSET 1 LIMIT 1),
 2, '18:00:00','20:00:00','Fabio Zuluaga','CANCHA-FU1'),

-- Jueves
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)')
  ORDER BY id_horario_bloque OFFSET 1 LIMIT 1),
 4, '18:00:00','20:00:00','Fabio Zuluaga','CANCHA-MI1'),

-- Viernes
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)')
  ORDER BY id_horario_bloque LIMIT 1),
 5, '11:30:00','13:30:00','Fabio Zuluaga','CANCHA-FU1'),

-- Sábado
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Formativo)')
  ORDER BY id_horario_bloque OFFSET 2 LIMIT 1),
 6, '08:00:00','10:00:00','Fabio Zuluaga','CANCHA-FU1');


-- Fútbol Masculino (Avanzado)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), '07:00:00','09:00:00','Alfonso González','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), '11:30:00','13:30:00','Alfonso González','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), '18:00:00','20:00:00','Alfonso González','CANCHA-FU1');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)') ORDER BY id_horario_bloque LIMIT 1), 1, '07:00:00','09:00:00','Alfonso González','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 2, '11:30:00','13:30:00','Alfonso González','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)') ORDER BY id_horario_bloque OFFSET 2 LIMIT 1), 3, '18:00:00','20:00:00','Alfonso González','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)') ORDER BY id_horario_bloque LIMIT 1), 4, '07:00:00','09:00:00','Alfonso González','CANCHA-FU1'),
((SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Fútbol Masculino (Avanzado)') ORDER BY id_horario_bloque LIMIT 1), 5, '07:00:00','09:00:00','Alfonso González','CANCHA-FU1');

-- ---------- DEPORTES INDIVIDUALES ----------
-- Ajedrez: LUNES 12:00-14:00, MARTES 17:00-19:00, MIERCOLES 12:00-14:00, JUEVES 07:00-09:00 (102I) Martha Isabel Matheus
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), '12:00:00','14:00:00','Martha Isabel Matheus','102I'),
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), '17:00:00','19:00:00','Martha Isabel Matheus','102I'),
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), '07:00:00','09:00:00','Martha Isabel Matheus','102I');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Ajedrez') ORDER BY id_horario_bloque LIMIT 1), 1, '12:00:00','14:00:00','Martha Isabel Matheus','102I'),
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Ajedrez') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 2, '17:00:00','19:00:00','Martha Isabel Matheus','102I'),
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Ajedrez') ORDER BY id_horario_bloque LIMIT 1), 3, '12:00:00','14:00:00','Martha Isabel Matheus','102I'),
((SELECT id_actividad FROM actividades WHERE nombre='Ajedrez'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Ajedrez') ORDER BY id_horario_bloque OFFSET 2 LIMIT 1), 4, '07:00:00','09:00:00','Martha Isabel Matheus','102I');

-- Judo: MARTES 09:00-11:00; VIERNES 18:00-20:00; SÁBADO 10:00-12:00 (COLISEO 2 ZONA C) Johanier López
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Judo'), '09:00:00','11:00:00','Johanier López','COLISEO 2 ZONA C'),
((SELECT id_actividad FROM actividades WHERE nombre='Judo'), '18:00:00','20:00:00','Johanier López','COLISEO 2 ZONA C'),
((SELECT id_actividad FROM actividades WHERE nombre='Judo'), '10:00:00','12:00:00','Johanier López','COLISEO 2 ZONA C');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Judo'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Judo') ORDER BY id_horario_bloque LIMIT 1), 2, '09:00:00','11:00:00','Johanier López','COLISEO 2 ZONA C'),
((SELECT id_actividad FROM actividades WHERE nombre='Judo'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Judo') ORDER BY id_horario_bloque OFFSET 1 LIMIT 1), 5, '18:00:00','20:00:00','Johanier López','COLISEO 2 ZONA C'),
((SELECT id_actividad FROM actividades WHERE nombre='Judo'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Judo') ORDER BY id_horario_bloque OFFSET 2 LIMIT 1), 6, '10:00:00','12:00:00','Johanier López','COLISEO 2 ZONA C');

-- Bloques para Natación (Formativo)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Formativo)'), '17:00:00','19:00:00','Yorlenny Arango','PISCINA EDIFICIO N'),
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Formativo)'), '11:30:00','13:30:00','Jéssica Montenegro','PISCINA EDIFICIO N');

-- Días asociados (2 = martes, 3 = miércoles)
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque 
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Natación (Formativo)')
  ORDER BY id_horario_bloque LIMIT 1),
 2, '17:00:00','19:00:00','Yorlenny Arango','PISCINA EDIFICIO N'),

((SELECT id_actividad FROM actividades WHERE nombre='Natación (Formativo)'),
 (SELECT id_horario_bloque FROM horarios_bloque 
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Natación (Formativo)')
  ORDER BY id_horario_bloque OFFSET 1 LIMIT 1),
 3, '11:30:00','13:30:00','Jéssica Montenegro','PISCINA EDIFICIO N');


-- Bloques para Natación (Avanzado)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)'), '17:00:00','19:00:00','Yorlenny Arango','PISCINA EDIFICIO N'),
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)'), '11:30:00','13:30:00','Yorlenny Arango','PISCINA EDIFICIO N'),
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)'), '10:00:00','12:00:00','Yorlenny Arango','PISCINA EDIFICIO N');

-- Días asociados (3 = miércoles, 4 = jueves, 5 = viernes)
INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)'),
 (SELECT id_horario_bloque FROM horarios_bloque 
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)')
  ORDER BY id_horario_bloque LIMIT 1),
 3, '17:00:00','19:00:00','Yorlenny Arango','PISCINA EDIFICIO N'),

((SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)'),
 (SELECT id_horario_bloque FROM horarios_bloque 
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)')
  ORDER BY id_horario_bloque OFFSET 1 LIMIT 1),
 4, '11:30:00','13:30:00','Yorlenny Arango','PISCINA EDIFICIO N'),

((SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)'),
 (SELECT id_horario_bloque FROM horarios_bloque 
  WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Natación (Avanzado)')
  ORDER BY id_horario_bloque OFFSET 2 LIMIT 1),
 5, '10:00:00','12:00:00','Yorlenny Arango','PISCINA EDIFICIO N');


-- ---------- TALLERES CORTOS ----------
-- Cerámica: LUNES 09:30-11:30 (SALÓN 203 I) - Inicia 1 de marzo (Semana 6) termina 27 abril (Semana 14)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Cerámica'), '09:30:00','11:30:00','Angélica Valencia','SALÓN 203 I');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Cerámica'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Cerámica') LIMIT 1), 1, '09:30:00','11:30:00','Angélica Valencia','SALÓN 203 I');

-- Voleibol Playa: JUEVES 12:00-14:00 RIO BEACH SPORTS - Inicia 11 marzo (Semana 7)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Voleibol Playa'), '12:00:00','14:00:00','Alexander Bonilla García','RIO BEACH SPORTS');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Voleibol Playa'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Voleibol Playa') LIMIT 1), 4, '12:00:00','14:00:00','Alexander Bonilla García','RIO BEACH SPORTS');

-- ---------- AGENDA CULTURAL Y DEPORTIVA (eventos listados) ----------
-- Conciertos y comienzo torneo de tenis de mesa (evento)
INSERT INTO horarios_bloque (actividades_id_actividad, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Concierto BU - Acústico & Son de la U'), '13:00:00','14:30:00','Organización BU','Tarima de BU'),
((SELECT id_actividad FROM actividades WHERE nombre='Concierto BU - Rock & Tambores'), '13:00:00','14:30:00','Organización BU','Tarima de BU'),
((SELECT id_actividad FROM actividades WHERE nombre='Torneo Interno de Tenis de Mesa'), '09:00:00','18:00:00','Organización BU','Coliseo 2');

INSERT INTO horarios_actividad (actividades_id_actividad, horario_bloque_id, dia_semana, hora_inicio, hora_fin, profesor, lugar)
VALUES
((SELECT id_actividad FROM actividades WHERE nombre='Concierto BU - Acústico & Son de la U'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Concierto BU - Acústico & Son de la U') LIMIT 1), 2, '13:00:00','14:30:00','Organización BU','Tarima de BU'),
((SELECT id_actividad FROM actividades WHERE nombre='Concierto BU - Rock & Tambores'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Concierto BU - Rock & Tambores') LIMIT 1), 4, '13:00:00','14:30:00','Organización BU','Tarima de BU'),
((SELECT id_actividad FROM actividades WHERE nombre='Torneo Interno de Tenis de Mesa'), (SELECT id_horario_bloque FROM horarios_bloque WHERE actividades_id_actividad=(SELECT id_actividad FROM actividades WHERE nombre='Torneo Interno de Tenis de Mesa') LIMIT 1), 2, '09:00:00','18:00:00','Organización BU','Coliseo 2');

-- =========================
-- 5) PARTICIPANTES (IDs = cédulas del PDF) - CASOS Y TORNEO
-- =========================

-- Casos:
-- 1) María Ximena Narvaez Olarte - CC 1112343789
-- 2) Carlos Daniel Pérez Solarte - CC 1445786392
-- Torneo: 6 inscritos (cedulas)
-- ========================================
-- CREACIÓN DE USUARIOS EN auth_user
-- username = cédula del participante
-- ========================================

INSERT INTO auth_user (
    username, first_name, last_name, email, password,
    is_superuser, is_staff, is_active, date_joined
)
VALUES
('1112343789', 'María Ximena', 'Narvaez Olarte', 'maria.narvaez@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1445786392', 'Carlos Daniel', 'Pérez Solarte', 'carlos.perez@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1123456789', 'Juan', 'Montenegro', 'juan.montenegro@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1978463723', 'Jaime', 'Villalobos', 'jaime.villalobos@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1739593012', 'Óscar', 'Triviño', 'oscar.trivino@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1749303184', 'Camilo', 'Forero', 'camilo.forero@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1940385178', 'Mario', 'Sinisterra', 'mario.sinisterra@example.com', '', FALSE, FALSE, TRUE, NOW()),
('1748234111', 'Felipe', 'Gómez', 'felipe.gomez@example.com', '', FALSE, FALSE, TRUE, NOW());
-- ========================================
-- INSERCIÓN DE PARTICIPANTES (vinculados a auth_user)
-- ========================================

INSERT INTO participantes (
    id_participante, nombre, apellido, correo, semestre,
    estado_activo, roles_id_rol, facultad, programa, genero, "user"
)
VALUES
(1112343789, 'María Ximena', 'Narvaez Olarte', 'maria.narvaez@example.com', 4, 'S', (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1), 'Artes', 'Artes Plásticas', 'F',(SELECT id FROM auth_user WHERE username='1112343789')),

(1445786392, 'Carlos Daniel', 'Pérez Solarte', 'carlos.perez@example.com', 6, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Música', 'Música', 'M',
 (SELECT id FROM auth_user WHERE username='1445786392')),

(1123456789, 'Juan', 'Montenegro', 'juan.montenegro@example.com', 3, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Deportes', 'Deporte', 'M',
 (SELECT id FROM auth_user WHERE username='1123456789')),

(1978463723, 'Jaime', 'Villalobos', 'jaime.villalobos@example.com', 5, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Deportes', 'Deporte', 'M',
 (SELECT id FROM auth_user WHERE username='1978463723')),

(1739593012, 'Óscar', 'Triviño', 'oscar.trivino@example.com', 2, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Deportes', 'Deporte', 'M',
 (SELECT id FROM auth_user WHERE username='1739593012')),

(1749303184, 'Camilo', 'Forero', 'camilo.forero@example.com', 4, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Deportes', 'Deporte', 'M',
 (SELECT id FROM auth_user WHERE username='1749303184')),

(1940385178, 'Mario', 'Sinisterra', 'mario.sinisterra@example.com', 4, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Deportes', 'Deporte', 'M',
 (SELECT id FROM auth_user WHERE username='1940385178')),

(1748234111, 'Felipe', 'Gómez', 'felipe.gomez@example.com', 3, 'S',
 (SELECT id_rol FROM roles WHERE nombre_rol='Estudiante' LIMIT 1),
 'Deportes', 'Deporte', 'M',
 (SELECT id FROM auth_user WHERE username='1748234111'));


-- Nota: roles_id_rol en participantes quedó en NULL a falta de roles específicos; ajusta si en tu BD los roles existen.
-- Si quieres, puedo crear roles específicos y volver a insertar participantes para enlazarlos correctamente.

-- =========================
-- 6) PARTICIPACIONES Y ASISTENCIAS (CASOS del PDF)
-- Caso 1 - María Ximena:
--   - Inscrita a Arte Fantástico (7 semanas de asistencia) -> falta 1 semana para camiseta (según enunciado)
--   - Inscrita a Judo (1 semana de asistencia)
--   - Inscrita a Baloncesto Formativo (4 semanas de asistencia)
-- Fechas de ejemplo: asumimos inicio 2026-02-02; generamos asistencias semanales en fechas consecutivas
-- =========================

-- Insert participaciones para María
INSERT INTO participaciones (fecha_inscripcion, participantes_id_participante, actividades_id_actividad, roles_participacion_id_rol_participacion, estados_participacion_id_estado_participacion)
VALUES
('2026-02-02','1112343789',(SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico'), (SELECT id_rol_participacion FROM roles_participacion WHERE nombre='Asistente' LIMIT 1), 1),
('2026-02-02','1112343789',(SELECT id_actividad FROM actividades WHERE nombre='Judo'), (SELECT id_rol_participacion FROM roles_participacion WHERE nombre='Asistente' LIMIT 1), 1),
('2026-02-02','1112343789',(SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)'), (SELECT id_rol_participacion FROM roles_participacion WHERE nombre='Asistente' LIMIT 1), 1);

-- Crear asistencias para María:
-- Arte Fantástico -> 7 asistencias (simulate: semanas 1..7)
-- ==============================================
-- CREAR ASISTENCIAS Y NOTIFICACIONES CORRECTAS
-- ==============================================

-- Arte Fantástico -> 7 asistencias (simulate: semanas 1..7)
INSERT INTO asistencias (fecha, estados_asistencia_id_estado_asistencia, participaciones_id_participacion)
SELECT d::timestamp,
       (SELECT id_estado_asistencia FROM estados_asistencia WHERE nombre='Presente' LIMIT 1),
       p.id_participacion
FROM (
  VALUES
    ('2026-02-03'),('2026-02-10'),('2026-02-17'),
    ('2026-02-24'),('2026-03-03'),('2026-03-10'),('2026-03-17')
) AS weeks(d),
(SELECT id_participacion
 FROM participaciones
 WHERE participantes_id_participante = 1112343789
   AND actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Arte Fantástico')
 LIMIT 1) AS p(id_participacion);


-- Judo -> 1 asistencia (week 1)
INSERT INTO asistencias (fecha, estados_asistencia_id_estado_asistencia, participaciones_id_participacion)
VALUES (
  '2026-02-03',
  (SELECT id_estado_asistencia FROM estados_asistencia WHERE nombre='Presente' LIMIT 1),
  (SELECT id_participacion FROM participaciones
   WHERE participantes_id_participante = 1112343789
     AND actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Judo')
   LIMIT 1)
);


-- Baloncesto Formativo -> 4 asistencias (4 semanas)
INSERT INTO asistencias (fecha, estados_asistencia_id_estado_asistencia, participaciones_id_participacion)
SELECT d::timestamp,
       (SELECT id_estado_asistencia FROM estados_asistencia WHERE nombre='Presente' LIMIT 1),
       (SELECT id_participacion FROM participaciones
        WHERE participantes_id_participante = 1112343789
          AND actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Baloncesto (Nivel Formativo)')
        LIMIT 1)
FROM (VALUES ('2026-02-04'),('2026-02-11'),('2026-02-18'),('2026-02-25')) AS t(d);


-- Notificación a María Ximena (falta 1 semana para camiseta)
INSERT INTO notificaciones (mensaje, fecha, participantes_id_participante, tipos_notificacion_id_tipo_notificacion, leida)
VALUES (
  'Le falta 1 semana de asistencia en Arte Fantástico para ganarse la camiseta.',
  now(),
  1112343789,
  (SELECT id_tipo_notificacion FROM tipos_notificacion LIMIT 1),
  FALSE
);


-- Caso 2 - Carlos Daniel Pérez Solarte (Grupo de Rock, 9 semanas)
INSERT INTO participaciones (
  fecha_inscripcion,
  participantes_id_participante,
  actividades_id_actividad,
  roles_participacion_id_rol_participacion,
  estados_participacion_id_estado_participacion
)
VALUES (
  '2026-02-02',
  1445786392,
  (SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock'),
  (SELECT id_rol_participacion FROM roles_participacion WHERE nombre='Asistente' LIMIT 1),
  1
);


-- 9 asistencias para Grupo de Rock
INSERT INTO asistencias (fecha, estados_asistencia_id_estado_asistencia, participaciones_id_participacion)
SELECT d::timestamp,
       (SELECT id_estado_asistencia FROM estados_asistencia WHERE nombre='Presente' LIMIT 1),
       (SELECT id_participacion FROM participaciones
        WHERE participantes_id_participante = 1445786392
          AND actividades_id_actividad = (SELECT id_actividad FROM actividades WHERE nombre='Grupo de Rock')
        LIMIT 1)
FROM (
  VALUES
  ('2026-02-02'),('2026-02-09'),('2026-02-16'),
  ('2026-02-23'),('2026-03-02'),('2026-03-09'),
  ('2026-03-16'),('2026-03-23'),('2026-03-30')
) AS t(d);


-- Notificación a Carlos Daniel (fecha del concierto)
INSERT INTO notificaciones (mensaje, fecha, participantes_id_participante, tipos_notificacion_id_tipo_notificacion, leida)
VALUES (
  'Se le notifica: la fecha del Concierto BU - Rock & Tambores es Martes, 16 de marzo a la 1:00 p.m. en Tarima de BU.',
  '2026-03-16 13:00:00',
  1445786392,
  (SELECT id_tipo_notificacion FROM tipos_notificacion LIMIT 1),
  FALSE
);


-- =========================
-- 7) TORNEO INTERNO DE TENIS DE MESA (configuración, equipos, partidos, clasificaciones)
-- - Torneo: "Torneo Interno de Tenis de Mesa" ya insertado como actividad/evento; vamos a crear registro en torneos y equipos.
-- =========================

-- Crear torneo
INSERT INTO torneos (nombre, disciplinas_id_disciplina, fecha_inicio, fecha_fin, estados_torneo_id_estado_torneo, reglas_elegibilidad, aforo_equipos, limite_inscripcion)
VALUES
('Torneo Interno de Tenis de Mesa', (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1), '2026-03-23', '2026-04-30', (SELECT id_estado_torneo FROM estados_torneo WHERE nombre='En Curso' LIMIT 1), 'Inscripción abierta a estudiantes', 16, '2026-03-20');

-- Obtener id_torneo recién creado
-- (asumimos que solo hay un torneo con ese nombre; si hay varios, ajustar)
-- Creamos equipos (un equipo = jugador individual, vinculamos a participantes)
-- Jugadores y cédulas: Juan (1123456789), Jaime (1978463723), Óscar (1739593012), Camilo (1749303184), Mario (1940385178), Felipe (1748234111)

-- Crear equipos para cada jugador (equipos.participantes_id_participante es FK)
INSERT INTO equipos (nombre, fecha_creacion, cantidad_personas, participantes_id_participante, disciplinas_id_disciplina)
VALUES
('Equipo - Juan Montenegro', now(), 1, 1123456789, (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1)),
('Equipo - Jaime Villalobos', now(), 1, 1978463723, (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1)),
('Equipo - Óscar Triviño', now(), 1, 1739593012, (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1)),
('Equipo - Camilo Forero', now(), 1, 1749303184, (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1)),
('Equipo - Mario Sinisterra', now(), 1, 1940385178, (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1)),
('Equipo - Felipe Gómez', now(), 1, 1748234111, (SELECT id_disciplina FROM disciplinas WHERE nombre='Tenis de Mesa' LIMIT 1));

-- Link equipos al torneo (torneos_equipos)
INSERT INTO torneos_equipos (torneos_id_torneo, equipos_id_equipo)
SELECT (SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), e.id_equipo
FROM equipos e
WHERE e.nombre LIKE 'Equipo - %';

-- (Opcional) equipos_participantes table is a separate table; if you want an entry there too, insert:
INSERT INTO equipos_participantes (equipos_id_equipo, participantes_id_participante, id_participante1)
SELECT e.id_equipo, e.participantes_id_participante, e.participantes_id_participante
FROM equipos e
WHERE e.nombre LIKE 'Equipo - %';

-- PARTIDOS (según resultados en el PDF)
-- Notas: usamos campos: torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado
-- Vamos a insertar los 6 partidos con resultados dados.

-- Helper: obtener id_equipo por nombre
-- 1) Juan (2) vs Camilo (1)
INSERT INTO partidos (torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), '2026-03-23 09:00:00', '2026-03-23 09:30:00', 'Coliseo 2', (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Juan Montenegro' LIMIT 1), (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Camilo Forero' LIMIT 1), 2, 1, 'FINALIZADO');

-- 2) Jaime (2) vs Óscar (0)
INSERT INTO partidos (torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), '2026-03-23 09:40:00', '2026-03-23 10:10:00', 'Coliseo 2', (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Jaime Villalobos' LIMIT 1), (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Óscar Triviño' LIMIT 1), 2, 0, 'FINALIZADO');

-- 3) Mario (1) vs Felipe (2)
INSERT INTO partidos (torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), '2026-03-23 10:20:00', '2026-03-23 10:50:00', 'Coliseo 2', (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Mario Sinisterra' LIMIT 1), (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Felipe Gómez' LIMIT 1), 1, 2, 'FINALIZADO');

-- 4) Juan (1) vs Óscar (2)
INSERT INTO partidos (torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), '2026-03-24 09:00:00', '2026-03-24 09:30:00', 'Coliseo 2', (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Juan Montenegro' LIMIT 1), (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Óscar Triviño' LIMIT 1), 1, 2, 'FINALIZADO');

-- 5) Camilo (1) vs Mario (2)
INSERT INTO partidos (torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), '2026-03-24 09:40:00', '2026-03-24 10:10:00', 'Coliseo 2', (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Camilo Forero' LIMIT 1), (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Mario Sinisterra' LIMIT 1), 1, 2, 'FINALIZADO');

-- 6) Jaime (2) vs Felipe (1)
INSERT INTO partidos (torneos_id_torneo, fecha_inicio, fecha_fin, lugar, equipos_id_equipo, equipos_id_equipo2, marcador_a, marcador_b, estado)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1), '2026-03-24 10:20:00', '2026-03-24 10:50:00', 'Coliseo 2', (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Jaime Villalobos' LIMIT 1), (SELECT id_equipo FROM equipos WHERE nombre='Equipo - Felipe Gómez' LIMIT 1), 2, 1, 'FINALIZADO');

-- =========================
-- 8) CLASIFICACIONES (tabla de posiciones hasta el momento)
-- Calculadas manualmente a partir de los resultados del enunciado:
-- Asumimos: victoria = 3 pts, empate = 1 (no hay empates), derrota = 0.
-- Resultado resumen calculado en el análisis:
-- Jaime: PJ=2 PG=2 PP=0 GF=4 GC=1 PTS=6
-- Juan:  PJ=2 PG=1 PP=1 GF=3 GC=3 PTS=3
-- Óscar: PJ=2 PG=1 PP=1 GF=2 GC=3 PTS=3
-- Mario: PJ=2 PG=1 PP=1 GF=3 GC=3 PTS=3
-- Felipe: PJ=2 PG=1 PP=1 GF=3 GC=3 PTS=3
-- Camilo: PJ=2 PG=0 PP=2 GF=2 GC=4 PTS=0

-- Insert clasificaciones por equipo (torneos_id_torneo, equipos_id_equipo, pj, pg, pe, pp, gf, gc, pts)
INSERT INTO clasificaciones (torneos_id_torneo, equipos_id_equipo, pj, pg, pe, pp, gf, gc, pts)
VALUES
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1),(SELECT id_equipo FROM equipos WHERE nombre='Equipo - Jaime Villalobos' LIMIT 1), 2,2,0,0,4,1,6),
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1),(SELECT id_equipo FROM equipos WHERE nombre='Equipo - Juan Montenegro' LIMIT 1), 2,1,0,1,3,3,3),
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1),(SELECT id_equipo FROM equipos WHERE nombre='Equipo - Óscar Triviño' LIMIT 1), 2,1,0,1,2,3,3),
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1),(SELECT id_equipo FROM equipos WHERE nombre='Equipo - Mario Sinisterra' LIMIT 1), 2,1,0,1,3,3,3),
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1),(SELECT id_equipo FROM equipos WHERE nombre='Equipo - Felipe Gómez' LIMIT 1), 2,1,0,1,3,3,3),
((SELECT id_torneo FROM torneos WHERE nombre='Torneo Interno de Tenis de Mesa' LIMIT 1),(SELECT id_equipo FROM equipos WHERE nombre='Equipo - Camilo Forero' LIMIT 1), 2,0,0,2,2,4,0);

COMMIT;
