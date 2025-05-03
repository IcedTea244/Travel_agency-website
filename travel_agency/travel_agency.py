from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('travel_agency.db')
    cursor = conn.cursor()
    
    
    
    # Users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL)''')

    # Destinations table
    cursor.execute('''CREATE TABLE IF NOT EXISTS destinations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        location TEXT)''')
    
   
    # Experiences table
    cursor.execute('''CREATE TABLE IF NOT EXISTS experiences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        location TEXT NOT NULL,
                        destination TEXT NOT NULL,
                        description TEXT NOT NULL,
                        date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

# Route: Home
@app.route('/')
def home():
    location = request.args.get('location', '')
    experiences = []
    
    if location:
        conn = sqlite3.connect('travel_agency.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT users.username, experiences.destination, experiences.location, 
                   experiences.description, experiences.date_added
            FROM experiences
            JOIN users ON experiences.user_id = users.id
            WHERE experiences.location LIKE ? 
               OR experiences.destination LIKE ?
            ORDER BY experiences.date_added DESC
            LIMIT 10
        ''', ('%' + location + '%', '%' + location + '%'))
        
        experiences = cursor.fetchall()
        conn.close()
    
    return render_template('home.html', experiences=experiences, search_location=location)



# Route: Register new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('travel_agency.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
                         (username, email, password))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return redirect(url_for('profile', user_id=user_id))
        except sqlite3.IntegrityError:
            conn.close()
            return "User with this email already exists!"
    
    return render_template('register.html')

# Route: Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = sqlite3.connect('travel_agency.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return redirect(url_for('profile', user_id=user[0]))
        else:
            return "Invalid credentials"
    
    return render_template('login.html')

# Route: User Profile and Travel Plan
@app.route('/profile/<int:user_id>')
def profile(user_id):
    conn = sqlite3.connect('travel_agency.db')
    cursor = conn.cursor()
    
    # Fetch user details
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        return "User not found", 404
    
    # Fetch user travel experiences with all details
    cursor.execute('''
    SELECT location, destination, description, date_added, id 
    FROM experiences 
    WHERE user_id = ?
    ORDER BY date_added DESC
''', (user_id,))
    experiences = cursor.fetchall()
    
    # Fetch travel plans
    cursor.execute('''
        SELECT destinations.name, travel_plans.itinerary
        FROM travel_plans
        JOIN destinations ON travel_plans.destination_id = destinations.id
        WHERE travel_plans.user_id = ?''', (user_id,))
    plans = cursor.fetchall()
    
    conn.close()
    return render_template('profile.html', user=user, experiences=experiences, plans=plans)


# Route: Search for destinations
@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        # Get the country name entered by the user
        location = request.form['location'].strip()

        # Check if the location is not empty
        if location:
            conn = sqlite3.connect('travel_agency.db')
            cursor = conn.cursor()

            # Fetch destinations matching the location (country name)
            cursor.execute('''
                SELECT name, description, location
                FROM destinations
                WHERE location LIKE ?
            ''', (f'%{location}%',))  # Using LIKE for partial matching

            # Fetch all matching destinations
            destinations = cursor.fetchall()
            conn.close()

            # Render the search result template with the fetched destinations
            return render_template('search_results.html', destinations=destinations)

    # Render the search page if it's a GET request or no location provided
    return render_template('search.html')



## code added new for update experience
# Route: Add a new travel experience
@app.route('/add_experience/<int:user_id>', methods=['POST'])
def add_experience(user_id):
    location = request.form.get('location')
    destination = request.form.get('destination')
    description = request.form.get('description')
    
    if location and destination and description:
        conn = sqlite3.connect('travel_agency.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO experiences (user_id, location, destination, description)
            VALUES (?, ?, ?, ?)''', (user_id, location, destination, description))
        
        conn.commit()
        conn.close()
        
    return redirect(url_for('profile', user_id=user_id))

# Route: Delete a travel experience
@app.route('/delete_experience/<int:user_id>/<int:experience_id>', methods=['POST'])
def delete_experience(user_id, experience_id):
    conn = sqlite3.connect('travel_agency.db')
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM experiences WHERE id = ? AND user_id = ?', (experience_id, user_id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('profile', user_id=user_id))

# Route: Edit a travel experience
@app.route('/edit_experience/<int:user_id>/<int:experience_id>', methods=['GET', 'POST'])
def edit_experience(user_id, experience_id):
    conn = sqlite3.connect('travel_agency.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        # Update the experience in the database
        location = request.form['location']
        destination = request.form['destination']
        description = request.form['description']
        
        cursor.execute('''
            UPDATE experiences
            SET location = ?, destination = ?, description = ?
            WHERE id = ? AND user_id = ?
        ''', (location, destination, description, experience_id, user_id))
        
        conn.commit()
        conn.close()
        
        return redirect(url_for('profile', user_id=user_id))
    
    # Fetch the experience details for the edit form
    cursor.execute('SELECT location, destination, description FROM experiences WHERE id = ? AND user_id = ?', (experience_id, user_id))
    experience = cursor.fetchone()
    conn.close()
    
    return render_template('edit_experience.html', experience=experience, user_id=user_id, experience_id=experience_id)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)