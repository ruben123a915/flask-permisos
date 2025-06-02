from flask import Flask, render_template, request, redirect, url_for, session, render_template_string
import mysql.connector
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd

load_dotenv()

USERS = json.loads(os.getenv("USERS_JSON", "{}"))

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "secret"

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def parse_fecha_string(fecha_str):
    if not fecha_str:
        return None
    formats = ["%d/%m/%y", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(fecha_str, fmt)
        except Exception:
            continue
    return None

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = USERS.get(username)
        if user and user["password"] == password:
            session["logged_in"] = True
            session["role"] = user["role"]
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

def clean_columns(columns):
    # Remove PUERTAS column if exists
    return [col for col in columns if col != "PUERTAS"]

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    search_query = request.args.get("search", "").strip()
    localidad = request.args.get("localidad", "").strip()
    mes = request.args.get("mes", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `PLATAFORMA-2`")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    columns = clean_columns(columns)

    if "FECHA" in columns:
        idx = columns.index("FECHA") + 1
        if "VENCE" not in columns:
            columns.insert(idx, "VENCE")

    filtered_rows = []
    for row in rows:
        row_dict = dict(zip([desc[0] for desc in cursor.description], row))

        # Skip rows with empty or null FOLIO
        folio_val = row_dict.get("FOLIO")
        if not folio_val or str(folio_val).strip() == "":
            continue

        # Filtering:
        if search_query:
            found = False
            sq = search_query.lower()
            for val in row:
                if val and sq in str(val).lower():
                    found = True
                    break
            if not found:
                continue

        if localidad and localidad != row_dict.get("LOCALIDAD", ""):
            continue

        fecha_dt = parse_fecha_string(row_dict.get("FECHA"))
        if mes:
            try:
                mes_int = int(mes)
            except ValueError:
                mes_int = None
            if not fecha_dt or fecha_dt.month != mes_int:
                continue

        fecha_str = row_dict.get("FECHA") or ""
        if fecha_dt:
            fecha_str = fecha_dt.strftime("%d/%m/%y")

        vence_str = ""
        if fecha_dt:
            vence_dt = fecha_dt + relativedelta(months=1)
            vence_str = vence_dt.strftime("%d/%m/%y")

        new_row = []
        for col in columns:
            if col == "VENCE":
                val = vence_str
            elif col == "FECHA":
                val = fecha_str
            else:
                val = row_dict.get(col)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                val = "-"
            new_row.append(val)
        filtered_rows.append(tuple(new_row))

    cursor.close()
    conn.close()

    return render_template("dashboard.html", columns=columns, data=filtered_rows, request=request)

@app.route("/dashboard-live")
def dashboard_live():
    if not session.get("logged_in"):
        return "", 401

    search_query = request.args.get("search", "").strip()
    localidad = request.args.get("localidad", "").strip()
    mes = request.args.get("mes", "").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM `PLATAFORMA-2`")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    columns = clean_columns(columns)

    if "FECHA" in columns:
        idx = columns.index("FECHA") + 1
        if "VENCE" not in columns:
            columns.insert(idx, "VENCE")

    filtered_rows = []
    for row in rows:
        row_dict = dict(zip([desc[0] for desc in cursor.description], row))

        # Skip rows with empty or null FOLIO
        folio_val = row_dict.get("FOLIO")
        if not folio_val or str(folio_val).strip() == "":
            continue

        if search_query:
            found = False
            sq = search_query.lower()
            for val in row:
                if val and sq in str(val).lower():
                    found = True
                    break
            if not found:
                continue

        if localidad and localidad != row_dict.get("LOCALIDAD", ""):
            continue

        fecha_dt = parse_fecha_string(row_dict.get("FECHA"))
        if mes:
            try:
                mes_int = int(mes)
            except ValueError:
                mes_int = None
            if not fecha_dt or fecha_dt.month != mes_int:
                continue

        fecha_str = row_dict.get("FECHA") or ""
        if fecha_dt:
            fecha_str = fecha_dt.strftime("%d/%m/%y")

        vence_str = ""
        if fecha_dt:
            vence_dt = fecha_dt + relativedelta(months=1)
            vence_str = vence_dt.strftime("%d/%m/%y")

        new_row = []
        for col in columns:
            if col == "VENCE":
                val = vence_str
            elif col == "FECHA":
                val = fecha_str
            else:
                val = row_dict.get(col)
            if val is None or (isinstance(val, str) and val.strip() == ""):
                val = "-"
            new_row.append(val)
        filtered_rows.append(tuple(new_row))

    cursor.close()
    conn.close()

    html = render_template_string("""
    <table class="table table-bordered table-hover table-striped">
        <thead>
            <tr>
                <th>#</th>
                {% for col in columns %}
                    <th>{{ col }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in data %}
            <tr>
                <td>{{ loop.index }}</td>
                {% for item in row %}
                    <td>{{ item }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>
    """, columns=columns, data=filtered_rows)

    return html

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/upload-excel", methods=["GET", "POST"])
def upload_excel():
    if not session.get("logged_in") or session.get("role") != "admin":
        return "Unauthorized", 403

    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return "No file uploaded", 400

        try:
            df = pd.read_excel(file)
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT FOLIO FROM `PLATAFORMA-2`")
            existing_folios = set(f[0] for f in cursor.fetchall())

            new_rows = df[~df['FOLIO'].isin(existing_folios)]

            for _, row in new_rows.iterrows():
                values = []
                for col in new_rows.columns:
                    val = row[col]
                    if isinstance(val, pd.Timestamp):
                        val = val.strftime("%d/%m/%y")
                    elif pd.isna(val):
                        val = None
                    values.append(val)

                # Changed here: include all columns (including PUERTAS)
                columns = ', '.join([f"`{col}`" for col in new_rows.columns])
                placeholders = ', '.join(['%s'] * len(new_rows.columns))

                sql = f"INSERT INTO `PLATAFORMA-2` ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, tuple(values))

            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("dashboard"))
        except Exception as e:
            return f"Error processing file: {e}", 500

    return '''
    <h2>Upload Excel File (Admin only)</h2>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file" accept=".xls,.xlsx" required>
      <input type="submit" value="Upload">
    </form>
    '''


if __name__ == "__main__":
    app.run(debug=True)
