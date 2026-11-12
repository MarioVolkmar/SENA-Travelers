from datetime import date


def today() -> date:
    """
    Fecha actual del sistema.

    Todos los servicios la piden aquí (clock.today()) para que los tests
    puedan fijarla y no dependan del día en que se ejecutan.
    """
    return date.today()


def age_on(birth_date: date, on_date: date) -> int:
    """Años cumplidos en una fecha: el 9 de mayo alguien nacido el 10 de mayo aún no cumple."""
    years = on_date.year - birth_date.year
    if (on_date.month, on_date.day) < (birth_date.month, birth_date.day):
        years -= 1
    return years
