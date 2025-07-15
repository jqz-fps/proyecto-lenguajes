class Ingreso:
  def __init__(self, id, id_persona, fecha):
    self.id = id
    self.id_persona = id_persona
    self.fecha = fecha

  def __str__(self):
    return f"ID: {self.id}\tID Persona: {self.id_persona}\tFecha: {self.fecha}"