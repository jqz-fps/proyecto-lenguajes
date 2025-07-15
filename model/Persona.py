class Persona:
  def __init__(self, id, dni, codigo, nombres, apellidos, encoding):
    self.id = id
    self.dni = dni
    self.codigo = codigo
    self.nombres = nombres
    self.apellidos = apellidos
    self.encoding = encoding

  def __str__(self):
    return f"ID: {self.id}\tDNI: {self.dni}\tCodigo: {self.codigo}\tNombres: {self.nombres}\tApellidos: {self.apellidos}\tEncoding: {self.encoding}"