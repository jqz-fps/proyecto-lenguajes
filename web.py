from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO
import dao.dao_persona as DAOPersona, dao.dao_ingreso as DAOIngreso
from model.Persona import Persona
from datetime import datetime, timedelta
import face_recognition
import calendar
import locale
import re

locale.setlocale(locale.LC_TIME, 'Spanish_Spain')

app = Flask(__name__,
  template_folder='web/templates',
  static_folder='web/static'
)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/')
def ingresos():
  ingresos = DAOIngreso.obtener_todos()
  personas = DAOPersona.obtener_todos()
  personas_dict = {p.id: p for p in personas}

  for ingreso in ingresos:
    ingreso.persona = personas_dict.get(ingreso.id_persona)
  
  return render_template('ingresos.html', ingresos=ingresos)

@app.route('/ingresos/nuevo', methods=['POST'])
def ingresos_nuevo():
  data = request.get_json()
  socketio.emit('nuevo_ingreso', data)
  return '', 204

@app.route('/resumen')
def resumen():
  ingresos = DAOIngreso.obtener_todos()

  hoy = datetime.now().date()

  inicio_semana = hoy - timedelta(days=hoy.weekday())
  fin_semana = inicio_semana + timedelta(days=6)

  inicio_mes = hoy.replace(day=1)
  fin_mes = hoy.replace(day=calendar.monthrange(hoy.year, hoy.month)[1])

  conteo_semana = {}
  conteo_mes = {}

  for ingreso in ingresos:
    fecha = ingreso.fecha
    if isinstance(fecha, str):
      fecha = datetime.fromisoformat(fecha)
    fecha = fecha.date()
    fecha_str = fecha.isoformat()

    if inicio_semana <= fecha <= fin_semana:
      conteo_semana[fecha_str] = conteo_semana.get(fecha_str, 0) + 1

    if inicio_mes <= fecha <= fin_mes:
      conteo_mes[fecha_str] = conteo_mes.get(fecha_str, 0) + 1

  fechas_semana = [
    (inicio_semana + timedelta(days=i)).isoformat()
    for i in range(7)
  ]
  chart_labels_last_week = [
    (inicio_semana + timedelta(days=i)).strftime("%a")
    for i in range(7)
  ]
  chart_data_last_week = [conteo_semana.get(fecha, 0) for fecha in fechas_semana]

  dias_en_mes = (fin_mes - inicio_mes).days + 1
  fechas_mes = [
    (inicio_mes + timedelta(days=i)).isoformat()
    for i in range(dias_en_mes)
  ]
  chart_labels_last_month = [
    (inicio_mes + timedelta(days=i)).day
    for i in range(dias_en_mes)
  ]
  chart_data_last_month = [conteo_mes.get(fecha, 0) for fecha in fechas_mes]

  return render_template('resumen.html',
                           chart_labels_last_week=chart_labels_last_week,
                           chart_data_last_week=chart_data_last_week,
                           chart_labels_last_month=chart_labels_last_month,
                           chart_data_last_month=chart_data_last_month
  )

@app.route('/personas')
def personas():
  personas = DAOPersona.obtener_todos()
  return render_template('personas.html', personas=personas)

@app.route('/personas/detalle/<int:id>')
def persona(id):
  if id is None:
    return "ID no proporcionado", 400

  persona = DAOPersona.obtener(id)
  if persona is None:
    return "Persona no encontrada", 404

  ingresos = DAOIngreso.obtener_por_persona(id)

  hoy = datetime.now().date()
  hace_7_dias = hoy - timedelta(days=8)
    
  conteo_semana = {}

  for ingreso in ingresos:
    fecha = ingreso.fecha
    if isinstance(fecha, str):
      fecha = datetime.fromisoformat(fecha)

    fecha_str = fecha.date().isoformat()

    if fecha.date() >= hace_7_dias:
      if fecha_str in conteo_semana:
        conteo_semana[fecha_str] += 1
      else:
        conteo_semana[fecha_str] = 1

  chart_labels_last_week = sorted(conteo_semana.keys())
  chart_data_last_week = [conteo_semana[f] for f in chart_labels_last_week]

  return render_template('detalle.html',
                           persona=persona,
                           ingresos=ingresos,
                           chart_labels_last_week=chart_labels_last_week,
                           chart_data_last_week=chart_data_last_week
  )

@app.route('/agregar', methods=['GET'])
def agregar():
  return render_template('agregar.html')

@app.route('/agregar', methods=['POST'])
def agregar_persona():
  personas = DAOPersona.obtener_todos()
  dni = request.form.get('dni')
  codigo = request.form.get('codigo')
  nombres = request.form.get('nombres')
  apellidos = request.form.get('apellidos')
  foto = request.files.get('foto')

  if dni is None:
    return render_template('agregar.html', error="El DNI es obligatorio")
  if codigo is None:
    return render_template('agregar.html', error="El Código es obligatorio")
  if nombres is None:
    return render_template('agregar.html', error="Los nombres son obligatorios")
  if apellidos is None:
    return render_template('agregar.html', error="Los apellidos son obligatorios")

  if not re.match(r'^\d{8}$', dni):
    return render_template('agregar.html', error="El DNI debe tener 8 dígitos")
  if not re.match(r'^U\d{8}$', codigo):
    return render_template('agregar.html', error="El Código debe empezar con U y tener 8 dígitos")

  for persona in personas:
    if persona.dni == dni:
      return render_template('agregar.html', error="Ya existe una persona con ese DNI")
    if persona.codigo == codigo:
      return render_template('agregar.html', error="Ya existe una persona con ese Código")
    
  face = face_recognition.load_image_file(foto)
  face_locations = face_recognition.face_locations(face)
  if not face_locations:
    return render_template('agregar.html', error="No se encontró ninguna cara en la foto")
  elif len(face_locations) > 1:
    return render_template('agregar.html', error="La foto contiene más de una cara")
  
  face_encoding = face_recognition.face_encodings(face, known_face_locations=[face_locations[0]])[0]
  encoding_blob = face_encoding.tobytes()

  persona = Persona(-1, dni, codigo, nombres, apellidos, encoding_blob)
  DAOPersona.crear(persona)
  
  return redirect(url_for('personas'))

if __name__ == '__main__':
  socketio.run(app, debug=True)