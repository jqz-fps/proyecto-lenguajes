import numpy as np
from model.Persona import Persona
from .conexion import conectar, cerrar_conexion
import logging

def crear(persona):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("INSERT INTO Persona (dni, codigo, nombres, apellidos, encoding) VALUES (?, ?, ?, ?, ?)",
      (persona.dni, persona.codigo, persona.nombres, persona.apellidos, persona.encoding)
    )
    id_nuevo = cur.lastrowid
    logging.debug(f"Persona creada: ID: {id_nuevo}\tDNI: {persona.dni}\tCodigo: {persona.codigo}\tNombres: {persona.nombres}\tApellidos: {persona.apellidos}\tEncoding: {persona.encoding}")
    conexion.commit()
    return id_nuevo
  except Exception as e:
    logging.error(f"Error al crear persona: {e}")
  finally:
    cerrar_conexion(conexion)

def obtener(id):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("SELECT * FROM Persona WHERE id = ?", (id,))
    respuesta = cur.fetchone()
    if respuesta is None:
      return None
    encoding_bytes = respuesta["encoding"]
    encoding_np = np.frombuffer(encoding_bytes, dtype=np.float64)
    persona = Persona(
        respuesta["id"],
        respuesta["dni"],
        respuesta["codigo"],
        respuesta["nombres"],
        respuesta["apellidos"],
        encoding_np
      )
    logging.debug(f"Persona obtenida: ID: {persona.id}\tDNI: {persona.dni}\tCodigo: {persona.codigo}\tNombres: {persona.nombres}\tApellidos: {persona.apellidos}\tEncoding: {persona.encoding}")
    return persona
  except Exception as e:
    logging.error(f"Error al obtener persona: {e}")
  finally:
    cerrar_conexion(conexion)

def obtener_todos():
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("SELECT * FROM Persona")
    respuesta = cur.fetchall()
    personas = []
    for persona in respuesta:
      encoding_bytes = persona["encoding"]
      encoding_np = np.frombuffer(encoding_bytes, dtype=np.float64)
      personas.append(Persona(
          persona["id"],
          persona["dni"],
          persona["codigo"],
          persona["nombres"],
          persona["apellidos"],
          encoding_np
        )
      )
    logging.debug("Se han obtenido las personas")
    return personas
  except Exception as e:
    logging.error(f"Error al obtener personas: {e}")
  finally:
    cerrar_conexion(conexion)

def actualizar(persona):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("UPDATE Persona SET dni = ?, codigo = ?, nombres = ?, apellidos = ?, encoding = ? WHERE id = ?",
      (persona.dni, persona.codigo, persona.nombres, persona.apellidos, persona.encoding, persona.id)
    )
    logging.debug(f"Persona actualizada: ID: {persona.id}\tDNI: {persona.dni}\tCodigo. {persona.codigo}\tNombres: {persona.nombres}\tApellidos: {persona.apellidos}\tEncoding: {persona.encoding}")
    conexion.commit()
  except Exception as e:
    logging.error(f"Error al actualizar persona: {e}")
  finally:
    cerrar_conexion(conexion)

def eliminar(id_persona):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("DELETE FROM Persona WHERE id = ?", (id_persona,))
    logging.debug(f"Persona eliminada: ID: {id_persona}")
    conexion.commit()
  except Exception as e:
    logging.error(f"Error al eliminar persona: {e}")
  finally:
    cerrar_conexion(conexion)