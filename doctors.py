from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/telemedicine"
client = MongoClient(app.config["MONGO_URI"])
db = client['telemedicine']
users_collection = db['doctors']

# Route to display doctor listings with search
@app.route('/')
def doctor_listings():
    specialization = request.args.get('specialization')

    query = {"specialization": {"$regex": specialization, "$options": "i"}} if specialization else {}
    doctors = users_collection.find(query)

    return render_template('doctors.html', 
        doctors=doctors, 
        specialization=specialization
    )

if __name__ == '__main__':
    app.run(debug=True, port=5001)