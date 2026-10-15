"""Resume un archivo de resultados. No llama a la API, así que no gasta nada.

Uso:
    python informe.py results/results_XXXX.jsonl
"""
import json
import sys


def media(filas, clave):
    return sum(f[clave] for f in filas) / len(filas)


def pct(valor):
    return f"{valor * 100:.1f}%"


def imprimir_tabla(cabecera, filas):
    """Imprime una tabla con las columnas alineadas."""
    anchos = [max(len(str(x)) for x in columna) for columna in zip(cabecera, *filas)]
    for linea in [cabecera] + filas:
        print("  ".join(str(celda).ljust(ancho) for celda, ancho in zip(linea, anchos)))


def imprimir_informe(filas):
    metodos = list(dict.fromkeys(f["metodo"] for f in filas))  # en el orden en que se ejecutaron
    tipos = sorted({f["tipo"] for f in filas})

    print("\n== Resumen por método ==")
    tabla = []
    for m in metodos:
        fm = [f for f in filas if f["metodo"] == m]
        tabla.append([
            m, len(fm),
            pct(media(fm, "json_ok")), pct(media(fm, "molde_ok")),
            pct(media(fm, "exacto")), pct(media(fm, "campos")),
            round(media(fm, "tin")), round(media(fm, "tout")), round(media(fm, "ms")),
            sum(f["reintentos"] for f in fm),
        ])
    imprimir_tabla(
        ["método", "n", "json", "molde", "exacto", "campos", "tok in", "tok out", "ms", "reintentos"],
        tabla,
    )

    print("\n== Acierto exacto por tipo de texto ==")
    tabla = []
    for m in metodos:
        fila = [m]
        for t in tipos:
            ft = [f for f in filas if f["metodo"] == m and f["tipo"] == t]
            fila.append(pct(media(ft, "exacto")) if ft else "-")
        tabla.append(fila)
    imprimir_tabla(["método"] + tipos, tabla)

    fallos = sum(1 for f in filas if not f["exacto"])
    errores_api = sum(1 for f in filas if f["error"])
    print(f"\nFallos: {fallos} de {len(filas)}. Errores de la API: {errores_api}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python informe.py results/results_XXXX.jsonl")
    with open(sys.argv[1], encoding="utf-8") as archivo:
        imprimir_informe([json.loads(linea) for linea in archivo if linea.strip()])
