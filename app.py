import os
import csv
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, flash

app = Flask(__name__)
app.secret_key = "cambia-esta-clave"

CSV_PATH = os.path.join(os.path.dirname(__file__), "novedades.csv")

# Esquema de columnas (superset para cubrir ALTA/BAJA/REEMPLAZO/OTROS)
FIELDS = [
    "timestamp",
    "legajo",
    "nombre",
    "tipo_empleado",         # Docente / No Docente
    "tipo_novedad",          # Alta / Baja / Reemplazo / Otros

    # ALTA (y REEMPLAZO si es persona nueva)
    "fecha_nacimiento",
    "dni",
    "cuil",
    "domicilio",
    "email",
    "subvencionado",         # Si/No
    "trabaja_otra_institucion", # Si/No
    "horas_catedras",        # número
    "asignaciones_familiares",  # Si/No
    "cantidad_hijos",
    "nivel",                 # Inicial/Primario/Secundario/Terciario
    "fecha_alta",
    "cargo",

    # REEMPLAZO (cuando ya trabaja en el colegio)
    "reemplazo_persona_ya_trabaja", # Si/No
    "reemplazo_cargo_que_cubre",
    "fecha_inicio_reemplazo",
    "fecha_fin_reemplazo",

    # BAJA
    "fecha_baja",
    "motivo_baja",           # Jubilación/Renuncia/Despido

    # OTROS
    "tipo_otro",             # Anticipo/Inasistencia/Lic. sin goce

    # Campos heredados del MVP anterior (opcionales)
    "cargos_actuales",
    "tipo_movimiento",
    "subvencion",
    "codigo",
    "observaciones",
]

