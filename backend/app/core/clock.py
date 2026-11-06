from datetime import date


def today() -> date:
    """
    Fecha actual del sistema.

    Todos los servicios la piden aquí (clock.today()) para que los tests
    puedan fijarla y no dependan del día en que se ejecutan.
    """
    return date.today()
