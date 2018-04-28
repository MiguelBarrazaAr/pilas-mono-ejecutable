# -*- encoding: utf-8 -*-
# pilas engine accesible
# License: LGPLv3 (see http://www.gnu.org/licenses/lgpl.html)
#
# repository - http://github.com/barrazamiguel/pilas-ejecutable
import random
import inspect
import traceback
import importlib

from pilasengine.actores.actor import Actor
from pilasengine.actores.actor_invisible import ActorInvisible
from pilasengine.actores.animacion import Animacion
import pilasengine



#from pilasengine.actores.texto import Texto
#from pilasengine.actores.grupo import Grupo
#from pilasengine.actores.temporizador import Temporizador



class Actores(object):
    """Representa la forma de acceso y construcción de actores.

    Esta clase representa el objeto creado por pilas que
    se puede acceder escribiendo ``pilas.actores``. Desde aquí
    se puede acceder a los actores pre-diseñados de pilas y
    agregarlos a la escena.

    Por ejemplo, para crear una nave en pantalla podemos escribir:

        >>> nave = pilas.actores.Nave()

    """
    _lista_actores_personalizados = []

    def __init__(self, pilas):
        self.pilas = pilas
        self._diccionario_de_actores = {}
        self._vincular_todos_los_actores_estandar()

    def obtener_clases(self):
        return self._diccionario_de_actores

    def obtener_clase_por_nombre(self, nombre_de_la_clase):
        for k, v in self._diccionario_de_actores.items():
            if nombre_de_la_clase.lower() in [k, k.lower()]:
                return v
        else:
            raise NameError("La muncion " + nombre_de_la_clase + " no coincide con ninguna clase de actor conocida.")

    def vincular_actor_estandar(self, modulo, clase):
        referencia_a_modulo = importlib.import_module('pilasengine.actores.' + modulo)
        referencia_a_clase = getattr(referencia_a_modulo, clase)
        self._diccionario_de_actores[clase] = referencia_a_clase

    def vincular_actor_personalizado(self, nombre_de_clase, referencia_a_clase):
        self._diccionario_de_actores[nombre_de_clase] = referencia_a_clase

    def vincular(self, clase_del_actor):
        """Permite vincular una clase de actor con pilas.

        Esto permite de después el actor se pueda crear desde
        el módulo "pilas.actores".

        Por ejemplo, si tengo una clase ``MiActor`` lo puedo
        vincular con:

            >>> pilas.actores.vincular(MiActor)
            >>> mi_actor = pilas.actores.MiActor()

        """

        if not issubclass(clase_del_actor, Actor):
            raise Exception("Solo se pueden vincular clases que heredan de\
                            pilasengine.actores.Actor")

        def metodo_crear_actor(self, *k, **kw):
            try:
                nuevo_actor = clase_del_actor(self.pilas, *k, **kw)
                return nuevo_actor
            except TypeError, error:
                if not self.pilas.modo_test:
                    print traceback.format_exc()
                mensaje_extendido = "\n\t(en la clase %s ya que se llamó con los argumentos: %s %s" %(str(clase_del_actor.__name__), str(k), str(kw))
                raise TypeError(str(error) + mensaje_extendido)

        nombre_del_actor = clase_del_actor.__name__
        existe = getattr(self.__class__, nombre_del_actor, None)

        if existe:
            raise Exception("Lo siento, ya existe un actor con el nombre " +
                            nombre_del_actor)

        setattr(self.__class__, nombre_del_actor, metodo_crear_actor)
        Actores._lista_actores_personalizados.append(nombre_del_actor)
        self.vincular_actor_personalizado(nombre_del_actor, clase_del_actor)

    def obtener_actores_personalizados(self):
        "Retorna una lista con todos los nombres de actores personalizados."
        return Actores._lista_actores_personalizados

    def eliminar_actores_personalizados(self):
        "Recorre todos los actores personalizados y los elimina."
        for x in Actores._lista_actores_personalizados:
            delattr(self.__class__, x)

        Actores._lista_actores_personalizados = []

    def agregar_actor(self, actor):
        """Agrega un actor a la escena actual.

        Este método se ejecuta internamente cada vez que se
        contruye un actor escribiendo algo como:

            >>> actor = pilas.actores.Actor()
        """
        if isinstance(actor, Actor):
            escena_actual = self.pilas.obtener_escena_actual()

            self.pilas.log("Iniciando el actor, llamando a actor.iniciar() del objeto ", actor)

            # Toma los argumentos del actor y los envía directamente
            # al método iniciar.
            k = actor.argumentos_adicionales[0]
            kv = actor.argumentos_adicionales[1]

            falla_pre_iniciar = False
            mensaje_error_pre_iniciar = ""

            try:
                actor.pre_iniciar(*k, **kv)
            except TypeError, error:
                #print "ERROR en " + actor.__class__.__name__ + ":"
                #print traceback.format_exc()
                falla_pre_iniciar = True
                mensaje_error_pre_iniciar = str(error)

            try:
                actor.iniciar(*k, **kv)
            except TypeError, error:
                if not self.pilas.modo_test:
                    print traceback.format_exc()

                    if falla_pre_iniciar:
                        print("Tambien ocurrio un error al pre_iniciar" + mensaje_error_pre_iniciar)

                # el siguiente metodo, _validar_argumentos, intentará
                # dar una descripción mas detallada de los argumentos que
                # faltan.
                self._validar_argumentos("iniciar", actor.__class__.__name__, actor.iniciar, k, kv)
                raise TypeError(error)

            self.pilas.log("Agregando el actor", actor, "en la escena", escena_actual)
            escena_actual.agregar_actor(actor)
        else:
            raise Exception("Solo puedes agregar actores de esta forma.")

        return actor

    def _validar_argumentos(self, metodo, nombre_clase, funcion, k, kv):
        """Se asegura que la función iniciar del actor
        se pueda ejecutar con los argumentos indicados."""

        argumentos_esperados = inspect.getargspec(funcion)
        args = argumentos_esperados[0]
        defaults = argumentos_esperados[3]

        if defaults:
            cantidad_de_argumentos_opcionales = len(defaults)
        else:
            cantidad_de_argumentos_opcionales = 0

        args.remove('self')

        if len(args) == 0:
            mensaje_argumentos = "El método '%s' no espera ningún argumento." %(metodo)
        else:
            mensaje_argumentos = "El método '%s' espera estos %d argumentos: %s" %(metodo, len(args), str(args))

        titulo_error = "No se puede llamar al metodo '%s' de la clase '%s'" %(metodo, nombre_clase)

        # Lanza un error si se invoca a el constructor con argumentos
        # posiciones. Es decir, siempre se tiene que llamar al constructor
        # especificando el nombre de cada argumento.
        #
        # Por ejemplo, esto sería correcto:
        #
        #        Actor(x=100, y=300, otro='pepe')
        #
        # Mientras que esto arrojaría un error si o si:
        #
        #        Actor(100, 300, 'pepe')
        #
        if k:
            mensaje = "El método tiene que ser invocado especificando el nombre de cada argumento, no con los valores posicionales directamente como aquí: " + ', '.join([str(x) for x in k])
            raise TypeError("%s.\n\t%s." %(titulo_error, mensaje))

        # Busca los argumentos nombrados y los excluye de la lista
        # de argumentos esperados por la función.
        # Si encuentra argumentos no esperados, lanza una excepción.
        #
        argumentos_esperados = args[:]

        for (key, _) in kv.items():
            if key in argumentos_esperados:
                argumentos_esperados.remove(key)
            else:
                raise TypeError("%s.\n\n\tNo se esperaba el argumento '%s'. %s" %(titulo_error, key, mensaje_argumentos))

        # Trata de quitar los argumentos opcionales si existen.
        for x in range(cantidad_de_argumentos_opcionales):
            if argumentos_esperados:
                argumentos_esperados.pop()

        cantidad_de_argumentos = len(argumentos_esperados)

        if cantidad_de_argumentos > 0:
            if cantidad_de_argumentos == 1:
                detalle = "Falta el argumento: " + argumentos_esperados[0]
            else:
                detalle = "Faltan %d argumentos: %s" %(cantidad_de_argumentos, ', '.join(argumentos_esperados))

            raise TypeError("%s.\n\t%s.\n\t%s" %(titulo_error, detalle, mensaje_argumentos))

    def agregar_grupo(self, grupo):
        if isinstance(grupo, Grupo):
            escena_actual = self.pilas.obtener_escena_actual()
            self.pilas.log("Agregando el grupo", grupo, "a la escena",
                           escena_actual)
            escena_actual.agregar_grupo(grupo)
        else:
            raise Exception("Solo puedes agregar grupos de esta forma.")

        return grupo

    ## --------------------
    ## Acceso a los actores
    ## --------------------


    def listar_actores(self):
        return list(self.pilas.obtener_escena_actual()._actores)
    
    def Ejes(self, x=0, y=0):
        ":rtype: ejes.Ejes"
        return self._crear_actor('ejes', 'Ejes', x=x, y=y)
    
    def Mono(self, x=0, y=0):
        ":rtype: mono.Mono"
        return self._crear_actor('mono', 'Mono', x=x, y=y)
    
    def Bala(self, x=0, y=0, rotacion=0, velocidad_maxima=9,
             angulo_de_movimiento=90):
        ":rtype: bala.Bala"
        return self._crear_actor('bala', 'Bala',
                                 x=x, y=y, rotacion=rotacion,
                                 velocidad_maxima=velocidad_maxima,
                                 angulo_de_movimiento=angulo_de_movimiento)
    
    def Actor(self, x=0, y=0, imagen='sin_imagen.png'):
        ":rtype: actor.Actor"
        return self._crear_actor('actor', 'Actor', x=x, y=y, imagen=imagen)

    def ActorInvisible(self, x=0, y=0, imagen='sin_imagen.png'):
        ":rtype: actor_invisible.ActorInvisible"
        return self._crear_actor('actor_invisible', 'ActorInvisible', x=x, y=y, imagen=imagen)

    def Puntaje(self, x=0, y=0, color='negro', texto='0'):
        ":rtype: puntaje.Puntaje"
        return self._crear_actor('puntaje', 'Puntaje', texto=texto, x=x, y=y, color=color)

    def CursorMano(self, x=0, y=0):
        ":rtype: cursor_mano.CursorMano"
        return self._crear_actor('cursor_mano', 'CursorMano', x=x, y=y)

    def Sonido(self, x=0, y=0):
        return self._crear_actor('sonido', 'Sonido', x=x, y=y)

    def Menu(self, opciones=[], x=0, y=0, fuente=None,
             color_normal=pilasengine.colores.gris, color_resaltado=pilasengine.colores.blanco):
        ":rtype: menu.Menu"
        return self._crear_actor('menu', 'Menu', x=x, y=y, opciones=opciones,
                                 fuente=fuente, color_normal=color_normal,
                                 color_resaltado=color_resaltado)

    def Opcion(self, texto="", x=0, y=0,
                 funcion_a_invocar=None,argumentos=None,fuente=None,
                 color_normal=pilasengine.colores.gris,
                 color_resaltado=pilasengine.colores.blanco):
        ":rtype: opcion.Opcion"
        return self._crear_actor("opcion", "Opcion", x=x, y=y,
                                 texto=texto,
                                 funcion_a_invocar=funcion_a_invocar,
                                 argumentos=argumentos, fuente=fuente,
                                 color_normal=color_normal,
                                 color_resaltado=color_resaltado)

    def MensajeError(self, error, descripcion):
        ":rtype: mensaje_error.MensajeError"

        return self._crear_actor('mensaje_error', 'MensajeError', error,
                                 descripcion)
    
    def Animacion(self, grilla='sin_imagen.png', ciclica=False, x=0, y=0, velocidad=10):
        ":rtype: animacion.Animacion"
        return self._crear_actor('animacion', 'Animacion', grilla=grilla,
                                 ciclica=ciclica, x=x, y=y, velocidad=velocidad)
    
    def Grupo(self):
        ":rtype: grupo.Grupo"
        import grupo
        nuevo_grupo = grupo.Grupo(self.pilas)
        return self.agregar_grupo(nuevo_grupo)
    
    def Dialogo(self):
        ":rtype: dialogo.Dialogo"
        return self._crear_actor('dialogo', 'Dialogo')
    
    def Energia(self, x=0, y=0, progreso=100, ancho=200, alto=30,
                color_relleno=pilasengine.colores.amarillo, con_sombra=True,
                con_brillo=True):
        ":rtype: energia.Energia"
        return self._crear_actor('energia', 'Energia', x=x, y=y,
                                 progreso=progreso, ancho=ancho, alto=alto,
                                 color_relleno=color_relleno,
                                 con_sombra=con_sombra,
                                 con_brillo=con_brillo)
    
    def Boton(self, x=0, y=0,
                ruta_normal='boton/boton_normal.png',
                ruta_press='boton/boton_press.png',
                ruta_over='boton/boton_over.png'):
        ":rtype: boton.Boton"
        return self._crear_actor('boton', 'Boton', x=x, y=y,
                                 ruta_normal=ruta_normal,
                                 ruta_press=ruta_press,
                                 ruta_over=ruta_over)

    def Explosion(self, x=0, y=0):
        ":rtype: explosion.Explosion"
        return self._crear_actor('explosion', 'Explosion', x=x, y=y)

    def ExplosionDeHumo(self, x=0, y=0):
        ":rtype: explosion_de_humo.ExplosionDeHumo"
        return self._crear_actor('explosion_de_humo', 'ExplosionDeHumo', x=x, y=y)

    def Humo(self, x=0, y=0):
        ":rtype: humo.Humo"
        return self._crear_actor('humo', 'Humo', x=x, y=y)

    def Sombra(self, x=0, y=0):
        ":rtype: sombra.Sombra"
        return self._crear_actor('sombra', 'Sombra', x=x, y=y)

    def Globo(self, texto="sin texto", x=0, y=0, dialogo=None, avance_con_clicks=True,
              autoeliminar=False, ancho_globo=0, alto_globo=0, objetivo=None):
        ":rtype: globo.Globo"
        return self._crear_actor('globo', 'Globo', texto=texto, x=x, y=y,
                                 dialogo=dialogo,
                                 avance_con_clicks=avance_con_clicks,
                                 autoeliminar=autoeliminar,
                                 ancho_globo=ancho_globo,
                                 alto_globo=alto_globo,
                                 objetivo=objetivo)

    def Texto(self, cadena_de_texto="Sin texto", magnitud=20, vertical=False,
              fuente=None, fijo=True, ancho=0, x=0, y=0):
        ":rtype: texto.Texto"
        import texto
        nuevo_actor = texto.Texto(self.pilas, cadena_de_texto, magnitud,
                                  vertical, fuente, fijo, ancho, x, y)
        return nuevo_actor

    def TextoInferior(self, texto="Sin texto", magnitud=20, retraso=5):
        ":rtype: texto_inferior.TextoInferior"
        import texto_inferior
        nuevo_actor = texto_inferior.TextoInferior(self.pilas, texto, magnitud,
                                                   retraso=retraso)
        return nuevo_actor

    def DeslizadorHorizontal(self, x=0, y=0, min=0, max=100, etiqueta=''):
        ":rtype: deslizador_horizontal.DeslizadorHorizontal"
        return self._crear_actor('deslizador_horizontal',
                                 'DeslizadorHorizontal',
                                 x=x, y=y, _min=min, _max=max,
                                 etiqueta=etiqueta)

    def Emisor(self, x=0, y=0):
        ":rtype: emisor.Emisor"
        return self._crear_actor('emisor', 'Emisor', x=x, y=y)

    def Controlador(self, x=0, y=0):
        ":rtype: controlador.Controlador"
        return self._crear_actor('controlador', 'Controlador', x=x, y=y)

    def Temporizador(self, x=0, y=0):
        ":rtype: temporizador.Temporizador"
        return self._crear_actor('temporizador', 'Temporizador', x=x, y=y)

    def ManejadorPropiedad(self, x, y, actor, propiedad, minimo, maximo):
        ":rtype: manejador_propiedad.ManejadorPropiedad"
        return self._crear_actor('manejador_propiedad',
                                 'ManejadorPropiedad',
                                 x, y,
                                 actor=actor, propiedad=propiedad,
                                 _min=minimo, _max=maximo)

    def Particula(self, emisor=None, x=0, y=0, dx=0, dy=0, imagen="particula.png", vida=1):
        ":rtype: particula.Particula"
        actor = self._crear_actor('particula', 'Particula', emisor=emisor,
                                  x=x, y=y,
                                  dx=dx, dy=dy,
                                  imagen=imagen,
                                  vida=vida)
        return actor

    def _crear_actor(self, modulo, clase, *k, **kw):

        referencia_a_modulo = importlib.import_module('pilasengine.actores.' + modulo)
        referencia_a_clase = getattr(referencia_a_modulo, clase)

        try:
            nuevo_actor = referencia_a_clase(self.pilas, *k, **kw)
        except TypeError, error:
            mensaje_extendido = "\n\t(en la clase %s ya que se llamó con los argumentos: %s %s" %(str(referencia_a_clase.__name__), str(k), str(kw))
            raise TypeError(str(error) + mensaje_extendido)

        # Importante: cuando se inicializa el actor, el método __init__
        #             realiza una llamada a pilas.actores.agregar_actor
        #             para vincular el actor a la escena.
        return nuevo_actor

    def fabricar(self, clase, cantidad):
        grupo = self.Grupo()
        ancho_ventana, alto_ventana = self.pilas.widget.obtener_area()

        for i in xrange(cantidad):
            _x = random.randint(-ancho_ventana/2, ancho_ventana/2)
            _y = random.randint(-alto_ventana/2, alto_ventana/2)

            try:
                actor = clase(self.pilas)
                actor.x = _x
                actor.y = _y
            except TypeError:
                actor = clase(self.pilas, x=_x, y=_y)

            grupo.agregar(actor)

        return grupo

    def _vincular_todos_los_actores_estandar(self):
        self.vincular_actor_estandar('actor', 'Actor')
        self.vincular_actor_estandar('texto', 'Texto')
        self.vincular_actor_estandar('texto_inferior', 'TextoInferior')
        self.vincular_actor_estandar('mono', 'Mono')
        self.vincular_actor_estandar('actor', 'Actor')
        self.vincular_actor_estandar('actor_invisible', 'ActorInvisible')
        self.vincular_actor_estandar('ejes', 'Ejes')
        self.vincular_actor_estandar('puntaje', 'Puntaje')
        self.vincular_actor_estandar('cursor_mano', 'CursorMano')
        self.vincular_actor_estandar('sonido', 'Sonido')
        self.vincular_actor_estandar('menu', 'Menu')
        self.vincular_actor_estandar("opcion", "Opcion")
        self.vincular_actor_estandar('mensaje_error', 'MensajeError')
        self.vincular_actor_estandar('animacion', 'Animacion')
        self.vincular_actor_estandar('dialogo', 'Dialogo')
        self.vincular_actor_estandar('energia', 'Energia')
        self.vincular_actor_estandar('boton', 'Boton')
        self.vincular_actor_estandar('explosion', 'Explosion')
        self.vincular_actor_estandar('explosion_de_humo', 'ExplosionDeHumo')
        self.vincular_actor_estandar('humo', 'Humo')
        self.vincular_actor_estandar('sombra', 'Sombra')
        self.vincular_actor_estandar('globo', 'Globo')
        self.vincular_actor_estandar('deslizador_horizontal', 'DeslizadorHorizontal')
        self.vincular_actor_estandar('emisor', 'Emisor')
        self.vincular_actor_estandar('controlador', 'Controlador')
        self.vincular_actor_estandar('temporizador', 'Temporizador')
        self.vincular_actor_estandar('manejador_propiedad', 'ManejadorPropiedad')


