from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session
import mysql.connector
import pandas as pd
from flask import flash


app = Flask(__name__)

# Set the secret key for session management !! errors otherwise !! and errors are not good. Debugging sucks! But is kind of fun. Like a puzzle, with no tutorial...
app.secret_key = "408"

# Database connection
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "YourPasswordForPC",
    "database": "PetAdoptionDB"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# link of animal for presentation https://th.bing.com/th/id/R.abbef5ac29bd30e901e417e2f23d09a6?rik=gOSRZroMWnsljg&pid=ImgRaw&r=0

@app.route("/pets", methods=["GET"])
def view_pets():
    # Fetch shelters for the filter dropdown
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT shelter_id, shelter_name FROM Shelters")
    shelters = cursor.fetchall()

    # Fetch pets with filters
    species = request.args.get("species")
    age = request.args.get("age")
    shelter_id = request.args.get("shelter_id")
    
    query = "SELECT * FROM Pets WHERE 1=1"
    params = []

    if species:
        query += " AND species = %s"
        params.append(species)
    
    if age:
        query += " AND age = %s"
        params.append(age)
    
    if shelter_id:
        query += " AND shelter_id = %s"
        params.append(shelter_id)
    
    cursor.execute(query, tuple(params))
    pets = cursor.fetchall()
    conn.close()

    return render_template("pets.html", pets=pets, shelters=shelters)


@app.route("/update_pet_photo/<int:pet_id>", methods=["POST"])
def update_pet_photo(pet_id):
    new_image_url = request.form["image_url"]  # Get the new image URL from the form
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update the photo URL in the database
    cursor.execute("UPDATE Pets SET image_url = %s WHERE pet_id = %s", (new_image_url, pet_id))
    conn.commit()
    conn.close()
    
    # Redirect back to the pets page
    return redirect(url_for("view_pets"))

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        # add logic if we want, to connect to database and keep record of messages, etc.
        print(f"New Contact Message from {name} ({email}): {message}")

        return render_template("contact.html", success=True)

    return render_template("contact.html", success=False)



@app.route("/pets_by_shelter", methods=["GET"])
def pets_by_shelter():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Query with subquery
    query = """
        SELECT p.pet_id, p.name, p.species, p.breed, s.shelter_name
        FROM Pets p
        JOIN Shelters s ON p.shelter_id = s.shelter_id
        WHERE s.shelter_id IN (
            SELECT shelter_id
            FROM Pets
            GROUP BY shelter_id
            HAVING COUNT(*) > 1
        )
    """
    cursor.execute(query)
    pets_by_shelter = cursor.fetchall()
    conn.close()

    return render_template("pets_by_shelter.html", pets_by_shelter=pets_by_shelter)



@app.route("/approved_applications", methods=["GET"])
def approved_applications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Query 1: Join Users, Adoption_Applications, and Pets to get details about approved applications
    query1 = """
        SELECT a.application_id, u.username, p.name AS pet_name, p.species, s.shelter_name
        FROM Adoption_Applications a
        JOIN Users u ON a.user_id = u.user_id
        JOIN Pets p ON a.pet_id = p.pet_id
        JOIN Shelters s ON p.shelter_id = s.shelter_id
        WHERE a.status = 'Approved'
    """
    cursor.execute(query1)
    approved_applications = cursor.fetchall()

    # Query 2: Join Pets, Pet_Health_Record, and Shelters to get pets' health details by shelter
    query2 = """
        SELECT p.name AS pet_name, p.species, h.checkup_date, h.vaccinations, s.shelter_name
        FROM Pets p
        JOIN Pet_Health_Record h ON p.pet_id = h.pet_id
        JOIN Shelters s ON p.shelter_id = s.shelter_id
        ORDER BY s.shelter_name, p.name
    """
    cursor.execute(query2)
    pet_health_by_shelter = cursor.fetchall()

    conn.close()

    return render_template(
        "approved_applications.html",
        approved_applications=approved_applications,
        pet_health_by_shelter=pet_health_by_shelter,
    )

# Display Approved Applications View

