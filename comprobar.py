"""Comprobaciones: ¿es JSON?, ¿cumple el molde?, ¿tiene sentido?, ¿coincide con lo esperado?"""
import json
import unicodedata

from config import ACCIONES, CAMPOS, FRANJAS


def leer_json(texto):
    """Convierte texto en JSON. Devuelve None si no es JSON válido."""
    try:
        return json.loads(texto)
    except ValueError:
        return None


def extraer_json(texto):
    """Rescata lo que haya entre la primera { y la última }: quita bloques ```json y texto extra."""
    inicio, fin = texto.find("{"), texto.rfind("}")
    return leer_json(texto[inicio:fin + 1]) if 0 <= inicio < fin else None


def comprobar_molde(d):
    """Mira la FORMA del JSON. Devuelve None si está bien, o un texto explicando el error."""
    if not isinstance(d, dict):
        return "no es un objeto"
    if set(d) != set(CAMPOS):
        return f"campos incorrectos: {sorted(d)}"
    if d["accion"] not in ACCIONES:
        return f"accion no válida: {d['accion']!r}"
    if d["franja"] not in FRANJAS:
        return f"franja no válida: {d['franja']!r}"
    if not isinstance(d["cita_actual"], str) or not isinstance(d["nueva_fecha"], str):
        return "cita_actual y nueva_fecha deben ser texto"
    return None


def comprobar_sentido(d):
    """Reglas de SENTIDO del backend (son ejemplos: adáptalas). No usa la respuesta esperada."""
    accion = d["accion"]
    if accion == "reprogramar_cita" and not (d["cita_actual"] and d["nueva_fecha"]):
        return "reprogramar_cita necesita cita_actual y nueva_fecha"
    if accion == "cancelar_cita" and not d["cita_actual"]:
        return "cancelar_cita necesita cita_actual"
    if accion == "pedir_aclaracion" and (d["cita_actual"] or d["nueva_fecha"] or d["franja"] != "ninguna"):
        return "pedir_aclaracion debe dejar el resto vacío"
    return None


def sin_tildes(valor):
    """Minúsculas y sin tildes, para que 'Miércoles' y 'miercoles' cuenten igual."""
    texto = unicodedata.normalize("NFD", str(valor).strip().lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def puntuar(salida, esperado):
    """Compara con la respuesta esperada. Devuelve (todo_correcto, fracción_de_campos_correctos)."""
    if not isinstance(salida, dict):
        return False, 0.0
    aciertos = [sin_tildes(salida.get(c, "")) == sin_tildes(esperado[c]) for c in CAMPOS]
    return all(aciertos), sum(aciertos) / len(aciertos)
