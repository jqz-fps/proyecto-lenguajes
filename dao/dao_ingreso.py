from model.Ingreso import Ingreso
from .conexion import conectar, cerrar_conexion
import logging

def crear(ingreso):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("INSERT INTO Ingreso (id_persona, fecha) VALUES (?, ?)",
      (ingreso.id_persona, ingreso.fecha)
    )
    id_nuevo = cur.lastrowid
    logging.debug(f"Ingreso creado: ID: {id_nuevo}\tID Persona: {ingreso.id_persona}\tFecha: {ingreso.fecha}")
    conexion.commit()
    return id_nuevo
  except Exception as e:
    logging.error(f"Error al crear ingreso: {e}")
  finally:
    cerrar_conexion(conexion)

def obtener_por_persona(id_persona):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("SELECT * FROM Ingreso WHERE id_persona = ? ORDER BY fecha DESC", (id_persona,))
    respuesta = cur.fetchall()
    ingresos = []
    for ingreso in respuesta:
      ingresos.append(Ingreso(
          ingreso["id"],
          ingreso["id_persona"],
          ingreso["fecha"]
        )
      )
    logging.debug(f"Ingresos obtenidos: ID Persona: {id_persona}")
    return ingresos
  except Exception as e:
    logging.error(f"Error al obtener ingreso por persona: {e}")
  finally:
    cerrar_conexion(conexion)

def obtener_todos():
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("SELECT * FROM Ingreso ORDER BY fecha DESC")
    respuesta = cur.fetchall()
    ingresos = []
    for ingreso in respuesta:
      ingresos.append(Ingreso(
          ingreso["id"],
          ingreso["id_persona"],
          ingreso["fecha"]
        )
      )
    logging.debug("Se han obtenido las ingresos")
    return ingresos
  except Exception as e:
    logging.error(f"Error al obtener ingresos: {e}")
  finally:
    cerrar_conexion(conexion)

def actualizar(ingreso):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("UPDATE Ingreso SET id_persona = ?, fecha = ? WHERE id = ?",
      (ingreso.id_persona, ingreso.fecha, ingreso.id)
    )
    logging.debug(f"Ingreso actualizado: ID: {ingreso.id}\tID Persona: {ingreso.id_persona}\tFecha: {ingreso.fecha}")
    conexion.commit()
  except Exception as e:
    logging.error(f"Error al actualizar ingreso: {e}")
  finally:
    cerrar_conexion(conexion)

def eliminar(id_ingreso):
  conexion = conectar()
  try:
    if not conexion: raise Exception("No se ha podido conectar a la base de datos")
    cur = conexion.cursor()
    cur.execute("DELETE FROM Ingreso WHERE id = ?", (id_ingreso,))
    logging.debug(f"Ingreso eliminado: ID: {id_ingreso}")
    conexion.commit()
  except Exception as e:
    logging.error(f"Error al eliminar ingreso: {e}")
  finally:
    cerrar_conexion(conexion)