@app.route("/view_approved_applications", methods=["GET"])
def view_approved_applications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM ApprovedApplicationsView")
    approved_applications = cursor.fetchall()
    conn.close()

    return render_template(
        "view_approved_applications.html", approved_applications=approved_applications
    )


# Display Pet Health Records View

@app.route("/view_pet_health_records", methods=["GET"])
def view_pet_health_records():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PetHealthRecordsView")
    pet_health_records = cursor.fetchall()
    conn.close()

    return render_template(
        "view_pet_health_records.html", pet_health_records=pet_health_records
    )



@app.route("/species_summary", methods=["GET"])
def species_summary():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Aggregation query
    query = """
        SELECT species, COUNT(*) AS total_pets
        FROM Pets
        GROUP BY species
    """
    cursor.execute(query)
    species_summary = cursor.fetchall()
    conn.close()

    return render_template("species_summary.html", species_summary=species_summary)


@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch all available pets from the Pets table
    cursor.execute("""
        SELECT pet_id, name, species, breed, age, gender, status, image_url
        FROM Pets
        WHERE status = 'Available'
    """)
    pets = cursor.fetchall()
    conn.close()

    return render_template("index.html", pets=pets)


@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch available pets from the Pets table
    cursor.execute("""
        SELECT pet_id, name, species, breed, age, gender, status, image_url
        FROM Pets
        WHERE status = 'Available'
    """)
    pets = cursor.fetchall()
    conn.close()

    return render_template("home.html", pets=pets)



@app.route("/add_pet", methods=["GET", "POST"])
def add_pet():
    if request.method == "POST":
        # Get form data
        shelter_id = request.form["shelter_id"]
        name = request.form["name"]
        species = request.form["species"]
        breed = request.form.get("breed", None)
        age = request.form.get("age", None)
        gender = request.form["gender"]
        description = request.form.get("description", None)
        arrival_date = request.form["arrival_date"]
        image_url = request.form.get("image_url", None)

        # Insert into the database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Pets (shelter_id, name, species, breed, age, gender, status, description, arrival_date, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, 'Available', %s, %s, %s)
        """, (shelter_id, name, species, breed, age, gender, description, arrival_date, image_url))
        conn.commit()
        conn.close()

        flash("New pet added successfully!", "success")
        return redirect(url_for("index"))
    
    return render_template("add_pet.html")

@app.route("/delete_pet/<int:pet_id>")
def delete_pet(pet_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Pets SET status = 'Unavailable' WHERE pet_id = %s", (pet_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_pets"))

@app.route("/generate_report")
def generate_report():
    conn = get_db_connection()
    query = "SELECT * FROM Pets WHERE status = 'Available'"
    df = pd.read_sql(query, conn)
    report_path = "reports/available_pets.xlsx"
    df.to_excel(report_path, index=False)
    conn.close()
    return send_file(report_path, as_attachment=True)



# User Login and Registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        phone = request.form["phone"]
        address = request.form["address"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Users (username, password, email, phone, address)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password, email, phone, address))
        conn.commit()
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            # test
            session["user_id"] = user["user_id"]  # Store user ID in session
            session["user_type"] = user["user_type"]  # Store user type in session
            return redirect(url_for("index"))
        else:
            return "Invalid credentials"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Shelter Management
@app.route("/shelters")
def view_shelters():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Shelters")
    shelters = cursor.fetchall()
    conn.close()
    return render_template("shelters.html", shelters=shelters)

@app.route("/add_shelter", methods=["GET", "POST"])
def add_shelter():
    if request.method == "POST":
        shelter_name = request.form["shelter_name"]
        location = request.form["location"]
        contact_phone = request.form["contact_phone"]
        contact_email = request.form["contact_email"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Shelters (shelter_name, location, contact_phone, contact_email)
            VALUES (%s, %s, %s, %s)
        """, (shelter_name, location, contact_phone, contact_email))
        conn.commit()
        conn.close()
        return redirect(url_for("view_shelters"))
    return render_template("add_shelter.html")

