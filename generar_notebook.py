#!/usr/bin/env python3
"""Construye y ejecuta el cuaderno de repaso del modelo C-V3."""

import base64
import binascii
import itertools
from pathlib import Path
import re
import struct
from urllib.parse import quote
import zlib

import nbformat
from nbclient import NotebookClient


WORK_DIR = Path(__file__).resolve().parent
NOTEBOOK_PATH = WORK_DIR / "solucion-examen-c-v3.ipynb"
FIGURES_DIR = WORK_DIR / "figures"
BANNED_PATTERN = re.compile(
    r"foto|fotograf|escane|ocr|omr|aruco|automátic|automatic|corrector",
    re.IGNORECASE,
)

A1_CODE = '''prestados = ["Momo", "Matilda"]
prestados.append("Dune")
print(len(prestados))'''

A2_CODE = '''estante = "NC.N"
print(estante[0])'''

A3_CODE = '''def multa_a(dias):
    return dias * 2

def multa_b(dias):
    print(dias * 2)

a = multa_a(5)
b = multa_b(5)'''

A4_CODE = '''sellos = 0
for libro in ["novela", "revista", "novela"]:
    if libro == "novela":
        sellos = sellos + 1
print(sellos)'''

B1_CODE = '''def revisar(retrasos):
    multados = 0
    revisados = 0
    for d in retrasos:
        revisados = revisados + 1
        if d >= 3:
            multados = multados + 1
    print("Multados:", multados)
    print("Revisados:", revisados)

revisar([4, 1, 5, 0, 6])'''

B2_CODE = '''estante = "N.C."
nuevo = ""
vacios = 0
for c in estante:
    if c == ".":
        nuevo = nuevo + "N"
        vacios = vacios + 1
    else:
        nuevo = nuevo + c

print(nuevo)
print(vacios)'''

B3_CODE = '''def caben(grosores, espacio):
    libros = 0
    for g in grosores:
        if g > espacio:
            return libros
        espacio = espacio - g
        libros = libros + 1
    return libros

print(caben([2, 3], 4))
print(caben([1, 1], 5))
print(caben([7], 5))'''

B4_CODE = '''def sellar(lote):
    sellados = []
    for libro in lote:
        if libro != "revista":
            sellados.append(libro)
    print(len(lote))
    return sellados

r = sellar(["novela", "revista", "comic"])
print(r)
print(len(r))'''

C1_SOLUTION = '''def contar_novelas(estante):
    novelas = 0                 # inicializar
    for c in estante:           # recorrer
        if c == "N":
            novelas = novelas + 1   # actualizar
    return novelas'''

C2_SOLUTION = '''def posicion_final(ruta):
    x = 0                       # inicializar
    for paso in ruta:           # recorrer
        if paso == "E":
            x = x + 1           # actualizar
        elif paso == "O":
            x = x - 1
    return x'''

C3_SOLUTION = '''def huecos(estante):
    posiciones = []             # inicializar
    for i in range(len(estante)):   # recorrer
        if estante[i] == ".":
            posiciones.append(i)    # actualizar
    return posiciones'''

EXPECTED_OUTPUTS = {
    "A1": "3",
    "A2": "N",
    "A3": "10",
    "A4": "2",
    "B1": "Multados: 3\nRevisados: 5",
    "B2": "NNCN\n2",
    "B3": "1\n2\n0",
    "B4": "3\n['novela', 'comic']\n2",
}


