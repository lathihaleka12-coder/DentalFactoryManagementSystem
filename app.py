
from flask import Flask, render_template, request, redirect
import sqlite3
import os

app = Flask(__name__)

DATABASE = os.path.join(app.root_path, "database", "dental.db")


def get_db():
    return sqlite3.connect(DATABASE)


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS dentists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            dentist_name TEXT NOT NULL,
            job_type TEXT NOT NULL,
            order_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS productions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            technician TEXT NOT NULL,
            stage TEXT NOT NULL,
            start_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending'
        )
    """)

    production_columns = [
        column[1] for column in
        conn.execute("PRAGMA table_info(productions)").fetchall()
    ]

    if "status" not in production_columns:
        conn.execute("""
            ALTER TABLE productions
            ADD COLUMN status TEXT NOT NULL DEFAULT 'Pending'
        """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            patient_name TEXT NOT NULL,
            amount REAL NOT NULL,
            bill_date TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)

    default_settings = [
        ("clinic_name", "Dental Factory"),
        ("phone", ""),
        ("email", ""),
        ("address", "")
    ]

    conn.executemany("""
        INSERT OR IGNORE INTO settings
        (setting_name, setting_value)
        VALUES (?, ?)
    """, default_settings)

    conn.commit()
    conn.close()


# DASHBOARD

@app.route("/")
def home():
    conn = get_db()

    total_patients = conn.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    total_dentists = conn.execute(
        "SELECT COUNT(*) FROM dentists"
    ).fetchone()[0]

    pending_jobs = conn.execute("""
        SELECT COUNT(*) FROM jobs
        WHERE status = 'Pending'
    """).fetchone()[0]

    completed_jobs = conn.execute("""
        SELECT COUNT(*) FROM jobs
        WHERE status = 'Completed'
    """).fetchone()[0]

    todays_production = conn.execute("""
        SELECT COUNT(*) FROM productions
        WHERE start_date = date('now', 'localtime')
    """).fetchone()[0]

    total_production = conn.execute(
        "SELECT COUNT(*) FROM productions"
    ).fetchone()[0]

    total_revenue = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM bills
        WHERE payment_status = 'Paid'
    """).fetchone()[0]

    pending_payment = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM bills
        WHERE payment_status = 'Pending'
    """).fetchone()[0]

    conn.close()

    return render_template(
        "index.html",
        total_patients=total_patients,
        total_dentists=total_dentists,
        pending_jobs=pending_jobs,
        completed_jobs=completed_jobs,
        todays_production=todays_production,
        total_production=total_production,
        total_revenue=total_revenue,
        pending_payment=pending_payment
    )


# PATIENT MANAGEMENT

@app.route("/patients", methods=["GET", "POST"])
def patients():
    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()

        if name and phone and address:
            conn = get_db()
            conn.execute(
                "INSERT INTO patients (name, phone, address) VALUES (?, ?, ?)",
                (name, phone, address)
            )
            conn.commit()
            conn.close()

        return redirect("/patients")

    conn = get_db()
    patient_list = conn.execute(
        "SELECT * FROM patients ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("patients.html", patients=patient_list)


@app.route("/edit_patient/<int:id>", methods=["GET", "POST"])
def edit_patient(id):
    conn = get_db()

    if request.method == "POST":
        name = request.form["name"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()

        if name and phone and address:
            conn.execute(
                "UPDATE patients SET name=?, phone=?, address=? WHERE id=?",
                (name, phone, address, id)
            )
            conn.commit()

        conn.close()
        return redirect("/patients")

    patient = conn.execute(
        "SELECT * FROM patients WHERE id=?", (id,)
    ).fetchone()
    conn.close()

    if patient is None:
        return redirect("/patients")

    return render_template("edit_patient.html", patient=patient)


@app.route("/delete_patient/<int:id>", methods=["POST"])
def delete_patient(id):
    conn = get_db()
    conn.execute("DELETE FROM patients WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/patients")


# DENTIST MANAGEMENT

@app.route("/dentists", methods=["GET", "POST"])
def dentists():
    if request.method == "POST":
        name = request.form["name"].strip()
        specialization = request.form["specialization"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        if name and specialization and phone and email:
            conn = get_db()
            conn.execute("""
                INSERT INTO dentists
                (name, specialization, phone, email)
                VALUES (?, ?, ?, ?)
            """, (name, specialization, phone, email))
            conn.commit()
            conn.close()

        return redirect("/dentists")

    conn = get_db()
    dentist_list = conn.execute(
        "SELECT * FROM dentists ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("dentists.html", dentists=dentist_list)


@app.route("/edit_dentist/<int:id>", methods=["GET", "POST"])
def edit_dentist(id):
    conn = get_db()

    if request.method == "POST":
        name = request.form["name"].strip()
        specialization = request.form["specialization"].strip()
        phone = request.form["phone"].strip()
        email = request.form["email"].strip()

        if name and specialization and phone and email:
            conn.execute("""
                UPDATE dentists
                SET name=?, specialization=?, phone=?, email=?
                WHERE id=?
            """, (name, specialization, phone, email, id))
            conn.commit()

        conn.close()
        return redirect("/dentists")

    dentist = conn.execute(
        "SELECT * FROM dentists WHERE id=?", (id,)
    ).fetchone()
    conn.close()

    if dentist is None:
        return redirect("/dentists")

    return render_template("edit_dentist.html", dentist=dentist)


@app.route("/delete_dentist/<int:id>", methods=["POST"])
def delete_dentist(id):
    conn = get_db()
    conn.execute("DELETE FROM dentists WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dentists")


# JOB TRACKING MANAGEMENT

@app.route("/job_tracking", methods=["GET", "POST"])
def job_tracking():
    if request.method == "POST":
        patient_name = request.form["patient_name"].strip()
        dentist_name = request.form["dentist_name"].strip()
        job_type = request.form["job_type"].strip()
        order_date = request.form["order_date"].strip()
        due_date = request.form["due_date"].strip()
        status = request.form["status"].strip()

        if (patient_name and dentist_name and job_type
                and order_date and due_date and status):
            conn = get_db()
            conn.execute("""
                INSERT INTO jobs
                (patient_name, dentist_name, job_type,
                 order_date, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                patient_name, dentist_name, job_type,
                order_date, due_date, status
            ))
            conn.commit()
            conn.close()

        return redirect("/job_tracking")

    conn = get_db()
    job_list = conn.execute(
        "SELECT * FROM jobs ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("job_tracking.html", jobs=job_list)


@app.route("/edit_job/<int:id>", methods=["GET", "POST"])
def edit_job(id):
    conn = get_db()

    if request.method == "POST":
        patient_name = request.form["patient_name"].strip()
        dentist_name = request.form["dentist_name"].strip()
        job_type = request.form["job_type"].strip()
        order_date = request.form["order_date"].strip()
        due_date = request.form["due_date"].strip()
        status = request.form["status"].strip()

        if (patient_name and dentist_name and job_type
                and order_date and due_date and status):
            conn.execute("""
                UPDATE jobs
                SET patient_name=?, dentist_name=?, job_type=?,
                    order_date=?, due_date=?, status=?
                WHERE id=?
            """, (
                patient_name, dentist_name, job_type,
                order_date, due_date, status, id
            ))
            conn.commit()

        conn.close()
        return redirect("/job_tracking")

    job = conn.execute(
        "SELECT * FROM jobs WHERE id=?", (id,)
    ).fetchone()
    conn.close()

    if job is None:
        return redirect("/job_tracking")

    return render_template("edit_job.html", job=job)


@app.route("/delete_job/<int:id>", methods=["POST"])
def delete_job(id):
    conn = get_db()
    conn.execute("DELETE FROM jobs WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/job_tracking")


# PRODUCTION MANAGEMENT

@app.route("/production", methods=["GET", "POST"])
def production():
    if request.method == "POST":
        job_id = request.form["job_id"].strip()
        technician = request.form["technician"].strip()
        stage = request.form["stage"].strip()
        start_date = request.form["start_date"].strip()
        status = request.form["status"].strip()

        if (job_id.isdigit() and technician and stage
                and start_date and status in
                ["Pending", "In Progress", "Completed"]):

            conn = get_db()
            conn.execute("""
                INSERT INTO productions
                (job_id, technician, stage, start_date, status)
                VALUES (?, ?, ?, ?, ?)
            """, (
                int(job_id), technician, stage,
                start_date, status
            ))
            conn.commit()
            conn.close()

        return redirect("/production")

    conn = get_db()
    production_list = conn.execute("""
        SELECT id, job_id, technician, stage, start_date, status
        FROM productions
        ORDER BY id DESC
    """).fetchall()
    conn.close()

    return render_template(
        "production.html",
        productions=production_list
    )


@app.route("/edit_production/<int:id>", methods=["GET", "POST"])
def edit_production(id):
    conn = get_db()

    if request.method == "POST":
        job_id = request.form["job_id"].strip()
        technician = request.form["technician"].strip()
        stage = request.form["stage"].strip()
        start_date = request.form["start_date"].strip()
        status = request.form["status"].strip()

        if (job_id.isdigit() and technician and stage
                and start_date and status in
                ["Pending", "In Progress", "Completed"]):

            conn.execute("""
                UPDATE productions
                SET job_id=?, technician=?, stage=?,
                    start_date=?, status=?
                WHERE id=?
            """, (
                int(job_id), technician, stage,
                start_date, status, id
            ))
            conn.commit()

        conn.close()
        return redirect("/production")

    production_item = conn.execute("""
        SELECT id, job_id, technician, stage, start_date, status
        FROM productions
        WHERE id = ?
    """, (id,)).fetchone()
    conn.close()

    if production_item is None:
        return redirect("/production")

    return render_template(
        "edit_production.html",
        item=production_item
    )


@app.route("/delete_production/<int:id>", methods=["POST"])
def delete_production(id):
    conn = get_db()
    conn.execute("DELETE FROM productions WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/production")


# BILLING MANAGEMENT

@app.route("/billing", methods=["GET", "POST"])
def billing():
    if request.method == "POST":
        job_id = request.form["job_id"].strip()
        patient_name = request.form["patient_name"].strip()
        amount = request.form["amount"].strip()
        bill_date = request.form["bill_date"].strip()
        payment_method = request.form["payment_method"].strip()
        payment_status = request.form["payment_status"].strip()

        try:
            amount = float(amount)
        except ValueError:
            amount = -1

        if (job_id.isdigit() and patient_name and amount >= 0
                and bill_date and payment_method and payment_status):
            conn = get_db()
            conn.execute("""
                INSERT INTO bills
                (job_id, patient_name, amount, bill_date,
                 payment_method, payment_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                int(job_id), patient_name, amount, bill_date,
                payment_method, payment_status
            ))
            conn.commit()
            conn.close()

        return redirect("/billing")

    conn = get_db()
    bill_list = conn.execute(
        "SELECT * FROM bills ORDER BY id DESC"
    ).fetchall()
    conn.close()

    return render_template("billing.html", bills=bill_list)


@app.route("/edit_bill/<int:id>", methods=["GET", "POST"])
def edit_bill(id):
    conn = get_db()

    if request.method == "POST":
        job_id = request.form["job_id"].strip()
        patient_name = request.form["patient_name"].strip()
        amount = request.form["amount"].strip()
        bill_date = request.form["bill_date"].strip()
        payment_method = request.form["payment_method"].strip()
        payment_status = request.form["payment_status"].strip()

        try:
            amount = float(amount)
        except ValueError:
            amount = -1

        if (job_id.isdigit() and patient_name and amount >= 0
                and bill_date and payment_method and payment_status):
            conn.execute("""
                UPDATE bills
                SET job_id=?, patient_name=?, amount=?, bill_date=?,
                    payment_method=?, payment_status=?
                WHERE id=?
            """, (
                int(job_id), patient_name, amount, bill_date,
                payment_method, payment_status, id
            ))
            conn.commit()

        conn.close()
        return redirect("/billing")

    bill = conn.execute(
        "SELECT * FROM bills WHERE id=?", (id,)
    ).fetchone()
    conn.close()

    if bill is None:
        return redirect("/billing")

    return render_template("edit_bill.html", bill=bill)


@app.route("/delete_bill/<int:id>", methods=["POST"])
def delete_bill(id):
    conn = get_db()
    conn.execute("DELETE FROM bills WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/billing")


# REPORTS

@app.route("/reports")
def reports():
    conn = get_db()

    total_patients = conn.execute(
        "SELECT COUNT(*) FROM patients"
    ).fetchone()[0]

    total_dentists = conn.execute(
        "SELECT COUNT(*) FROM dentists"
    ).fetchone()[0]

    total_jobs = conn.execute(
        "SELECT COUNT(*) FROM jobs"
    ).fetchone()[0]

    total_productions = conn.execute(
        "SELECT COUNT(*) FROM productions"
    ).fetchone()[0]

    total_bills = conn.execute(
        "SELECT COUNT(*) FROM bills"
    ).fetchone()[0]

    total_revenue = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM bills
        WHERE payment_status='Paid'
    """).fetchone()[0]

    pending_amount = conn.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM bills
        WHERE payment_status='Pending'
    """).fetchone()[0]

    job_status = conn.execute("""
        SELECT status, COUNT(*)
        FROM jobs
        GROUP BY status
    """).fetchall()

    production_stages = conn.execute("""
        SELECT stage, COUNT(*)
        FROM productions
        GROUP BY stage
    """).fetchall()

    conn.close()

    return render_template(
        "reports.html",
        total_patients=total_patients,
        total_dentists=total_dentists,
        total_jobs=total_jobs,
        total_productions=total_productions,
        total_bills=total_bills,
        total_revenue=total_revenue,
        pending_amount=pending_amount,
        job_status=job_status,
        production_stages=production_stages
    )


# SETTINGS

@app.route("/settings", methods=["GET", "POST"])
def settings():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            setting_name TEXT PRIMARY KEY,
            setting_value TEXT
        )
    """)

    if request.method == "POST":
        clinic_name = request.form.get("clinic_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()

        settings_data = [
            ("clinic_name", clinic_name),
            ("phone", phone),
            ("email", email),
            ("address", address)
        ]

        try:
            conn.executemany("""
                INSERT INTO settings (setting_name, setting_value)
                VALUES (?, ?)
                ON CONFLICT(setting_name)
                DO UPDATE SET setting_value = excluded.setting_value
            """, settings_data)

            conn.commit()

        except sqlite3.Error as e:
            print("Settings Save Error:", e)

        finally:
            conn.close()

        return redirect("/settings?saved=1")

    settings_rows = conn.execute("""
        SELECT setting_name, setting_value
        FROM settings
    """).fetchall()

    conn.close()

    settings_data = dict(settings_rows)

    return render_template(
        "settings.html",
        settings=settings_data,
        saved=request.args.get("saved") == "1"
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