from pilasengine.actores.actor import ActorEliminadoException
from pilasengine.actores.actor import ActorEliminado
from pilasengine.actores.actor import Actor
from pilasengine.actores.animacion import Animacion
from pilasengine.actores.animado import Animado
from pilasengine.actores.bala import Bala
from pilasengine.actores.boton import Boton
from pilasengine.actores.controlador import Controlador
from pilasengine.actores.deslizador_horizontal import DeslizadorHorizontal
from pilasengine.actores.dialogo import Dialogo
from pilasengine.actores.ejes import Ejes
from pilasengine.actores.emisor import Emisor
from pilasengine.actores.energia import Energia
from pilasengine.actores.estudiante import Estudiante
from pilasengine.actores.explosion import Explosion
from pilasengine.actores.explosion_de_humo import ExplosionDeHumo
from pilasengine.actores.globo import Globo
from pilasengine.actores.grupo import Grupo
from pilasengine.actores.humo import Humo
from pilasengine.actores.manejador_propiedad import ManejadorPropiedad
from pilasengine.actores.mensaje_error import MensajeError
from pilasengine.actores.menu import Menu
from pilasengine.actores.menu import Menu
from pilasengine.actores.mono import Mono
from pilasengine.actores.municion import Municion
from pilasengine.actores.opcion import Opcion
from pilasengine.actores.particula import Particula
from pilasengine.actores.puntaje import Puntaje
from pilasengine.actores.sombra import Sombra
from pilasengine.actores.sonido import Sonido
from pilasengine.actores.temporizador import Temporizador
from pilasengine.actores.texto import Texto
from pilasengine.actores.texto_inferior import TextoInferior
