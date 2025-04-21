from flask import Flask, render_template, request, redirect, url_for, session, render_template_string
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "this_is_secret"

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Dummy role-based check
        users = {
            "admin": {"password": "Guadalupe2024", "role": "admin"},
            "Vialidad": {"password": "20242027", "role": "staff"},
            "permisosjuarez": {"password": "2024", "role": "viewer"}
        }
        user = users.get(username)
        if user and user["password"] == password:
            session["logged_in"] = True
            session["role"] = user["role"]
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    search_query = request.args.get("search")
    localidad = request.args.get("localidad")
    mes = request.args.get("mes")

    query = """
        SELECT * FROM (
            SELECT *, STR_TO_DATE(`ï»¿FECHA`, '%m/%d/%Y') AS fecha_real
            FROM `PLATAFORMA-2`
        ) AS sub
        WHERE 1=1
    """
    params = []

    if search_query:
        like = f"%{search_query}%"
        query += """
            AND (
                `ï»¿FECHA` LIKE %s OR
                `FOLIO` LIKE %s OR
                `MODELO` LIKE %s OR
                `TIPO` LIKE %s OR
                `CAPACIDAD` LIKE %s OR
                `SERIE` LIKE %s OR
                `COLOR` LIKE %s OR
                `PUERTAS` LIKE %s OR
                `NOMBRE` LIKE %s OR
                `LOCALIDAD` LIKE %s
            )
        """
        params += [like] * 10

    if localidad:
        query += " AND `LOCALIDAD` = %s"
        params.append(localidad)

    if mes:
        query += " AND MONTH(fecha_real) = %s"
        params.append(int(mes))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description if desc[0] != 'fecha_real']
    data = [tuple(val for i, val in enumerate(row) if cursor.description[i][0] != 'fecha_real') for row in data]
    cursor.close()
    conn.close()

    return render_template("dashboard.html", data=data, columns=column_names, request=request)

@app.route("/dashboard-live")
def dashboard_live():
    if not session.get("logged_in"):
        return "", 401

    search_query = request.args.get("search")
    localidad = request.args.get("localidad")
    mes = request.args.get("mes")

    query = """
        SELECT * FROM (
            SELECT *, STR_TO_DATE(`ï»¿FECHA`, '%m/%d/%Y') AS fecha_real
            FROM `PLATAFORMA-2`
        ) AS sub
        WHERE 1=1
    """
    params = []

    if search_query:
        like = f"%{search_query}%"
        query += """
            AND (
                `ï»¿FECHA` LIKE %s OR
                `FOLIO` LIKE %s OR
                `MODELO` LIKE %s OR
                `TIPO` LIKE %s OR
                `CAPACIDAD` LIKE %s OR
                `SERIE` LIKE %s OR
                `COLOR` LIKE %s OR
                `PUERTAS` LIKE %s OR
                `NOMBRE` LIKE %s OR
                `LOCALIDAD` LIKE %s
            )
        """
        params += [like] * 10

    if localidad:
        query += " AND `LOCALIDAD` = %s"
        params.append(localidad)

    if mes:
        query += " AND MONTH(fecha_real) = %s"
        params.append(int(mes))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    data = cursor.fetchall()
    column_names = [desc[0] for desc in cursor.description if desc[0] != 'fecha_real']
    data = [tuple(val for i, val in enumerate(row) if cursor.description[i][0] != 'fecha_real') for row in data]
    cursor.close()
    conn.close()

    html = render_template_string("""
    <table class=\"table table-bordered table-hover table-striped\">
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
    """, data=data, columns=column_names)

    return html

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)