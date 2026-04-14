

from flask import request

from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient


app = Flask(__name__)
app.secret_key = "secret123"


# Connect to MongoDB
import certifi
from pymongo import MongoClient
import os

client = MongoClient(
    os.environ.get("MONGO_URI"),
    tls=True,
    tlsCAFile=certifi.where()
)

client = MongoClient("mongodb+srv://darshan:Darsh123@cluster0.dk0funy.mongodb.net/?appName=Cluster0")
db = client["alumni_db"]
db = client["alumni_db"]
collection = db["users"]
alumni_collection = db["alumni"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        # Check user in MongoDB
        user = collection.find_one({
            "email": email,
            "password": password
        })

        if user:
         session["user"] = user["name"]
         session["email"] = user["email"]
         session["role"] = user["role"]

        if user["role"] == "admin":
         return redirect("/admin_dashboard")

        elif user["role"] == "alumni":
         return redirect("/dashboard")

        elif user["role"] == "student":
         return redirect("/student_dashboard")
     
        else:
            return "Invalid Email or Password"

    return render_template("login.html")

@app.route("/view_users")
def view_users():
    if "role" in session and session["role"] == "admin":
        users = collection.find()
        return render_template("view_users.html", users=users)
    else:
        return "Access Denied"

@app.route("/admin_alumni")
def admin_alumni():
    if "role" in session and session["role"] == "admin":
        data = alumni_collection.find()
        return render_template("view_alumni.html", data=data)
    else:
        return "Access Denied" 
    
@app.route("/admin_reports")
def admin_reports():
    if "role" in session and session["role"] == "admin":
        return redirect("/analytics")
    else:
        return "Access Denied"
    
    

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        # Insert into MongoDB
        role = request.form["role"]
        skills = request.form["skills"]
        batch = request.form.get("batch")
        company = request.form.get("company")
        email = request.form.get("email")
        alumni_collection.insert_one({
       "name": name,
       "batch": batch,
       "company": company,
       "role": role,
      "skills": skills,
      "email": email
})

        return "User Registered Successfully!"

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "user" in session:
        return render_template("dashboard.html", name=session["user"])
    else:
        return redirect("/login")

@app.route("/admin_dashboard")
def admin_dashboard():
    if "role" in session and session["role"] == "admin":

        total_users = collection.count_documents({})
        total_alumni = alumni_collection.count_documents({})

        companies = alumni_collection.distinct("company")
        total_companies = len(companies)

        return render_template(
            "admin_dashboard.html",
            name=session["user"],
            users=total_users,
            alumni=total_alumni,
            companies=total_companies
        )

    else:
        return "Access Denied"
    
@app.route("/student_dashboard")
def student_dashboard():
    if "role" in session and session["role"] == "student":
        return render_template("student_dashboard.html", name=session["user"])
    else:
        return redirect("/login")
    
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

@app.route("/profile")
def profile():
    if "email" in session:
        user = collection.find_one({"email": session["email"]})
        return render_template("profile.html", user=user)
    else:
        return redirect("/login")
    
@app.route("/add_alumni", methods=["GET", "POST"])
def add_alumni():
    if request.method == "POST":
        name = request.form["name"]
        batch = request.form["batch"]
        company = request.form["company"]
        role = request.form["role"]
        skills = request.form["skills"]

        alumni_collection.insert_one({
            "name": name,
            "batch": batch,
            "company": company,
            "role": role,
            "skills": skills
        })

        return "Alumni Added Successfully!"

    return render_template("add_alumni.html")

@app.route("/view_alumni")
def view_alumni():
    data = alumni_collection.find()
    return render_template("view_alumni.html", data=data)

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":

        name = request.form.get("name")
        company = request.form.get("company")
        batch = request.form.get("batch")
        

        query = {}

        if name:
            query["name"] = {"$regex": name, "$options": "i"}

        if company:
            query["company"] = {"$regex": company, "$options": "i"}

        if batch:
            query["batch"] = batch


        results = alumni_collection.find(query)

        return render_template("view_alumni.html", data=results)

    return render_template("search.html")

@app.route("/analytics")
def analytics():
    data = alumni_collection.find()

    company_count = {}

    for d in data:
        company = d.get("company", "Unknown")

        if company in company_count:
            company_count[company] += 1
        else:
            company_count[company] = 1

    labels = list(company_count.keys())
    values = list(company_count.values())

    return render_template("analytics.html", labels=labels, values=values)

@app.route("/skill_analysis")
def skill_analysis():

    data = alumni_collection.find()

    skill_count = {}

    for d in data:
        skills = d.get("skills", "")

        skill_list = skills.split(",")

        for skill in skill_list:
            skill = skill.strip().lower()

            if skill:
                if skill in skill_count:
                    skill_count[skill] += 1
                else:
                    skill_count[skill] = 1

    labels = list(skill_count.keys())
    values = list(skill_count.values())

    return render_template("skill_analysis.html", labels=labels, values=values)

@app.route("/contact/<email>")
def contact(email):
    return render_template("contact.html", email=email)

@app.route("/send_message", methods=["POST"])
def send_message():
    sender = session["email"]
    receiver = request.form["receiver"]
    message = request.form["message"]

    db["messages"].insert_one({
        "sender": sender,
        "receiver": receiver,
        "message": message
    })

    return "Message Sent Successfully!"
    

@app.route("/messages")
def messages():
    if "email" in session:
        user_email = session["email"]

        msgs = db["messages"].find({"receiver": user_email})

        return render_template("messages.html", msgs=msgs)

    return redirect("/login")

from bson.objectid import ObjectId

@app.route("/reply/<id>", methods=["GET", "POST"])
def reply(id):
    if request.method == "POST":
        reply_text = request.form["reply"]

        db["messages"].update_one(
            {"_id": ObjectId(id)},
            {"$set": {"reply": reply_text}}
        )

        return redirect("/messages")

    return render_template("reply.html")

@app.route("/chat/<email>", methods=["GET", "POST"])
def chat(email):

    user = session["email"]

    if request.method == "POST":
        message = request.form["message"]

        db["messages"].insert_one({
            "sender": user,
            "receiver": email,
            "message": message
        })

    # Fetch conversation
    messages = db["messages"].find({
        "$or": [
            {"sender": user, "receiver": email},
            {"sender": email, "receiver": user}
        ]
    })

    # Chat list
    chats = db["messages"].distinct("receiver", {"sender": user})

    return render_template("chat.html", messages=messages, chats=chats)

@app.route("/contact")
def contact_page():
    return render_template("contact_page.html")

@app.route("/add_event", methods=["GET", "POST"])
def add_event():
    if "role" in session and session["role"] == "alumni":

        if request.method == "POST":
            title = request.form["title"]
            description = request.form["description"]
            date = request.form["date"]

            db["events"].insert_one({
                "title": title,
                "description": description,
                "date": date,
                "created_by": session["email"]
            })

            return "Event Added Successfully!"

        return render_template("add_event.html")

    return "Access Denied"

@app.route("/events")
def view_events():
    events = db["events"].find()
    return render_template("events.html", events=events)

from bson.objectid import ObjectId

@app.route("/register_event/<id>")
def register_event(id):

    db["registrations"].insert_one({
        "event_id": id,
        "user": session["email"]
    })

    return "Registered Successfully!"
@app.route("/edit_event/<id>", methods=["GET", "POST"])
def edit_event(id):

    event = db["events"].find_one({"_id": ObjectId(id)})

    if request.method == "POST":
        db["events"].update_one(
            {"_id": ObjectId(id)},
            {"$set": {
                "title": request.form["title"],
                "description": request.form["description"],
                "date": request.form["date"]
            }}
        )

        return redirect("/events")

    return render_template("edit_event.html", event=event)

@app.route("/delete_event/<id>")
def delete_event(id):

    db["events"].delete_one({"_id": ObjectId(id)})

    return redirect("/events")


import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)