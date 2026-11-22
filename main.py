from abc import ABC, abstractmethod
from datetime import datetime
import logging

# Archivo de eventos
logging.basicConfig(filename='eventos.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
# Excepciones del sistema
class ErrorSistema(Exception):
    pass
class ErrorValidacion(ErrorSistema):
    pass
class ServicioNoDisponible(ErrorSistema):
    pass
class ErrorReserva(ErrorSistema):
    pass

# Clase general
class Entidad(ABC):
    @abstractmethod
    def descripcion(self):
        pass

# Clase cliente
class Cliente(Entidad):
    def __init__(self, identificacion, nombre, correo):
        self.__identificacion = self._texto(identificacion, 'identificacion')
        self.__nombre = self._texto(nombre, 'nombre')
        self.__correo = self._correo(correo)
    @staticmethod
    def _texto(valor, campo):
        if not isinstance(valor, str) or not valor.strip():
            raise ErrorValidacion(f'{campo} no valido')
        return valor.strip()
    @staticmethod
    def _correo(valor):
        if not isinstance(valor, str) or valor.count('@') != 1 or '.' not in valor.split('@')[-1]:
            raise ErrorValidacion('Correo no valido')
        return valor.strip()
    @property
    def identificacion(self):
        return self.__identificacion
    @property
    def nombre(self):
        return self.__nombre
    @property
    def correo(self):
        return self.__correo
    def descripcion(self):
        return f'{self.nombre} ({self.identificacion})'

# Clase servicio
class Servicio(Entidad, ABC):
    def __init__(self, codigo, nombre, tarifa, disponible=True):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ErrorValidacion('Codigo no valido')
        if not isinstance(nombre, str) or not nombre.strip():
            raise ErrorValidacion('Nombre de servicio no valido')
        if isinstance(tarifa, bool) or not isinstance(tarifa, (int, float)) or not 0 < tarifa < float('inf'):
            raise ErrorValidacion('Tarifa no valida')
        self.codigo = codigo.strip()
        self.nombre = nombre.strip()
        self.tarifa = tarifa
        self.disponible = disponible
    def validar(self, duracion):
        if isinstance(duracion, bool) or not isinstance(duracion, int) or duracion <= 0:
            raise ErrorValidacion('Duracion debe ser un entero positivo')
        if not self.disponible:
            raise ServicioNoDisponible(f'{self.nombre} no disponible')
    @abstractmethod
    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        pass
    def aplicar_ajustes(self, subtotal, descuento=0, impuesto=0):
        if not all(isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 100 for x in (descuento, impuesto)):
            raise ErrorValidacion('Descuento o impuesto no valido')
        return round(subtotal * (1 - descuento / 100) * (1 + impuesto / 100), 2)

# Servicio de salas
class Sala(Servicio):
    def __init__(self, codigo, nombre, tarifa, capacidad, disponible=True):
        super().__init__(codigo, nombre, tarifa, disponible)
        if isinstance(capacidad, bool) or not isinstance(capacidad, int) or capacidad <= 0:
            raise ErrorValidacion('Capacidad no valida')
        self.capacidad = capacidad
    def validar(self, duracion):
        super().validar(duracion)
        if duracion > 12:
            raise ErrorValidacion('Maximo 12 horas para salas')
    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        self.validar(duracion)
        return self.aplicar_ajustes(self.tarifa * duracion, descuento, impuesto)
    def descripcion(self):
        return f'Sala {self.nombre}, capacidad {self.capacidad}'

# Servicio de equipos
class Equipo(Servicio):
    def __init__(self, codigo, nombre, tarifa, tipo, disponible=True):
        super().__init__(codigo, nombre, tarifa, disponible)
        if not isinstance(tipo, str) or not tipo.strip():
            raise ErrorValidacion('Tipo de equipo no valido')
        self.tipo = tipo.strip()
    def validar(self, duracion):
        super().validar(duracion)
        if duracion > 30:
            raise ErrorValidacion('Maximo 30 dias para equipos')
    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        self.validar(duracion)
        return self.aplicar_ajustes(self.tarifa * duracion, descuento, impuesto)
    def descripcion(self):
        return f'Equipo {self.nombre}, tipo {self.tipo}'

# Servicio de asesorias
class Asesoria(Servicio):
    def __init__(self, codigo, nombre, tarifa, especialidad, disponible=True):
        super().__init__(codigo, nombre, tarifa, disponible)
        if not isinstance(especialidad, str) or not especialidad.strip():
            raise ErrorValidacion('Especialidad no valida')
        self.especialidad = especialidad.strip()
    def validar(self, duracion):
        super().validar(duracion)
        if duracion > 8:
            raise ErrorValidacion('Maximo 8 horas para asesorias')
    def calcular_costo(self, duracion, descuento=0, impuesto=0):
        self.validar(duracion)
        return self.aplicar_ajustes(self.tarifa * duracion, descuento, impuesto)
    def descripcion(self):
        return f'Asesoria {self.nombre}, especialidad {self.especialidad}'

# Clase reserva
class Reserva(Entidad):
    def __init__(self, numero, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente) or not isinstance(servicio, Servicio):
            raise ErrorValidacion('Cliente o servicio no valido')
        servicio.validar(duracion)
        self.numero = numero
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = duracion
        self.estado = 'pendiente'
        self.total = 0
    def confirmar(self):
        if self.estado != 'pendiente':
            raise ErrorReserva('Solo se confirman reservas pendientes')
        self.estado = 'confirmada'
        logging.info('Reserva %s confirmada', self.numero)
    def cancelar(self):
        if self.estado == 'cancelada':
            raise ErrorReserva('Reserva ya cancelada')
        self.estado = 'cancelada'
        logging.info('Reserva %s cancelada', self.numero)
    def procesar(self, descuento=0, impuesto=0):
        try:
            if self.estado != 'pendiente':
                raise ErrorReserva('La reserva no esta pendiente')
            self.total = self.servicio.calcular_costo(self.duracion, descuento, impuesto)
        except (ErrorSistema, TypeError, ValueError) as error:
            logging.error('Error procesando reserva %s: %s', self.numero, error)
            raise ErrorReserva('No se pudo procesar la reserva') from error
        else:
            self.confirmar()
            return self.total
        finally:
            logging.info('Procesamiento finalizado para reserva %s', self.numero)
    def descripcion(self):
        return f'Reserva {self.numero}: {self.cliente.nombre}, {self.servicio.nombre}, {self.estado}'

# Sistema principal
class Sistema:
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []
    def registrar_cliente(self, identificacion, nombre, correo):
        if any(c.identificacion == identificacion for c in self.clientes):
            raise ErrorValidacion('Identificacion repetida')
        cliente = Cliente(identificacion, nombre, correo)
        self.clientes.append(cliente)
        logging.info('Cliente registrado: %s', cliente.identificacion)
        return cliente
    def registrar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion('Servicio no valido')
        if any(s.codigo == servicio.codigo for s in self.servicios):
            raise ErrorValidacion('Codigo de servicio repetido')
        self.servicios.append(servicio)
        logging.info('Servicio registrado: %s', servicio.codigo)
        return servicio
    def crear_reserva(self, identificacion, codigo, duracion):
        cliente = next((c for c in self.clientes if c.identificacion == identificacion), None)
        servicio = next((s for s in self.servicios if s.codigo == codigo), None)
        if cliente is None or servicio is None:
            raise ErrorReserva('Cliente o servicio no encontrado')
        reserva = Reserva(len(self.reservas) + 1, cliente, servicio, duracion)
        self.reservas.append(reserva)
        logging.info('Reserva creada: %s', reserva.numero)
        return reserva

def ejecutar_prueba(numero, nombre, accion):
    print(f'\nPrueba {numero}: {nombre}')
    try:
        resultado = accion()
    except Exception as error:
        logging.error('Prueba %s fallo: %s', numero, error)
        print(f'Error controlado: {error}')
    else:
        print(f'Correcto: {resultado}')
    finally:
        print('Prueba finalizada')

# Pruebas sistema
def main():
    sistema = Sistema()
    datos = {}
    def cliente_valido():
        datos['cliente'] = sistema.registrar_cliente('1001', 'Ana Perez', 'ana@correo.com')
        return datos['cliente'].descripcion()
    def sala_valida():
        sistema.registrar_servicio(Sala('S1', 'Reuniones', 40000, 12))
        return 'Sala registrada'
    def equipo_valido():
        sistema.registrar_servicio(Equipo('E1', 'Portatil', 60000, 'Computador'))
        return 'Equipo registrado'
    def asesoria_valida():
        sistema.registrar_servicio(Asesoria('A1', 'Programacion', 80000, 'Python'))
        return 'Asesoria registrada'
    def reserva_valida():
        datos['reserva'] = sistema.crear_reserva('1001', 'S1', 2)
        return f'Total ${datos["reserva"].procesar():,.0f}'
    def reserva_descuento():
        reserva = sistema.crear_reserva('1001', 'A1', 2)
        return f'Total con descuento e impuesto ${reserva.procesar(10, 19):,.0f}'
    def cancelar_reserva():
        datos['reserva'].cancelar()
        return datos['reserva'].descripcion()
    pruebas = [
        ('Cliente valido', cliente_valido),
        ('Cliente invalido', lambda: sistema.registrar_cliente('1002', '', 'malcorreo')),
        ('Sala valida', sala_valida),
        ('Equipo valido', equipo_valido),
        ('Asesoria valida', asesoria_valida),
        ('Servicio invalido', lambda: sistema.registrar_servicio(Sala('S2', 'Sala mala', -5, 10))),
        ('Reserva exitosa', reserva_valida),
        ('Reserva con ajustes', reserva_descuento),
        ('Reserva fallida', lambda: sistema.crear_reserva('1001', 'E1', -3)),
        ('Servicio inexistente', lambda: sistema.crear_reserva('1001', 'X9', 2)),
        ('Cancelar reserva', cancelar_reserva),
        ('Cliente repetido', lambda: sistema.registrar_cliente('1001', 'Otro', 'otro@correo.com')),
        ('Servicio no disponible', lambda: sistema.registrar_servicio(Equipo('E2', 'Proyector', 30000, 'Video', False))),
    ]
    for numero, (nombre, accion) in enumerate(pruebas, 1):
        ejecutar_prueba(numero, nombre, accion)

    ejecutar_prueba(14, 'Reserva no disponible', lambda: sistema.crear_reserva('1001', 'E2', 1))
    print(f'\nClientes: {len(sistema.clientes)} | Servicios: {len(sistema.servicios)} | Reservas: {len(sistema.reservas)}')
    print('Eventos y errores guardados en eventos.log')
if __name__ == '__main__':
    main()
