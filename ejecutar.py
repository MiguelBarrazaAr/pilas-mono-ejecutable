# -*- encoding: utf-8 -*-
import pilasengine

pilas = pilasengine.iniciar(titulo="alpha test")

try:
    pilas.forzar_habilitacion_de_audio()
except AttributeError:
    print("Omitiendo forzar la inicializacion, version anterior a 1.4.8")

music = pilas.musica.cargar("audio/rayman.ogg")

class MonoConControles(pilasengine.actores.mono.Mono):
    
    def iniciar(self):
        self.imagen = "mono.png"
        self.sonido = pilas.sonidos.cargar('audio/tick.wav')
    
    def actualizar(self):
        if self.pilas.escena_actual().control.arriba:
            self.y += 2
            self.sonido.reproducir()
        elif self.pilas.escena_actual().control.abajo:
            self.y -= 2
            self.sonido.reproducir()
        
        if self.pilas.escena_actual().control.izquierda:
            self.x -= 2
            self.sonido.reproducir()
        elif self.pilas.escena_actual().control.derecha:
            self.x += 2
            self.sonido.reproducir()

        if self.pilas.escena_actual().control.boton:
            self.saltar()
            self.gritar()

mono_con_controles = MonoConControles(pilas)
pilas.avisar(u"Usá el teclado para mover al personaje.")
music.reproducir(repetir=True)
pilas.ejecutar()