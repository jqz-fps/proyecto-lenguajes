import logging, time
from datetime import datetime
import face_recognition, cv2
import dao.dao_persona as DAOPersona, dao.dao_ingreso as DAOIngreso
from model.Ingreso import Ingreso
import requests, threading

logging.basicConfig(
  level=logging.DEBUG,
  format="%(asctime)s - %(levelname)s - %(message)s",
  filename="audit.log",
  filemode="a",
)

logging.info("---------- Se ha iniciado el registro en vivo ----------")

# Cargar lista de personas conocidas desde la BD
personas = DAOPersona.obtener_todos()

# Diccionario de ingresos recientes, para manejar el cooldown
ultimos_ingresos = {}
# Lista de mensajes de ingreso recientes
mensajes_ingreso = []

# Objeto cv2 para capturar desde la camara, y dimensiones de la camara
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

def capturar_y_preprocesar(cap):
  """
  Captura un frame de la camara, lo voltea horizontalmente (espejado),
  lo convierte a RGB y genera una version reducida a su cuarta parte.

  Args:
    cap: Objeto cv2 que representa la cámara.

  Returns:
    tuple (
      frame: Frame capturado,
      frame_rgb: Frame capturado convertido a RGB,
      small_frame: Frame capturado convertido a RGB reducido
    )
  """
  ret, frame = cap.read()
  if not ret:
    return None, None, None
  frame = cv2.flip(frame, 1)
  frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  small_frame = cv2.resize(frame_rgb, (0, 0), fx=0.25, fy=0.25)
  return frame, frame_rgb, small_frame

def reconocer_rostros(small_frame):
  """
  Realiza la deteccion de rostros en una imagen reducida.

  Args:
    small_frame: Frame reducido (0.25 veces su tamaño original).

  Returns:
    tuple (
      locations: Lista de ubicaciones de los rostros encontrados.
      encodings: Lista de codificaciones de los rostros encontrados.
    )
  """
  locations = face_recognition.face_locations(small_frame, model="hog")
  encodings = face_recognition.face_encodings(small_frame, locations)
  return locations, encodings

def identificar_persona(face_encoding, personas):
  """
  Compara una codificacion facial con todas la lista de personas conocidas,
  y devuelve la mejor coincidencia

  Args:
    face_encoding: Codificacion facial de la persona encontrada.
    personas: Lista de personas conocidas.

  Returns:
    tuple (
      persona: Persona coincidente o None,
      distancia: Distancia minima o None.
    )
  """
  distancias = [face_recognition.face_distance([p.encoding], face_encoding)[0] for p in personas]
  indice_min = distancias.index(min(distancias))
  if distancias[indice_min] < 0.45:
    return personas[indice_min], distancias[indice_min]
  return None, None


def enviar_ingreso(data):
  """
  Envía información de un ingreso.
  
  Args:
    data: Diccionario con los datos del ingreso.
  """
  try:
    requests.post('http://localhost:5000/ingresos/nuevo', json=data)
  except Exception as e:
    logging.error(f"Error enviando ingreso: {e}")

def registrar_ingreso(persona, tiempo_actual, ultimos_ingresos, mensajes_ingreso):
  """
  Registra el ingreso de una persona, siempre y cuando haya pasado el tiempo
  minimo desde su ultimo ingreso.

  Args:
    persona: Persona que ingreso.
    tiempo_actual: Tiempo actual en segundos.
    ultimos_ingresos: Diccionario con los ultimos ingresos de personas.
    mensajes_ingreso: Lista de mensajes de ingreso recientes.

  Returns:
    tuple (
      color: Color del recuadro de la persona (verde si hay coincidencia, rojo si no).
      tiempo_ultimo: Tiempo en segundos desde el ultimo ingreso.
    )
  """
  tiempo_ultimo = ultimos_ingresos.get(persona.id, 0)
  if tiempo_actual - tiempo_ultimo >= 60:
    ingreso = Ingreso(None, persona.id, datetime.now())
    DAOIngreso.crear(ingreso)
    threading.Thread(target=enviar_ingreso, args=({
      'codigo': persona.codigo,
      'nombres': persona.nombres,
      'apellidos': persona.apellidos,
      'fecha': ingreso.fecha.strftime('%Y-%m-%d'),
      'hora': datetime.now().strftime('%H:%M:%S')
    },)).start()
    ultimos_ingresos[persona.id] = tiempo_actual
    mensaje = [
      "Ingreso",
      f"DNI: {persona.dni}",
      f"Nombres: {persona.nombres}",
      f"Apellidos: {persona.apellidos}",
      f"Codigo: {persona.codigo}",
      f"Hora: {datetime.now().strftime('%H:%M:%S')}"
    ]
    logging.info(mensaje)
    mensajes_ingreso.append((mensaje, tiempo_actual + 5))
    return (0, 255, 0), tiempo_ultimo
  else:
    return (0, 255, 0), tiempo_ultimo