def ensure_csv():
    """Crea o migra el CSV para que tenga el encabezado FIELDS preservando datos existentes."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(FIELDS)
        return

    # Verificar encabezado existente
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            header = []

    if header != FIELDS:
        # Leer registros existentes (si el header actual es válido)
        existing = []
        if header:
            with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
                dr = csv.DictReader(f)
                for r in dr:
                    existing.append(r)
        # Reescribir con nuevo header
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)
            for r in existing:
                w.writerow([r.get(k, "") for k in FIELDS])

def append_row(data: dict):
    ensure_csv()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([data.get(k, "") for k in FIELDS])

def read_all_rows():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/enviar", methods=["POST"])
def enviar():
    # Campos base
    legajo = (request.form.get("legajo") or "").strip()
    nombre = (request.form.get("nombre") or "").strip()
    tipo_empleado = (request.form.get("tipo_empleado") or "").strip()
    tipo_novedad = (request.form.get("tipo_novedad") or "").strip()

    # Alta / Persona nueva (también aplica a Reemplazo si NO trabaja en el colegio)
    fecha_nacimiento = (request.form.get("fecha_nacimiento") or "").strip()
    dni = (request.form.get("dni") or "").strip()
    cuil = (request.form.get("cuil") or "").strip()
    domicilio = (request.form.get("domicilio") or "").strip()
    email = (request.form.get("email") or "").strip()
    subvencionado = (request.form.get("subvencionado") or "").strip()
    trabaja_otra_institucion = (request.form.get("trabaja_otra_institucion") or "").strip()
    horas_catedras = (request.form.get("horas_catedras") or "").strip()
    asignaciones_familiares = (request.form.get("asignaciones_familiares") or "").strip()
    cantidad_hijos = (request.form.get("cantidad_hijos") or "").strip()
    nivel = (request.form.get("nivel") or "").strip()
    fecha_alta = (request.form.get("fecha_alta") or "").strip()
    cargo = (request.form.get("cargo") or "").strip()

    # Reemplazo
    reemplazo_persona_ya_trabaja = (request.form.get("reemplazo_persona_ya_trabaja") or "").strip()
    reemplazo_cargo_que_cubre = (request.form.get("reemplazo_cargo_que_cubre") or "").strip()
    fecha_inicio_reemplazo = (request.form.get("fecha_inicio_reemplazo") or "").strip()
    fecha_fin_reemplazo = (request.form.get("fecha_fin_reemplazo") or "").strip()

    # Baja
    fecha_baja = (request.form.get("fecha_baja") or "").strip()
    motivo_baja = (request.form.get("motivo_baja") or "").strip()

    # Otros
    tipo_otro = (request.form.get("tipo_otro") or "").strip()

    # Extras heredados
    cargos_actuales = (request.form.get("cargos_actuales") or "").strip()
    tipo_movimiento = (request.form.get("tipo_movimiento") or "").strip()
    subvencion = (request.form.get("subvencion") or "").strip()
    codigo = (request.form.get("codigo") or "").strip()
    observaciones = (request.form.get("observaciones") or "").strip()

    # Validaciones mínimas (lo crítico para arrancar)
    errores = []
    if not nombre:
        errores.append("El campo 'Nombre y apellido' es obligatorio.")
    if not tipo_empleado:
        errores.append("Seleccioná 'Docente' o 'No Docente'.")
    if not tipo_novedad:
        errores.append("Seleccioná el 'Tipo de novedad'.")

    # Reglas por tipo
    if tipo_novedad == "Alta":
        if not fecha_alta:
            errores.append("En 'Alta', la 'Fecha de alta' es obligatoria.")
        if not nivel:
            errores.append("En 'Alta', el 'Nivel' es obligatorio.")
        if not cargo:
            errores.append("En 'Alta', el 'Cargo' es obligatorio.")

    elif tipo_novedad == "Baja":
        if not fecha_baja:
            errores.append("En 'Baja', la 'Fecha de baja' es obligatoria.")
        if not motivo_baja:
            errores.append("En 'Baja', el 'Motivo' es obligatorio.")

    elif tipo_novedad == "Reemplazo":
        if reemplazo_persona_ya_trabaja not in ("Si", "No"):
            errores.append("En 'Reemplazo', indicá si la persona ya trabaja en el colegio (Sí/No).")
        if reemplazo_persona_ya_trabaja == "Si":
            if not reemplazo_cargo_que_cubre:
                errores.append("En 'Reemplazo (ya trabaja)', indicá el cargo que cubre.")
            if not fecha_inicio_reemplazo or not fecha_fin_reemplazo:
                errores.append("En 'Reemplazo (ya trabaja)', indicá fechas de inicio y fin.")
        else:
            # Tratamos como un ALTA
            if not fecha_alta:
                errores.append("En 'Reemplazo (nuevo)', la 'Fecha de alta' es obligatoria.")
            if not nivel:
                errores.append("En 'Reemplazo (nuevo)', el 'Nivel' es obligatorio.")
            if not cargo:
                errores.append("En 'Reemplazo (nuevo)', el 'Cargo' es obligatorio.")

    elif tipo_novedad == "Otros":
        if not tipo_otro:
            errores.append("En 'Otros', seleccioná el subtipo (Anticipo/Inasistencia/Lic. sin goce).")

    # Validación simple numérica
    if horas_catedras:
        try:
            float(horas_catedras.replace(",", "."))
        except ValueError:
            errores.append("Horas Cátedras debe ser un número válido (ej: 10 o 10.5).")
    if cantidad_hijos:
        if not cantidad_hijos.isdigit():
            errores.append("Cantidad de hijos debe ser un número entero.")

    if errores:
        for e in errores:
            flash(e, "danger")
        return redirect(url_for("index"))

    registro = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "legajo": legajo,
        "nombre": nombre,
        "tipo_empleado": tipo_empleado,
        "tipo_novedad": tipo_novedad,

        "fecha_nacimiento": fecha_nacimiento,
        "dni": dni,
        "cuil": cuil,
        "domicilio": domicilio,
        "email": email,
        "subvencionado": subvencionado,
        "trabaja_otra_institucion": trabaja_otra_institucion,
        "horas_catedras": horas_catedras,
        "asignaciones_familiares": asignaciones_familiares,
        "cantidad_hijos": cantidad_hijos,
        "nivel": nivel,
        "fecha_alta": fecha_alta,
        "cargo": cargo,

        "reemplazo_persona_ya_trabaja": reemplazo_persona_ya_trabaja,
        "reemplazo_cargo_que_cubre": reemplazo_cargo_que_cubre,
        "fecha_inicio_reemplazo": fecha_inicio_reemplazo,
        "fecha_fin_reemplazo": fecha_fin_reemplazo,

        "fecha_baja": fecha_baja,
        "motivo_baja": motivo_baja,

        "tipo_otro": tipo_otro,

        "cargos_actuales": cargos_actuales,
        "tipo_movimiento": tipo_movimiento,
        "subvencion": subvencion,
        "codigo": codigo,
        "observaciones": observaciones,
    }

    append_row(registro)
    flash("¡Novedad registrada!", "success")
    return redirect(url_for("ver"))

@app.route("/ver", methods=["GET"])
def ver():
    rows = read_all_rows()
    try:
        rows.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    except Exception:
        pass
    return render_template("ver.html", rows=rows, total=len(rows))

@app.route("/descargar", methods=["GET"])
def descargar():
    ensure_csv()
    return send_file(
        CSV_PATH,
        as_attachment=True,
        download_name="novedades.csv",
        mimetype="text/csv"
    )

if __name__ == "__main__":
    ensure_csv()
    app.run(debug=True)