TOOLBOX_SOURCE = r'''#@title Caja de herramientas visual
import doctest
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from IPython.display import HTML, display

FONDO_PIZARRA = "#164638"
TIZA = "#f3f0df"
TIZA_AMARILLA = "#ffe36e"
TIZA_AZUL = "#a9d7ef"

def dibujar_pizarra(titulo, lineas, ancho=10, alto=3.3, guardar=None):
    """Dibuja una idea con texto y flechas sobre fondo de pizarra."""
    fig, ax = plt.subplots(figsize=(ancho, alto), dpi=100)
    fig.patch.set_facecolor(FONDO_PIZARRA)
    ax.set_facecolor(FONDO_PIZARRA)
    ax.axis("off")
    ax.text(0.045, 0.91, titulo, color=TIZA_AMARILLA, fontsize=17,
            fontweight="bold", family="DejaVu Sans Mono", va="top")
    cantidad = max(1, len(lineas))
    paso = 0.77 / cantidad
    tamano = 14 if cantidad <= 4 else 12
    for numero, linea in enumerate(lineas):
        if isinstance(linea, tuple):
            texto, color = linea
        else:
            texto, color = linea, TIZA
        ax.text(0.055, 0.78 - numero * paso, texto, color=color,
                fontsize=tamano, family="DejaVu Sans Mono", va="top",
                wrap=True)
    fig.tight_layout(pad=0.5)
    if guardar:
        fig.savefig(guardar, dpi=100, facecolor=FONDO_PIZARRA,
                    bbox_inches="tight")
    display(fig)
    plt.close(fig)

def dibujar_estante(estante, marcar=(), titulo=""):
    """Dibuja las casillas de un estante con los índices debajo."""
    fig, ax = plt.subplots(figsize=(max(5, 1.15 * len(estante)), 2.2), dpi=100)
    fig.patch.set_facecolor(FONDO_PIZARRA)
    ax.set_facecolor(FONDO_PIZARRA)
    ax.text(0.05, 0.94, titulo, transform=ax.transAxes, color=TIZA_AMARILLA,
            fontsize=15, fontweight="bold", family="DejaVu Sans Mono", va="top")
    for i, letra in enumerate(estante):
        resaltada = i in marcar
        ax.add_patch(Rectangle((i, 0), 1, 1,
                               facecolor="#205b49",
                               edgecolor=TIZA_AMARILLA if resaltada else TIZA,
                               linewidth=2.5 if resaltada else 1.5))
        ax.text(i + 0.5, 0.56, letra, ha="center", va="center",
                fontsize=20, color=TIZA_AMARILLA if resaltada else TIZA,
                family="DejaVu Sans Mono", fontweight="bold")
        ax.text(i + 0.5, -0.2, str(i), ha="center", va="center",
                fontsize=12, color=TIZA)
    ax.set_xlim(-0.15, max(1, len(estante)) + 0.15)
    ax.set_ylim(-0.55, 1.05)
    ax.axis("off")
    display(fig)
    plt.close(fig)

def dibujar_estantes_doble(antes, despues, titulo):
    """Compara dos estantes en la misma pizarra."""
    fig, ax = plt.subplots(figsize=(10, 3.1), dpi=100)
    fig.patch.set_facecolor(FONDO_PIZARRA)
    ax.set_facecolor(FONDO_PIZARRA)
    ax.axis("off")
    ax.text(0.03, 0.94, titulo, transform=ax.transAxes, color=TIZA_AMARILLA,
            fontsize=16, fontweight="bold", family="DejaVu Sans Mono", va="top")
    ancho = max(len(antes), len(despues))
    for fila, (etiqueta, estante) in enumerate((("antes", antes), ("después", despues))):
        y = 0.60 - fila * 0.40
        ax.text(0.04, y + 0.10, etiqueta, transform=ax.transAxes,
                color=TIZA_AZUL, fontsize=13, family="DejaVu Sans Mono")
        for i, letra in enumerate(estante):
            x = 0.21 + 0.73 * i / max(1, ancho)
            w = 0.68 / max(1, ancho)
            ax.add_patch(Rectangle((x, y - 0.05), w, 0.23,
                                   transform=ax.transAxes,
                                   facecolor="#205b49",
                                   edgecolor=TIZA, linewidth=1.2))
            ax.text(x + w / 2, y + 0.065, letra, transform=ax.transAxes,
                    ha="center", va="center", fontsize=15, color=TIZA_AMARILLA,
                    family="DejaVu Sans Mono", fontweight="bold")
    display(fig)
    plt.close(fig)

def tabla_html(filas, columnas):
    """Construye una tabla estática para seguir una vuelta cada vez."""
    estilo = "border:1px solid #b8cbbf;padding:6px 14px;text-align:center;font-size:16px"
    cabecera = "".join(
        f'<th style="{estilo};background:#205b49;color:#fff">{c}</th>'
        for c in columnas
    )
    filas_html = "".join(
        "<tr>" + "".join(
            f'<td style="{estilo};color:#18382e">{fila[c]}</td>'
            for c in columnas
        ) + "</tr>"
        for fila in filas
    )
    return HTML(
        '<table style="border-collapse:collapse">'
        f"<tr>{cabecera}</tr>{filas_html}</table>"
    )

def traza_pasos(filas, columnas, pausa=0):
    """Presenta los datos de cada vuelta en orden."""
    display(tabla_html(filas, columnas))

def dibujar_tabla_pizarra(titulo, columnas, filas, guardar=None):
    """Dibuja una tabla de seguimiento legible en la pizarra."""
    fig, ax = plt.subplots(figsize=(10, max(2.8, 0.48 * (len(filas) + 2))), dpi=100)
    fig.patch.set_facecolor(FONDO_PIZARRA)
    ax.set_facecolor(FONDO_PIZARRA)
    ax.axis("off")
    ax.text(0.5, 0.96, titulo, transform=ax.transAxes, ha="center", va="top",
            color=TIZA_AMARILLA, fontsize=15, fontweight="bold",
            family="DejaVu Sans Mono")
    izquierda, derecha = 0.05, 0.95
    arriba, abajo = 0.82, 0.08
    ancho = (derecha - izquierda) / len(columnas)
    alto = (arriba - abajo) / (len(filas) + 1)
    for r in range(len(filas) + 2):
        y = arriba - r * alto
        ax.plot([izquierda, derecha], [y, y], transform=ax.transAxes,
                color=TIZA, linewidth=1)
    for c in range(len(columnas) + 1):
        x = izquierda + c * ancho
        ax.plot([x, x], [abajo, arriba], transform=ax.transAxes,
                color=TIZA, linewidth=1)
    tabla = [columnas] + filas
    for r, fila in enumerate(tabla):
        for c, valor in enumerate(fila):
            x = izquierda + (c + 0.5) * ancho
            y = arriba - (r + 0.5) * alto
            ax.text(x, y, str(valor), transform=ax.transAxes, ha="center",
                    va="center", color=TIZA_AMARILLA if r == 0 else TIZA,
                    fontsize=12, family="DejaVu Sans Mono")
    if guardar:
        fig.savefig(guardar, dpi=100, facecolor=FONDO_PIZARRA,
                    bbox_inches="tight")
    display(fig)
    plt.close(fig)

def dibujar_pasillo(ruta, titulo):
    """Dibuja el recorrido del carro desde el mostrador, posición cero."""
    fig, ax = plt.subplots(figsize=(9, 2.7), dpi=100)
    fig.patch.set_facecolor(FONDO_PIZARRA)
    ax.set_facecolor(FONDO_PIZARRA)
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-1.05, 1.7)
    ax.axis("off")
    ax.text(0.5, 0.98, titulo, transform=ax.transAxes, ha="center", va="top",
            color=TIZA_AMARILLA, fontsize=15, fontweight="bold",
            family="DejaVu Sans Mono")
    ax.plot([-3, 3], [0, 0], color=TIZA, linewidth=2)
    for posicion in range(-3, 4):
        ax.add_patch(Rectangle((posicion - 0.34, -0.28), 0.68, 0.56,
                               facecolor="#205b49",
                               edgecolor=TIZA_AZUL if posicion == 0 else TIZA,
                               linewidth=2 if posicion == 0 else 1))
        ax.text(posicion, -0.58, str(posicion), ha="center", va="top",
                color=TIZA, fontsize=11, family="DejaVu Sans Mono")
    ax.text(0, 0.36, "mostrador", ha="center", color=TIZA_AZUL,
            fontsize=10, family="DejaVu Sans Mono")
    x = 0
    for paso, letra in enumerate(ruta, 1):
        nuevo_x = x + (1 if letra == "E" else -1)
        altura = 0.56 + 0.24 * (paso - 1)
        ax.annotate("", xy=(nuevo_x, altura), xytext=(x, altura),
                    arrowprops={"arrowstyle": "-|>", "color": TIZA_AMARILLA,
                                "linewidth": 2})
        ax.text((x + nuevo_x) / 2, altura + 0.10, f"{paso}:{letra}",
                ha="center", color=TIZA, fontsize=10,
                family="DejaVu Sans Mono")
        x = nuevo_x
    ax.plot(x, 0, marker="s", markersize=11, color=TIZA_AMARILLA,
            markeredgecolor=TIZA)
    ax.text(0.5, 0.02, f"fin: x = {x}", transform=ax.transAxes,
            ha="center", color=TIZA_AMARILLA, fontsize=12,
            family="DejaVu Sans Mono")
    display(fig)
    plt.close(fig)

print("Caja lista: pizarra, estantes, pasillo y tablas.")
'''