# Adoption Applications
@app.route("/apply_adoption", methods=["GET", "POST"])
def apply_adoption():
    if request.method == "POST":
        pet_id = request.form.get("pet_id")  # Get the selected pet_id from the form
        user_id = session.get("user_id")
        if not user_id:
            return redirect(url_for("login"))
        
        if not pet_id:
            flash("Please select a pet to apply for adoption.", "warning")
            return redirect(url_for("apply_adoption"))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Adoption_Applications (user_id, pet_id)
            VALUES (%s, %s)
        """, (user_id, pet_id))
        conn.commit()
        conn.close()
        return redirect(url_for("view_applications"))

    # Fetch the list of available animals
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT pet_id, name, breed FROM Pets WHERE status = 'available'")
    pets = cursor.fetchall()
    conn.close()

    return render_template("apply_adoption.html", pets=pets)


@app.route("/approve_application/<int:pet_id>", methods=["POST"])
def approve_application(pet_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Adoption_Applications SET status = 'Approved' WHERE pet_id = %s", (pet_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_applications"))

@app.route("/reject_application/<int:pet_id>", methods=["POST"])
def reject_application(pet_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Adoption_Applications SET status = 'Rejected' WHERE pet_id = %s", (pet_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("view_applications"))



@app.route("/view_applications")
def view_applications():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT a.application_id, u.username, p.name AS pet_name, a.status
        FROM Adoption_Applications a
        JOIN Users u ON a.user_id = u.user_id
        JOIN Pets p ON a.pet_id = p.pet_id
    """)
    applications = cursor.fetchall()
    conn.close()
    return render_template("applications.html", applications=applications)

@app.route("/health_records")
def health_records():
    # Fetch all health records along with pet details
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.pet_id, p.name, p.species, p.breed, phr.checkup_date, phr.weight, phr.vaccinations, phr.health_notes
        FROM Pets p
        LEFT JOIN Pet_Health_Record phr ON p.pet_id = phr.pet_id
        ORDER BY p.pet_id, phr.checkup_date DESC
    """)
    records = cursor.fetchall()
    conn.close()

    # Group health records by pet
    pets = {}
    for record in records:
        pet_id = record['pet_id']
        if pet_id not in pets:
            pets[pet_id] = {
                "pet_id": pet_id,
                "name": record['name'],
                "species": record['species'],
                "breed": record['breed'],
                "health_records": []
            }
        if record['checkup_date']:
            pets[pet_id]["health_records"].append({
                "checkup_date": record['checkup_date'],
                "weight": record['weight'],
                "vaccinations": record['vaccinations'],
                "health_notes": record['health_notes']
            })

    return render_template("health_records.html", pets=pets)


@app.route("/health_records/<int:pet_id>")
def pet_health_records(pet_id):
    # Fetch detailed health records for a specific pet
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM Pet_Health_Record WHERE pet_id = %s ORDER BY checkup_date DESC
    """, (pet_id,))
    records = cursor.fetchall()

    cursor.execute("SELECT name, species, breed FROM Pets WHERE pet_id = %s", (pet_id,))
    pet = cursor.fetchone()
    conn.close()

    return render_template("pet_health_records.html", pet=pet, records=records)


@app.route("/add_health_record", methods=["GET", "POST"])
def add_health_record():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        # Get data from the form
        pet_id = request.form["pet_id"]
        checkup_date = request.form["checkup_date"]
        weight = request.form["weight"]
        vaccinations = request.form["vaccinations"]
        health_notes = request.form["health_notes"]

        # Insert health record into the database
        cursor.execute("""
            INSERT INTO Pet_Health_Record (pet_id, checkup_date, weight, vaccinations, health_notes)
            VALUES (%s, %s, %s, %s, %s)
        """, (pet_id, checkup_date, weight, vaccinations, health_notes))
        conn.commit()
        conn.close()
        return redirect(url_for("health_records"))

    # Fetch all pets for selection
    cursor.execute("SELECT pet_id, name FROM Pets WHERE status != 'Adopted'")
    pets = cursor.fetchall()
    conn.close()
    return render_template("add_health_record.html", pets=pets)



if __name__ == "__main__":
    app.run(debug=True)
