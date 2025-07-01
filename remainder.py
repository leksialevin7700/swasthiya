from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["medication_db"]
reminders_collection = db["reminders"]

@app.route('/')
def home():
    return render_template('index.html')

# Add a new reminder
@app.route('/add_reminder', methods=['POST'])
def add_reminder():
    data = request.json
    reminders_collection.insert_one(data)
    return jsonify({"message": "Reminder added successfully!"})

# Get all reminders
@app.route('/get_reminders', methods=['GET'])
def get_reminders():
    reminders = list(reminders_collection.find({}, {"_id": 0}))
    return jsonify(reminders)

# Delete a reminder
@app.route('/delete_reminder', methods=['POST'])
def delete_reminder():
    data = request.json
    reminders_collection.delete_one({"medicine_name": data["medicine_name"]})
    return jsonify({"message": "Reminder deleted!"})

if __name__ == '__main__':
    app.run(debug=True, port=4004)