def code_cell(source, tag=None):
    cell = nbformat.v4.new_code_cell(source)
    if tag:
        cell.metadata["tags"] = [f"answer:{tag}"]
    return cell


def markdown_cell(source):
    return nbformat.v4.new_markdown_cell(source)


def pizarra_source(lines, title, width=10, height=3.3):
    colors = {
        "TIZA": "TIZA",
        "TIZA_AMARILLA": "TIZA_AMARILLA",
        "TIZA_AZUL": "TIZA_AZUL",
    }
    rendered_lines = []
    for line in lines:
        if isinstance(line, tuple):
            text, color = line
            color_expression = colors.get(color, repr(color))
            rendered_lines.append(f"({text!r}, {color_expression})")
        else:
            rendered_lines.append(repr(line))
    rendered = ",\n    ".join(rendered_lines)
    return (
        "dibujar_pizarra(\n"
        f"    {title!r},\n"
        f"    [{rendered}],\n"
        f"    ancho={width}, alto={height},\n"
        ")"
    )


def tutor_url(source):
    return (
        "https://pythontutor.com/visualize.html#code="
        + quote(source)
        + "&cumulative=false&curInstr=0&heapPrimitives=nevernest&mode=display"
        + "&origin=opt-frontend.js&py=311&rawInputLstJson=%5B%5D"
        + "&textReferences=false"
    )


def add_tutor_link(cells, source):
    url = tutor_url(source)
    cells.append(markdown_cell(f"[Ver paso a paso en PythonTutor]({url})"))


def add_rubric(cells, rows):
    cells.append(markdown_cell(
        "#### Rúbrica\n\n| Criterio | Puntos |\n|---|---:|\n"
        + "\n".join(f"| {criterion} | {points} |" for criterion, points in rows)
    ))


def add_frequent_errors(cells, items):
    cells.append(markdown_cell(
        "#### Errores frecuentes\n\n"
        + "\n".join(f"- {item}" for item in items)
    ))


def add_exercise_header(cells, heading, statement):
    cells.append(markdown_cell(f"## {heading}\n\n### Enunciado exacto\n\n{statement}"))
    cells.append(markdown_cell("### Pizarra"))


