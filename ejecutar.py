"""Pasa cada texto del dataset por los 4 métodos y guarda cada resultado.

Uso:
    python ejecutar.py --limit 10          # prueba pequeña (céntimos)
    python ejecutar.py --repeticiones 2    # prueba completa
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from comprobar import comprobar_molde, puntuar
from informe import imprimir_informe
from metodos import METODOS


def cargar_dataset(ruta, limite):
    with open(ruta, encoding="utf-8") as f:
        casos = [json.loads(linea) for linea in f if linea.strip()]
    return casos[:limite] if limite else casos


def ejecutar_caso(nombre, metodo, caso):
    """Un texto con un método. Devuelve una fila con todo lo que queremos medir."""
    inicio = time.perf_counter()
    try:
        r = metodo(caso["texto"])
        error = None
    except Exception as e:  # fallo de la API: se anota y se sigue con el siguiente
        r = {"salida": None, "bruto": "", "tin": 0, "tout": 0, "reintentos": 0}
        error = str(e)
    ms = round((time.perf_counter() - inicio) * 1000)

    exacto, campos = puntuar(r["salida"], caso["esperado"])
    return {
        "metodo": nombre,
        "id": caso["id"],
        "tipo": caso["tipo"],
        "json_ok": r["salida"] is not None,                  # ¿se pudo leer como JSON?
        "molde_ok": comprobar_molde(r["salida"]) is None,    # ¿cumple el molde?
        "exacto": exacto,                                    # ¿los 4 campos coinciden con lo esperado?
        "campos": campos,                                    # fracción de campos correctos
        "tin": r["tin"],
        "tout": r["tout"],
        "reintentos": r["reintentos"],
        "ms": ms,
        "error": error,
        "bruto": r["bruto"],
        "primer_error": r.get("primer_error"),   # solo structured_validated: por qué se reintentó
        "primer_bruto": r.get("primer_bruto"),   # y qué había contestado la primera vez
    }


def main():
    ap = argparse.ArgumentParser(description="Compara 4 formas de obtener JSON de un LLM.")
    ap.add_argument("--dataset", default="dataset.jsonl")
    ap.add_argument("--limit", type=int, default=0, help="usar solo los N primeros casos")
    ap.add_argument("--repeticiones", type=int, default=1)
    args = ap.parse_args()

    casos = cargar_dataset(args.dataset, args.limit)
    Path("results").mkdir(exist_ok=True)
    ruta = Path("results") / f"results_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
    print(f"{len(casos)} casos x {len(METODOS)} métodos x {args.repeticiones} repeticiones "
          f"= {len(casos) * len(METODOS) * args.repeticiones} llamadas (más reintentos)")

    filas = []
    with open(ruta, "w", encoding="utf-8") as f:
        for repeticion in range(1, args.repeticiones + 1):
            for caso in casos:
                for nombre, metodo in METODOS.items():
                    fila = ejecutar_caso(nombre, metodo, caso)
                    fila["repeticion"] = repeticion
                    filas.append(fila)
                    f.write(json.dumps(fila, ensure_ascii=False) + "\n")
                    f.flush()  # se guarda al momento: si se corta, no pierdes lo ya pagado
            print(f"Repetición {repeticion}/{args.repeticiones} completada")

    print(f"Resultados guardados en {ruta}")
    imprimir_informe(filas)


if __name__ == "__main__":
    main()
