import sqlite3, logging

BD_URL = "data/registro.db"

def conectar():
  try:
    conexion = sqlite3.connect(BD_URL)
    conexion.row_factory = sqlite3.Row
    return conexion
  except Exception as e:
    logging.error(f"Error al conectar a la base de datos: {e}")

def cerrar_conexion(conexion):
  if conexion != None:
    try:
      conexion.close()
    except Exception as e:
      logging.error(f"Error al cerrar la conexión con la base de datos: {e}")