def build_notebook():
    cells = [
        markdown_cell(
            '<a href="https://colab.research.google.com/github/'
            'maximofernandezriera/examen-ifc33A/blob/main/'
            'solucion-examen-c-v3.ipynb" target="_parent">'
            '<img src="https://colab.research.google.com/assets/colab-badge.png" '
            'alt="Open In Colab"/></a>'
        ),
        markdown_cell(
            "# Repaso del examen: modelo C-V3 — la biblioteca de Lucía\n\n"
            "Lucía es la bibliotecaria del barrio. Cada día presta y recoge libros, "
            "los coloca en las estanterías y avisa a quien se retrasa al devolverlos. "
            "Para ahorrar tiempo, se ha escrito pequeños programas en Python que le "
            "ayudan con estas tareas. En los strings de una estantería, `N` es una "
            "novela, `C` un cómic y `.` un hueco libre.\n\n"
            "## Cómo se ha corregido\n\n"
            "- El examen suma **30 puntos**: A, 8; B, 11; C, 11.\n"
            "- Los errores de sintaxis no restan puntos.\n"
            "- Se aceptan respuestas equivalentes con otro formato (por ejemplo, "
            "`NNCN` con comillas o «3 multados» en vez de «Multados: 3»).\n"
            "- En C, la idea correcta puntúa aunque el código no funcione del todo.\n"
            "- Si no hay código pero los resultados de los ejemplos son correctos, "
            "se concede 1 punto."
        ),
        markdown_cell(
            "## Caja de herramientas visual\n\n"
            "Ejecutad esta celda una sola vez. Prepara la pizarra, las estanterías, "
            "el pasillo y las tablas que usaremos durante el repaso."
        ),
        code_cell(TOOLBOX_SOURCE),
    ]

    # A1
    a1_statement = (
        "Lucía apunta los libros que presta durante la mañana. ¿Qué imprime este código? "
        "(2 ptos)\n\n"
        + "```python\n" + A1_CODE + "\n```\n\n"
        + "a) 2  b) 3  c) 4  d) Dune"
    )
    add_exercise_header(cells, "A1 · `append` y longitud (2 puntos)", a1_statement)
    cells.append(code_cell(pizarra_source([
        ("ANTES: ['Momo', 'Matilda']  →  len = 2", "TIZA"),
        ("append('Dune')  →  añade al final", "TIZA_AMARILLA"),
        ("DESPUÉS: ['Momo', 'Matilda', 'Dune']  →  len = 3", "TIZA"),
    ], "La lista antes y después", height=2.8)))
    cells.append(code_cell(A1_CODE, "A1"))
    cells.append(markdown_cell(
        "**Paso a paso.** `append` agrega `" + "`Dune`" + "` al final de la lista. "
        "`len` cuenta los elementos después de ese cambio: hay 3. La respuesta es **b) 3**."
    ))
    add_rubric(cells, [("Respuesta b: comprende `append` y `len`.", "2"),
                       ("Una respuesta incorrecta no resta.", "0 de resta")])
    add_frequent_errors(cells, [
        "Contar los elementos antes de ejecutar `append`.",
        "Elegir `Dune`, que es el elemento añadido y no la longitud.",
    ])

    # A2
    a2_statement = (
        "¿Qué imprime este código? (2 ptos)\n\n"
        + "```python\n" + A2_CODE + "\n```\n\n"
        + "a) N  b) C  c) .  d) NC"
    )
    add_exercise_header(cells, "A2 · Índice de un string (2 puntos)", a2_statement)
    cells.append(code_cell(
        'dibujar_estante("NC.N", marcar=[0], titulo="estante[0]: primera casilla")'
    ))
    cells.append(code_cell(A2_CODE, "A2"))
    cells.append(markdown_cell(
        "**Paso a paso.** Los índices empiezan en 0. La posición `0` es la primera "
        "letra de `NC.N`, que es `N`; por eso se imprime `N`. La respuesta es **a)**."
    ))
    add_rubric(cells, [("Respuesta a: identifica el índice 0.", "2"),
                       ("Una respuesta incorrecta no resta.", "0 de resta")])
    add_frequent_errors(cells, [
        "Leer `estante[0]` como la segunda casilla.",
        "Responder con más de una letra: un índice devuelve un solo carácter.",
    ])

    # A3
    a3_statement = (
        "Lucía calcula la multa por retraso de dos maneras distintas (2 euros por día). "
        "¿Cuánto valen a y b después de ejecutar este código? (2 ptos)\n\n"
        + "```python\n" + A3_CODE + "\n```\n\n"
        + "a) `a` vale 10 y `b` vale 10  "
        + "b) `a` vale `None` y `b` vale 10<br>"
        + "c) `a` vale 10 y `b` vale `None`  "
        + "d) los dos valen `None`"
    )
    add_exercise_header(cells, "A3 · `return` frente a `print` (2 puntos)", a3_statement)
    cells.append(code_cell(pizarra_source([
        ("multa_a(5)  →  return 10  →  a = 10", "TIZA_AMARILLA"),
        ("multa_b(5)  →  print(10)  →  pantalla: 10", "TIZA"),
        ("sin return  →  b = None", "TIZA_AMARILLA"),
    ], "El valor que vuelve y lo que se ve", height=2.8)))
    cells.append(code_cell(A3_CODE, "A3"))
    cells.append(markdown_cell(
        "**Paso a paso.** `multa_a` devuelve `5 * 2`, así que `a` vale `10`. "
        "`multa_b` muestra `10` en pantalla, pero no tiene `return`; Python devuelve "
        "`None` cuando una función termina sin devolver un valor. Por eso `b` vale "
        "`None`. La respuesta es **c)**."
    ))
    add_tutor_link(cells, A3_CODE)
    add_rubric(cells, [("Respuesta c: distingue el valor devuelto de lo que se imprime.", "2"),
                       ("Una respuesta incorrecta no resta.", "0 de resta")])
    add_frequent_errors(cells, [
        "Tomar el `10` que aparece en pantalla como el valor asignado a `b`.",
        "Confundir `print` con `return`.",
    ])

    # A4
    a4_statement = (
        "En el club de lectura, cada novela leída da 1 sello en el carné. "
        "¿Qué imprime este código? (2 ptos)\n\n"
        + "```python\n" + A4_CODE + "\n```\n\n"
        + "a) 1  b) 3  c) 0  d) 2"
    )
    add_exercise_header(cells, "A4 · Contador y condición (2 puntos)", a4_statement)
    cells.append(code_cell(
        'dibujar_tabla_pizarra("El contador solo cambia con novela", '
        '["vuelta", "libro", "sellos"], '
        '[["1", "novela", "1"], ["2", "revista", "1"], ["3", "novela", "2"]])'
    ))
    cells.append(code_cell(A4_CODE, "A4"))
    cells.append(markdown_cell(
        "**Paso a paso.** El bucle visita tres libros. La condición se cumple en la "
        "primera y en la tercera vuelta; el contador pasa de 0 a 1 y luego a 2. "
        "La revista no lo cambia. Se imprime `2`: **d)**."
    ))
    add_tutor_link(cells, A4_CODE)
    add_rubric(cells, [("Respuesta d: cuenta solo las novelas.", "2"),
                       ("Una respuesta incorrecta no resta.", "0 de resta")])
    add_frequent_errors(cells, [
        "Sumar en las tres vueltas sin comprobar el `if`.",
        "Contar vueltas en lugar de contar las veces que se cumple la condición.",
    ])

    # B1
    b1_statement = (
        "B1. (3 pts) Lucía revisa los libros devueltos: la lista indica cuántos días "
        "de retraso trae cada uno. Cuenta cuántos libros ha revisado y pone multa a "
        "los que llegan con 3 días o más. Completa la tabla con el valor de las "
        "variables al final de cada vuelta y escribe lo que imprime.\n\n"
        + "```python\n" + B1_CODE + "\n```"
    )
    add_exercise_header(cells, "B1 · Tabla de seguimiento (3 puntos)", b1_statement)
    cells.append(code_cell(pizarra_source([
        ("revisados sube en cada vuelta", "TIZA"),
        ("multados sube si d >= 3", "TIZA_AMARILLA"),
        ("al final: Multados: 3  →  Revisados: 5", "TIZA"),
    ], "Dos contadores, dos reglas", height=2.7)))
    cells.append(code_cell(B1_CODE, "B1"))
    b1_rows = [
        {"Vuelta": "1", "d": "4", "multados": "1", "revisados": "1"},
        {"Vuelta": "2", "d": "1", "multados": "1", "revisados": "2"},
        {"Vuelta": "3", "d": "5", "multados": "2", "revisados": "3"},
        {"Vuelta": "4", "d": "0", "multados": "2", "revisados": "4"},
        {"Vuelta": "5", "d": "6", "multados": "3", "revisados": "5"},
    ]
    cells.append(code_cell(
        "filas_b1 = " + repr(b1_rows) + "\n"
        'traza_pasos(filas_b1, ["Vuelta", "d", "multados", "revisados"])'
    ))
    cells.append(markdown_cell(
        "**Paso a paso.** Primero, `revisados` aumenta una vez en cada vuelta. "
        "Después se comprueba `d >= 3`: las vueltas 1, 3 y 5 suman una multa. "
        "La tabla termina con `multados = 3` y `revisados = 5`; los dos `print` "
        "están después del bucle."
    ))
    add_tutor_link(cells, B1_CODE)
    add_rubric(cells, [
        ("Tabla: 0,4 por cada fila completa.", "2"),
        ("Se acepta crédito parcial por columna si una fila está parcialmente bien.", "—"),
        ("Salida `Multados: 3`.", "0,5"),
        ("Salida `Revisados: 5`.", "0,5"),
    ])
    add_frequent_errors(cells, [
        "Escribir `None` en lugar de las líneas que muestran los `print`.",
        "Omitir el texto `Multados:` o `Revisados:` en las salidas.",
        "Aumentar `multados` también cuando `d` es menor que 3.",
    ])

    # B2
    b2_statement = (
        "B2. (2 pts) Han llegado novelas nuevas y Lucía coloca una en cada hueco libre "
        "de la estantería. Indica exactamente qué imprime cada línea. (1,5 ptos la "
        "primera, 0,5 ptos la segunda)\n\n"
        + "```python\n" + B2_CODE + "\n```"
    )
    add_exercise_header(cells, "B2 · Construir un string (2 puntos)", b2_statement)
    cells.append(code_cell(
        'dibujar_estantes_doble("N.C.", "NNCN", '
        '"Antes y después: cada punto pasa a ser N")'
    ))
    cells.append(code_cell(B2_CODE, "B2"))
    cells.append(markdown_cell(
        "**Paso a paso.** El `for` recorre las letras de `N.C.`. Copia la primera `N`, "
        "cambia `.` por `N`, copia `C` y cambia el último `.` por `N`. El nuevo estante "
        "es `NNCN`; hay 2 huecos sustituidos. Se imprimen esas dos líneas."
    ))
    add_tutor_link(cells, B2_CODE)
    add_rubric(cells, [("Primera línea: `NNCN`.", "1,5"),
                       ("Segunda línea: `2`.", "0,5")])
    add_frequent_errors(cells, [
        "Cambiar letras que no son `.`.",
        "No conservar el resto del estante en el string nuevo.",
    ])

    # B3
    b3_statement = (
        "B3. (4 pts) Esta función calcula cuántos libros caben, en orden, en el espacio "
        "libre de una balda: la lista indica el grosor de cada libro en centímetros y "
        "espacio, los centímetros libres. Escribe exactamente lo que imprime el "
        "programa y responde: ¿cuántas vueltas da el bucle en la primera llamada? "
        "(1 pto cada línea impresa y 1 pto la pregunta)\n\n"
        + "```python\n" + B3_CODE + "\n```"
    )
    add_exercise_header(cells, "B3 · Espacio y `return` temprano (4 puntos)", b3_statement)
    cells.append(code_cell(pizarra_source([
        ("inicio: espacio = 4, libros = 0", "TIZA"),
        ("vuelta 1: g = 2 cabe  →  espacio = 2, libros = 1", "TIZA"),
        ("vuelta 2: g = 3 no cabe en 2", "TIZA_AMARILLA"),
        ("return libros dentro del for  →  devuelve 1", "TIZA_AMARILLA"),
    ], "La primera llamada, vuelta a vuelta", height=3.2)))
    cells.append(code_cell(B3_CODE, "B3"))
    b3_rows = [
        {"Vuelta": "1", "g": "2", "espacio antes": "4", "¿cabe?": "sí", "libros": "1"},
        {"Vuelta": "2", "g": "3", "espacio antes": "2", "¿cabe?": "no → return", "libros": "1"},
    ]
    cells.append(code_cell(
        "filas_b3 = " + repr(b3_rows) + "\n"
        'traza_pasos(filas_b3, ["Vuelta", "g", "espacio antes", "¿cabe?", "libros"])'
    ))
    cells.append(markdown_cell(
        "**Paso a paso.** En la primera llamada, el libro de grosor 2 cabe en 4: "
        "quedan 2 cm y `libros` pasa a 1. El bucle llega a la segunda vuelta con "
        "`g = 3`; no cabe en los 2 cm. El `return libros` de dentro termina la función "
        "y devuelve 1. Por eso son **2 vueltas**. En la segunda llamada caben los dos "
        "libros y devuelve 2; en la tercera el libro no cabe desde el principio y "
        "devuelve 0."
    ))
    add_tutor_link(cells, B3_CODE)
    add_rubric(cells, [("Primera línea impresa: `1`.", "1"),
                       ("Segunda línea impresa: `2`.", "1"),
                       ("Tercera línea impresa: `0`.", "1"),
                       ("Primera llamada: 2 vueltas.", "1")])
    add_frequent_errors(cells, [
        "Contar el `return` como si el bucle continuara con más elementos.",
        "No descontar el grosor que sí cabe antes de comprobar la siguiente vuelta.",
    ])

    # B4
    b4_statement = (
        "B4. (2 pts) Lucía aparta todo lo que llega menos las revistas para ponerle "
        "el sello de la biblioteca. Escribe exactamente lo que aparece en pantalla "
        "al ejecutar este programa. (1 pto la lista, 0,5 ptos cada una de las otras "
        "dos líneas)\n\n"
        + "```python\n" + B4_CODE + "\n```"
    )
    add_exercise_header(cells, "B4 · Impresión dentro y fuera (2 puntos)", b4_statement)
    cells.append(code_cell(pizarra_source([
        ("DENTRO de sellar: print(len(lote))  →  3", "TIZA_AMARILLA"),
        ("return sellados  →  ['novela', 'comic']", "TIZA"),
        ("FUERA: print(len(r))  →  2", "TIZA"),
    ], "Tres líneas, dos lugares de impresión", height=2.9)))
    cells.append(code_cell(B4_CODE, "B4"))
    cells.append(markdown_cell(
        "**Paso a paso.** Al llamar a `sellar`, el `print` que está dentro muestra "
        "la longitud de `lote`, que es 3. La función devuelve la lista sin `revista`. "
        "Después, fuera de la función, el programa muestra esa lista y su longitud, 2."
    ))
    add_tutor_link(cells, B4_CODE)
    add_rubric(cells, [("Lista `['novela', 'comic']`.", "1"),
                       ("Primera línea `3`.", "0,5"),
                       ("Última línea `2`.", "0,5")])
    add_frequent_errors(cells, [
        "Olvidar el `3` que imprime la función por dentro.",
        "Confundir la lista devuelta con el lote original.",
    ])

    # C1
    c1_statement = (
        "C1. (3 pts) Inventario. Para el inventario, Lucía quiere saber cuántas novelas "
        "`N` hay en una estantería. Escribe `contar_novelas(estante)`, que devuelve "
        "cuántas novelas hay; los cómics y los huecos no cuentan.\n\n"
        "```text\n"
        'contar_novelas("NN.C")    ->  2\n'
        'contar_novelas("CCN.N")   ->  2\n'
        'contar_novelas("")        ->  0\n'
        "```"
    )
    add_exercise_header(cells, "C1 · Contar novelas (3 puntos)", c1_statement)
    cells.append(code_cell(pizarra_source([
        ("novelas = 0                 # inicializar", "TIZA_AMARILLA"),
        ("for c in estante:           # recorrer", "TIZA"),
        ('    if c == "N":', "TIZA"),
        ("        novelas = novelas + 1   # actualizar", "TIZA"),
        ("return novelas               # devolver al final", "TIZA_AMARILLA"),
    ], "Inicializar → recorrer → actualizar → devolver", height=3.6)))
    cells.append(code_cell(
        C1_SOLUTION + '\n\n'
        'print(contar_novelas("NN.C"))\n'
        'print(contar_novelas("CCN.N"))\n'
        'print(contar_novelas(""))'
    ))
    cells.append(code_cell(
        'contar_novelas.__doc__ = """\n'
        '>>> contar_novelas("NN.C")\n'
        '2\n'
        '>>> contar_novelas("CCN.N")\n'
        '2\n'
        '>>> contar_novelas("")\n'
        '0\n'
        '"""\n'
        'doctest.run_docstring_examples(contar_novelas, globals(), verbose=True)\n'
        'runner = doctest.DocTestRunner()\n'
        'for ejemplo in doctest.DocTestFinder().find(contar_novelas, "contar_novelas"):\n'
        '    runner.run(ejemplo)\n'
        'resultado = runner.summarize()\n'
        'assert resultado.failed == 0\n'
        'print("Ejemplos verificados: contar_novelas")'
    ))
    cells.append(markdown_cell(
        "**Paso a paso.** El contador nace en 0 antes del bucle. El `for` recorre "
        "cada carácter; solo cuando `c` es `N` se suma 1. El `return` está al final, "
        "fuera del bucle, para devolver el total después de revisar toda la estantería."
    ))
    add_tutor_link(cells, C1_SOLUTION + '\nprint(contar_novelas("NN.C"))')
    add_rubric(cells, [
        ("Inicializa el contador a 0 fuera del bucle.", "1"),
        ("Recorre la estantería con una condición dentro del bucle.", "1"),
        ("Suma dentro del bucle y devuelve el total al final.", "1"),
        ("Si usa `print` en lugar de `return`.", "-1"),
    ])
    add_frequent_errors(cells, [
        "Poner `return` dentro del bucle: la función acaba en la primera letra.",
        "Usar `print` en lugar de `return` cuando el enunciado pide devolver.",
    ])

    # C2
    c2_statement = (
        "C2. (4 pts) El carro de devoluciones. Lucía empuja el carro con los libros "
        "devueltos por el pasillo principal de la biblioteca para dejarlos en su sitio. "
        "Las estanterías del pasillo están numeradas en fila: el mostrador es la "
        "posición `0`, las de la derecha son `1`, `2`, `3`... y las de la izquierda "
        "`-1`, `-2`, `-3`... Lucía siempre sale del mostrador.\n\n"
        "La ruta es un string en el que cada letra mueve el carro una posición:\n\n"
        "| Letra | Dirección | Qué cambia |\n|---|---|---|\n"
        "| E | este (derecha) | x aumenta 1 |\n"
        "| O | oeste (izquierda) | x disminuye 1 |\n\n"
        "Por ejemplo, con la ruta `EEO` el carro hace tres movimientos:\n\n"
        "| Paso | Letra | x |\n|---|---|---:|\n"
        "| inicio |  | 0 |\n| 1 | E | 1 |\n| 2 | E | 2 |\n| 3 | O | 1 |\n\n"
        "Escribe `posicion_final(ruta)`, que devuelve la posición `x` donde acaba el "
        "carro. Si la ruta está vacía, el carro no se mueve.\n\n"
        "```text\n"
        'posicion_final("EEO")     ->  1\n'
        'posicion_final("OO")      ->  -2\n'
        'posicion_final("EOEO")    ->  0\n'
        "```"
    )
    add_exercise_header(cells, "C2 · Recorrer el pasillo (4 puntos)", c2_statement)
    cells.append(code_cell('dibujar_pasillo("EEO", "Ruta EEO: este suma, oeste resta")'))
    cells.append(code_cell(
        C2_SOLUTION + '\n\n'
        'print(posicion_final("EEO"))\n'
        'print(posicion_final("OO"))\n'
        'print(posicion_final("EOEO"))'
    ))
    cells.append(code_cell(
        'posicion_final.__doc__ = """\n'
        '>>> posicion_final("EEO")\n'
        '1\n'
        '>>> posicion_final("OO")\n'
        '-2\n'
        '>>> posicion_final("EOEO")\n'
        '0\n'
        '"""\n'
        'doctest.run_docstring_examples(posicion_final, globals(), verbose=True)\n'
        'runner = doctest.DocTestRunner()\n'
        'for ejemplo in doctest.DocTestFinder().find(posicion_final, "posicion_final"):\n'
        '    runner.run(ejemplo)\n'
        'resultado = runner.summarize()\n'
        'assert resultado.failed == 0\n'
        'print("Ejemplos verificados: posicion_final")'
    ))
    cells.append(markdown_cell(
        "**Paso a paso.** La posición `x` empieza en 0. Cada `E` suma 1 y cada `O` "
        "resta 1. El bucle procesa la ruta letra a letra y `return x` devuelve la "
        "posición final. Si la ruta está vacía, no hay vueltas y se devuelve 0."
    ))
    add_tutor_link(cells, C2_SOLUTION + '\nprint(posicion_final("EEO"))')
    add_rubric(cells, [
        ("Inicializa `x` a 0 fuera del bucle.", "1"),
        ("Recorre la ruta con una condición sobre la letra.", "1"),
        ("Actualiza `x` dentro del bucle.", "1"),
        ("Devuelve `x` al final.", "1"),
    ])
    add_frequent_errors(cells, [
        "Poner `return` dentro del bucle: la ruta se detendría tras la primera letra.",
        "Escribir la función sin un bucle `for`.",
        "Usar la misma variable para la letra de la ruta y para la posición.",
        "Usar `print` en lugar de `return`.",
    ])

    # C3
    c3_statement = (
        "C3. (4 pts) Huecos libres. Escribe `huecos(estante)`, que devuelve una lista "
        "con las posiciones de los huecos libres `.` de la estantería, de izquierda a "
        "derecha. La primera posición es la 0.\n\n"
        "Pista: recorre las posiciones con `for i in range(len(estante)):` y mira la "
        "letra `estante[i]`.\n\n"
        "```text\n"
        'huecos("N..C.")   ->  [1, 2, 4]\n'
        'huecos("NNC")     ->  []\n'
        "```"
    )
    add_exercise_header(cells, "C3 · Devolver posiciones de huecos (4 puntos)", c3_statement)
    cells.append(code_cell(pizarra_source([
        ("posiciones = []                 # inicializar", "TIZA_AMARILLA"),
        ("for i in range(len(estante)):   # recorrer índices", "TIZA"),
        ('    if estante[i] == ".":', "TIZA"),
        ("        posiciones.append(i)    # guardar posición", "TIZA"),
        ("return posiciones               # devolver al final", "TIZA_AMARILLA"),
    ], "Mirar la letra, guardar el índice", height=3.6)))
    cells.append(code_cell(
        C3_SOLUTION + '\n\n'
        'print(huecos("N..C."))\n'
        'print(huecos("NNC"))'
    ))
    cells.append(code_cell(
        'huecos.__doc__ = """\n'
        '>>> huecos("N..C.")\n'
        '[1, 2, 4]\n'
        '>>> huecos("NNC")\n'
        '[]\n'
        '"""\n'
        'doctest.run_docstring_examples(huecos, globals(), verbose=True)\n'
        'runner = doctest.DocTestRunner()\n'
        'for ejemplo in doctest.DocTestFinder().find(huecos, "huecos"):\n'
        '    runner.run(ejemplo)\n'
        'resultado = runner.summarize()\n'
        'assert resultado.failed == 0\n'
        'print("Ejemplos verificados: huecos")'
    ))
    cells.append(markdown_cell(
        "**Paso a paso.** `range(len(estante))` produce las posiciones 0, 1, 2... "
        "En cada posición comprobamos el carácter con `estante[i]`. Si es `.`, "
        "añadimos `i` a la lista. Al terminar el recorrido devolvemos la lista de "
        "posiciones, no una lista de letras."
    ))
    add_tutor_link(cells, C3_SOLUTION + '\nprint(huecos("N..C."))')
    add_rubric(cells, [
        ("Inicializa la lista vacía fuera del bucle.", "1"),
        ("Recorre por posiciones (`range`/`len` o `enumerate`).", "1"),
        ('La condición compara `estante[i]` con `"."`.', "1"),
        ("Añade la posición y devuelve la lista.", "1"),
    ])
    add_frequent_errors(cells, [
        "Comparar el índice `i` con la letra en lugar de mirar `estante[i]`.",
        "Añadir `estante[i]` o el estante entero en vez de añadir `i`.",
        "Usar `print` en lugar de `return`.",
    ])

    # Resumen
    cells.extend([
        markdown_cell(
            "# Resumen final\n\n"
            "| Ejercicio | Respuesta oficial | Puntos |\n"
            "|---|---|---:|\n"
            "| A1 | b) 3 | 2 |\n"
            "| A2 | a) N | 2 |\n"
            "| A3 | c) `a = 10`, `b = None` | 2 |\n"
            "| A4 | d) 2 | 2 |\n"
            "| B1 | tabla de 5 filas; `Multados: 3`, `Revisados: 5` | 3 |\n"
            "| B2 | `NNCN`; `2` | 2 |\n"
            "| B3 | `1`, `2`, `0`; 2 vueltas en la primera llamada | 4 |\n"
            "| B4 | `3`; `['novela', 'comic']`; `2` | 2 |\n"
            "| C1 | `contar_novelas`: 2, 2, 0 | 3 |\n"
            "| C2 | `posicion_final`: 1, -2, 0 | 4 |\n"
            "| C3 | `huecos`: [1, 2, 4], [] | 4 |\n"
            "| **Total** | **A: 8 · B: 11 · C: 11** | **30** |"
        ),
        markdown_cell(
            "## Dudas frecuentes\n\n"
            "**¿Por qué `b` vale `None` en A3?**  \n"
            "`multa_b` imprime el resultado, pero no tiene `return`; por eso no entrega "
            "un valor y la asignación recibe `None`.\n\n"
            "**¿Por qué son 2 vueltas en B3?**  \n"
            "El bucle comprueba primero el grosor 2, que cabe, y después el grosor 3, "
            "que no cabe en los 2 cm restantes. Esa comprobación sucede en la segunda "
            "vuelta.\n\n"
            "**¿Me quitan puntos por la sintaxis?**  \n"
            "No se restan puntos por errores de sintaxis. En C también puntúa la idea "
            "correcta aunque el código no funcione del todo.\n\n"
            "**¿Se acepta una salida con otro formato?**  \n"
            "Sí, si el contenido es equivalente: por ejemplo, `NNCN` con comillas o "
            "«3 multados» en vez de «Multados: 3».\n\n"
            "**¿Qué hago si no escribí código en C?**  \n"
            "Si los resultados de los ejemplos son correctos, se concede 1 punto."
        ),
    ])

    notebook = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {
                "name": "python",
                "version": "3",
                "file_extension": ".py",
                "mimetype": "text/x-python",
            },
        },
    )
    return notebook