def dibujar_informacion(frame, nombre, color, bbox, tiempo_actual, tiempo_ultimo, encontrado):
  """
  Dibuja el recuadro del rostro, el nombre de la persona y la barra de cooldown (si aplica).

  Args:
    frame: Frame donde se dibujara la información.
    nombre: Nombre de la persona.
    color: Color del recuadro de la persona.
    bbox: Ubicacion del recuadro de la persona.
    tiempo_actual: Tiempo actual en segundos.
    tiempo_ultimo: Tiempo en segundos desde el ultimo ingreso.
    encontrado: Indica si la persona ha sido encontrada o no, para mostrar la barra de cooldown.
  """
  top, right, bottom, left = bbox
  cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
  cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
  cv2.putText(frame, nombre, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 0, 0), 1)

  # Barra de tiempo restante para reingreso
  if encontrado:
    porcentaje = max(0.0, 60.0 - (tiempo_actual - tiempo_ultimo)) / 60.0
    barra_ancho = int((right - left) * porcentaje)
    cv2.rectangle(frame, (left, top - 10), (left + barra_ancho, top - 5), (0, 255, 255), -1)

def dibujar_mensajes(frame, mensajes_ingreso, tiempo_actual):
  """
  Muestra los mensajes de ingreso recientes.

  Args:
    frame: Frame donde se dibujara la información.
    mensajes_ingreso: Lista de mensajes de ingreso recientes.
    tiempo_actual: Tiempo actual en segundos.
  """
  alto, ancho = frame.shape[:2]
  mensajes_ingreso[:] = [(msg, t) for msg, t in mensajes_ingreso if tiempo_actual < t]
  for i, (lineas, _) in enumerate(mensajes_ingreso):
    # Posición base para este bloque de texto
    x = ancho - 250
    y_base = 30 + i * 160  # Espacio entre mensajes

    # Calcular ancho máximo del texto para este bloque
    max_width = 0
    for linea in lineas:
      (w, _), _ = cv2.getTextSize(linea, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
      if w > max_width:
        max_width = w
    max_width += 20  # Margen adicional a ambos lados

    # Dibujar cada línea con ese ancho
    for j, linea in enumerate(lineas):
      (text_width, text_height), _ = cv2.getTextSize(linea, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
      y = y_base + j * 30
      cv2.rectangle(frame, (x, y - text_height - 5), (x + max_width, y + 10), (0, 255, 0), -1)
      cv2.putText(frame, linea, (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

def dibujar_pie_pagina(frame):
  """
  Muestra el mensaje de ayuda y el reloj en el pie del frame.

  Args:
    frame: Frame donde se dibujara la información.
  """
  alto, ancho = frame.shape[:2]

  # Mensaje de ayuda
  mensaje = "Presione R para actualizar - ESC para salir"
  (tw, th), _ = cv2.getTextSize(mensaje, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
  overlay = frame.copy()
  cv2.rectangle(overlay, (10, alto - 40), (10 + tw + 20, alto - 10), (0, 140, 255), -1)
  cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
  cv2.putText(frame, mensaje, (20, alto - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

  # Hora actual
  reloj = datetime.now().strftime("%H:%M:%S")
  (rw, rh), _ = cv2.getTextSize(reloj, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
  cv2.putText(frame, reloj, (ancho - rw - 10, alto - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

while True:
  # Captura y preprocesa el frame desde la camara.
  frame, _, small_frame = capturar_y_preprocesar(cap)
  if frame is None:
    continue

  # Detecta rostros y obtiene sus codificaciones
  face_locations, face_encodings = reconocer_rostros(small_frame)
  tiempo_actual = time.time()

  # Compara cada rostro con las personas conocidas
  for (top, right, bottom, left), encoding in zip(face_locations, face_encodings):
    top, right, bottom, left = top * 4, right * 4, bottom * 4, left * 4
    bbox = (top, right, bottom, left)

    # Identifica la persona que coincide con el rostro
    persona, _ = identificar_persona(encoding, personas)
    if persona:
      nombre = f"{persona.nombres} {persona.apellidos}"
      # Registra el ingreso de la persona, siempre y cuando haya pasado el tiempo minimo
      color, tiempo_ultimo = registrar_ingreso(persona, tiempo_actual, ultimos_ingresos, mensajes_ingreso)
      dibujar_informacion(frame, nombre, color, bbox, tiempo_actual, tiempo_ultimo, True)
    else:
      dibujar_informacion(frame, "No encontrado", (0, 0, 255), bbox, tiempo_actual, tiempo_actual, False)

  if not face_locations:
    cv2.putText(frame, "No se encuentran rostros", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

  dibujar_pie_pagina(frame)
  dibujar_mensajes(frame, mensajes_ingreso, tiempo_actual)

  # Muestra el frame actualizado con toda la información superpuesta
  cv2.imshow("Registro de ingresos en vivo", frame)

  # Teclas de control
  key = cv2.waitKey(1) & 0xFF
  ## Tecla de salida del bucle
  if key == 27: break
  ## Tecla para actualizar la lista de personas
  elif key == ord('r'):
    personas = DAOPersona.obtener_todos()
    logging.info("Lista de personas actualizada.")

cap.release()
cv2.destroyAllWindows()

logging.info("-------------- Se ha terminado el registro -------------")
logging.info("--------------------------------------------------------")