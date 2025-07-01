from flask import (Flask, flash, redirect, render_template, request, session, url_for)
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from config import Config
from flask_session import Session
import random
import os
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.config.from_object(Config)
# Initialize session
Session(app)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database connection
client = MongoClient(app.config["MONGO_URI"])
db = client['telemedicine']
users_collection = db['doctors']
bcrypt = Bcrypt(app)

# Sample meet links (in a real app, you might generate these dynamically)
MEET_LINKS = [
    "http://meet.google.com/zga-uqnw-mgv",
    "https://meet.google.com/klm-nopq-rst",
    "https://meet.google.com/uvw-xyz1-234",
    "https://meet.google.com/567-890a-bcd",
    "https://meet.google.com/efg-hijk-lmn"
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home Route
@app.route('/')
def home():
    return render_template('home.html')

# Signup Route
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        specialization = request.form['specialization']
        description = request.form['description']
        experience = request.form['experience']
        
        # Save user to MongoDB
        users_collection.insert_one({
            'name': name,
            'email': email,
            'password': password,
            'specialization': specialization,
            'description': description,
            'experience': experience,
            'meet_links': [],  # Initialize empty list for meet links
            'total_consultations': 0,
            'patient_rating': 'N/A',
            'active_days': 0,
            'profile_pic': None  # Initialize profile picture field
        })
        
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = users_collection.find_one({'email': email})
        
        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['email'] = user['email']
            flash("Login successful!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Invalid credentials. Try again.", "danger")
    
    return render_template('login.html')

# Profile Page (Doctors can update their profile)
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user = users_collection.find_one({'email': session['email']})
    
    if request.method == 'POST':
        updated_specialization = request.form['specialization']
        updated_description = request.form['description']
        updated_experience = request.form['experience']
        
        update_data = {
            'specialization': updated_specialization,
            'description': updated_description,
            'experience': updated_experience
        }
        
        # Handle profile picture upload if provided
        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate a secure filename
                filename = secure_filename(f"{session['email']}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                file.save(file_path)
                
                # Update the profile picture path in database
                update_data['profile_pic'] = f"/static/uploads/profile_pics/{filename}"
        
        users_collection.update_one(
            {'email': session['email']},
            {'$set': update_data}
        )
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    # If user doesn't have meet_links field, initialize it
    if 'meet_links' not in user:
        users_collection.update_one(
            {'email': session['email']},
            {'$set': {'meet_links': []}}
        )
        user = users_collection.find_one({'email': session['email']})
    
    return render_template('profile.html', user=user)

# Add Meet Link to Profile
@app.route('/add_meet_link', methods=['POST'])
def add_meet_link():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # Get user to check existing links
    user = users_collection.find_one({'email': session['email']})
    
    # Select a random Meet link from the available options that isn't already in use
    available_links = [link for link in MEET_LINKS if link not in user.get('meet_links', [])]
    
    if available_links:
        random_link = random.choice(available_links)
        
        # Add the link to the user's profile in MongoDB
        users_collection.update_one(
            {'email': session['email']},
            {'$push': {'meet_links': random_link}}
        )
        
        flash('Google Meet link added to your profile!', 'success')
    else:
        flash('You have already added all available Meet links.', 'warning')
    
    return redirect(url_for('profile'))

# Remove Meet Link from Profile
@app.route('/remove_meet_link/<path:link>', methods=['POST'])
def remove_meet_link(link):
    if 'email' not in session:
        return redirect(url_for('login'))
    
    # Remove the specified link from the user's profile
    users_collection.update_one(
        {'email': session['email']},
        {'$pull': {'meet_links': link}}
    )
    
    flash('Google Meet link removed from your profile!', 'success')
    return redirect(url_for('profile'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True,port=3002)