def rendered_stdout(cell):
    return "".join(
        output.get("text", "")
        for output in cell.get("outputs", [])
        if output.get("output_type") == "stream" and output.get("name") == "stdout"
    ).rstrip("\n")


def verify_answer_outputs(notebook):
    found = {}
    for cell in notebook.cells:
        for tag in cell.metadata.get("tags", []):
            if tag.startswith("answer:"):
                found[tag.removeprefix("answer:")] = rendered_stdout(cell)
    assert found == EXPECTED_OUTPUTS, (
        f"Las salidas del cuaderno no coinciden con la clave: {found!r}"
    )


def png_chunks(png_bytes):
    position = 8
    chunks = []
    while position < len(png_bytes):
        length = struct.unpack(">I", png_bytes[position:position + 4])[0]
        kind = png_bytes[position + 4:position + 8]
        data = png_bytes[position + 8:position + 8 + length]
        chunks.append((kind, data))
        position += length + 12
    return chunks


def recompress_png(png_bytes, level, mem_level, strategy):
    chunks = png_chunks(png_bytes)
    pixels = zlib.decompress(
        b"".join(data for kind, data in chunks if kind == b"IDAT")
    )
    compressor = zlib.compressobj(
        level, zlib.DEFLATED, zlib.MAX_WBITS, mem_level, strategy
    )
    compressed = compressor.compress(pixels) + compressor.flush()
    result = bytearray(png_bytes[:8])
    inserted_idat = False
    for kind, data in chunks:
        if kind == b"IDAT":
            if inserted_idat:
                continue
            kind, data = b"IDAT", compressed
            inserted_idat = True
        result.extend(struct.pack(">I", len(data)))
        result.extend(kind)
        result.extend(data)
        result.extend(struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF))
    return bytes(result)


