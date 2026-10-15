"""Los 4 métodos para obtener JSON de un LLM.

Todos reciben el texto del usuario y devuelven un diccionario con:
  salida      el JSON ya convertido en dict (None si no se pudo)
  bruto       lo que contestó el modelo, tal cual
  tin, tout   tokens de entrada y de salida
  reintentos  cuántas veces hubo que repetir la pregunta
"""
import json

import anthropic

from comprobar import comprobar_molde, comprobar_sentido, extraer_json, leer_json
from config import MAX_TOKENS, MODELO, MOLDE, PROMPT, TEMPERATURA

MAX_REINTENTOS = 2
cliente = anthropic.Anthropic()

HERRAMIENTA = {
    "name": "registrar_peticion",
    "description": "Registra la petición del usuario en el formato que necesita el backend de citas.",
    "input_schema": MOLDE,
}

FORMATO = {"output_config": {"format": {"type": "json_schema", "schema": MOLDE}}}

# ---------------------------------------------------------------- ayudas
def llamar(mensajes, **extra):
    """Una llamada a la API. Devuelve (respuesta, tokens_entrada, tokens_salida)."""
    parametros = dict(model=MODELO, max_tokens=MAX_TOKENS, system=PROMPT, messages=mensajes, **extra)
    if TEMPERATURA is not None:
        parametros["temperature"] = TEMPERATURA
    respuesta = cliente.messages.create(**parametros)
    return respuesta, respuesta.usage.input_tokens, respuesta.usage.output_tokens


def texto_de(respuesta):
    """Une los bloques de texto de la respuesta."""
    return "".join(b.text for b in respuesta.content if b.type == "text")


def resultado(salida, bruto, tin, tout, reintentos=0):
    return {"salida": salida, "bruto": bruto, "tin": tin, "tout": tout, "reintentos": reintentos}


# ---------------------------------------------------------------- los 4 métodos
def prompt_only(texto):
    """1. Pedir el JSON en el prompt y parsear lo que conteste, tal cual."""
    respuesta, tin, tout = llamar([{"role": "user", "content": texto}])
    bruto = texto_de(respuesta)
    return resultado(leer_json(bruto), bruto, tin, tout)


def prompt_only_limpio(texto):
    """1b. Igual que prompt_only, pero quitando el bloque ```json y el texto extra antes de parsear."""
    respuesta, tin, tout = llamar([{"role": "user", "content": texto}])
    bruto = texto_de(respuesta)
    return resultado(extraer_json(bruto), bruto, tin, tout)


def tool_use(texto):
    """2. Darle una herramienta (un formulario) y obligarle a rellenarla."""
    respuesta, tin, tout = llamar(
        [{"role": "user", "content": texto}],
        tools=[HERRAMIENTA],
        tool_choice={"type": "tool", "name": HERRAMIENTA["name"]},
    )
    uso = next((b for b in respuesta.content if b.type == "tool_use"), None)
    if uso is None:
        return resultado(None, texto_de(respuesta), tin, tout)
    return resultado(uso.input, json.dumps(uso.input, ensure_ascii=False), tin, tout)


def structured(texto):
    """3. Pasarle el molde al API, que obliga al modelo a respetarlo."""
    respuesta, tin, tout = llamar([{"role": "user", "content": texto}], extra_body=FORMATO)
    bruto = texto_de(respuesta)
    return resultado(leer_json(bruto), bruto, tin, tout)


def structured_validated(texto):
    """4. Como el 3, pero revisamos la respuesta y, si falla, se la devolvemos al modelo."""
    mensajes = [{"role": "user", "content": texto}]
    tin_total = tout_total = 0
    primer_error = primer_bruto = None  # qué falló en el primer intento (si falló)

    for intento in range(MAX_REINTENTOS + 1):
        respuesta, tin, tout = llamar(mensajes, extra_body=FORMATO)
        tin_total += tin
        tout_total += tout
        bruto = texto_de(respuesta)
        salida = leer_json(bruto)

        error = comprobar_molde(salida) or comprobar_sentido(salida)
        if error is None or intento == MAX_REINTENTOS:
            break
        if primer_error is None:
            primer_error, primer_bruto = error, bruto

        # Falló: añadimos su respuesta y el motivo del error, y preguntamos otra vez.
        mensajes += [
            {"role": "assistant", "content": bruto.strip() or "{}"},
            {"role": "user", "content": f"Tu respuesta no es válida ({error}). Devuelve solo el JSON corregido."},
        ]

    r = resultado(salida, bruto, tin_total, tout_total, reintentos=intento)
    r["primer_error"], r["primer_bruto"] = primer_error, primer_bruto
    return r


METODOS = {
    "prompt_only": prompt_only,
    "prompt_only_limpio": prompt_only_limpio,
    "tool_use": tool_use,
    "structured": structured,
    "structured_validated": structured_validated,
}