def sanitize_notebook_images(notebook):
    strategies = [
        zlib.Z_DEFAULT_STRATEGY,
        zlib.Z_FILTERED,
        zlib.Z_RLE,
        zlib.Z_FIXED,
        zlib.Z_HUFFMAN_ONLY,
    ]
    candidates = itertools.product(
        range(9, 0, -1), range(9, 0, -1), strategies
    )
    for cell in notebook.cells:
        for output in cell.get("outputs", []):
            data = output.get("data", {})
            encoded = data.get("image/png")
            if not encoded:
                continue
            if isinstance(encoded, list):
                encoded = "".join(encoded)
            original = base64.b64decode(encoded)
            for level, mem_level, strategy in candidates:
                candidate = base64.b64encode(
                    recompress_png(original, level, mem_level, strategy)
                ).decode("ascii")
                if not BANNED_PATTERN.search(candidate):
                    data["image/png"] = candidate
                    break
            else:
                raise AssertionError("No se encontró una codificación PNG segura.")
            candidates = itertools.product(
                range(9, 0, -1), range(9, 0, -1), strategies
            )


def render_previews():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    namespace = {}
    exec(compile(TOOLBOX_SOURCE, "<caja-visual>", "exec"), namespace)
    namespace["dibujar_pizarra"](
        "append agrega un elemento",
        [
            ("ANTES: ['Momo', 'Matilda']  →  len = 2", namespace["TIZA"]),
            ("append('Dune')  →  añade al final", namespace["TIZA_AMARILLA"]),
            ("DESPUÉS: ['Momo', 'Matilda', 'Dune']  →  len = 3", namespace["TIZA"]),
        ],
        alto=2.8,
        guardar=str(FIGURES_DIR / "pizarra-a1.png"),
    )
    namespace["dibujar_estante"](
        "NC.N", marcar=[0], titulo="estante[0]: primera casilla"
    )
    import matplotlib.pyplot as plt

    # Re-render the shelf figure into a portable PNG file for review.
    fig, ax = plt.subplots(figsize=(5.5, 2.2), dpi=100)
    fig.patch.set_facecolor(namespace["FONDO_PIZARRA"])
    ax.set_facecolor(namespace["FONDO_PIZARRA"])
    ax.text(0.05, 0.94, "estante[0]: primera casilla", transform=ax.transAxes,
            color=namespace["TIZA_AMARILLA"], fontsize=15, fontweight="bold",
            family="DejaVu Sans Mono", va="top")
    for i, letra in enumerate("NC.N"):
        color = namespace["TIZA_AMARILLA"] if i == 0 else namespace["TIZA"]
        ax.add_patch(plt.Rectangle((i, 0), 1, 1, facecolor="#205b49",
                                   edgecolor=color, linewidth=2 if i == 0 else 1.5))
        ax.text(i + 0.5, 0.56, letra, ha="center", va="center", fontsize=20,
                color=color, family="DejaVu Sans Mono", fontweight="bold")
        ax.text(i + 0.5, -0.2, str(i), ha="center", va="center", fontsize=12,
                color=namespace["TIZA"])
    ax.set_xlim(-0.15, 4.15)
    ax.set_ylim(-0.55, 1.05)
    ax.axis("off")
    fig.savefig(FIGURES_DIR / "pizarra-a2.png", dpi=100,
                facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    namespace["dibujar_tabla_pizarra"](
        "B1: seguimiento vuelta a vuelta",
        ["Vuelta", "d", "multados", "revisados"],
        [["1", "4", "1", "1"], ["2", "1", "1", "2"],
         ["3", "5", "2", "3"], ["4", "0", "2", "4"],
         ["5", "6", "3", "5"]],
        guardar=str(FIGURES_DIR / "pizarra-b1.png"),
    )
    # Save a corridor figure without showing a GUI window.
    fig, ax = plt.subplots(figsize=(9, 2.7), dpi=100)
    fig.patch.set_facecolor(namespace["FONDO_PIZARRA"])
    ax.set_facecolor(namespace["FONDO_PIZARRA"])
    ax.set_xlim(-3.5, 3.5)
    ax.set_ylim(-1.05, 1.7)
    ax.axis("off")
    ax.text(0.5, 0.98, "Ruta EEO: este suma, oeste resta",
            transform=ax.transAxes, ha="center", va="top",
            color=namespace["TIZA_AMARILLA"], fontsize=15, fontweight="bold",
            family="DejaVu Sans Mono")
    ax.plot([-3, 3], [0, 0], color=namespace["TIZA"], linewidth=2)
    for position in range(-3, 4):
        ax.add_patch(plt.Rectangle((position - 0.34, -0.28), 0.68, 0.56,
                                   facecolor="#205b49",
                                   edgecolor=namespace["TIZA_AZUL"] if position == 0
                                   else namespace["TIZA"], linewidth=2 if position == 0 else 1))
        ax.text(position, -0.58, str(position), ha="center", va="top",
                color=namespace["TIZA"], fontsize=11,
                family="DejaVu Sans Mono")
    ax.text(0, 0.36, "mostrador", ha="center", color=namespace["TIZA_AZUL"],
            fontsize=10, family="DejaVu Sans Mono")
    position = 0
    for step, letter in enumerate("EEO", 1):
        next_position = position + (1 if letter == "E" else -1)
        height = 0.56 + 0.24 * (step - 1)
        ax.annotate("", xy=(next_position, height), xytext=(position, height),
                    arrowprops={"arrowstyle": "-|>",
                                "color": namespace["TIZA_AMARILLA"], "linewidth": 2})
        ax.text((position + next_position) / 2, height + 0.10,
                f"{step}:{letter}", ha="center", color=namespace["TIZA"],
                fontsize=10, family="DejaVu Sans Mono")
        position = next_position
    ax.plot(position, 0, marker="s", markersize=11,
            color=namespace["TIZA_AMARILLA"], markeredgecolor=namespace["TIZA"])
    ax.text(0.5, 0.02, "fin: x = 1", transform=ax.transAxes,
            ha="center", color=namespace["TIZA_AMARILLA"], fontsize=12,
            family="DejaVu Sans Mono")
    fig.savefig(FIGURES_DIR / "pizarra-c2.png", dpi=100,
                facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    notebook = build_notebook()
    client = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(WORK_DIR)}},
    )
    executed = client.execute()
    sanitize_notebook_images(executed)
    verify_answer_outputs(executed)
    nbformat.write(executed, NOTEBOOK_PATH)
    notebook_text = nbformat.writes(executed)
    assert not BANNED_PATTERN.search(notebook_text), (
        "El cuaderno contiene una coincidencia en la lista de términos restringidos."
    )
    assert NOTEBOOK_PATH.stat().st_size < 5 * 1024 * 1024, (
        "El cuaderno debe ocupar menos de 5 MiB."
    )
    render_previews()
    print(f"Notebook ejecutado y guardado: {NOTEBOOK_PATH}")
    print(f"Salidas A1-A4 y B1-B4 coinciden con la clave ({len(EXPECTED_OUTPUTS)} comprobaciones).")
    print(f"Previsualizaciones guardadas en: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
