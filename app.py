import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Project

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mmu_crewfinder_super_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crewfinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Context Processor to automatically initialize DB with dummy listings if empty
@app.before_request
def create_tables():
    db.create_all()
    if Project.query.count() == 0 and User.query.count() == 0:
        # Create a sample test user
        admin = User(username="Divyyeash", email="divyyeash.k@student.mmu.edu.my")
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()
        
        # Populate dummy project listings
        p1 = Project(subject_code="TCP1201", title="Mini IT Project (Web App)", 
                     description="Building a peer-to-peer marketplace app using Flask. Looking for someone strong in frontend design/CSS layout!", 
                     tags="Flask,CSS,FCI", slots_open=2, user_id=admin.id)
        p2 = Project(subject_code="PRG2111", title="OOP Assignment Group 4", 
                     description="Developing a Java-based inventory system. Core structure is down, need assistance managing database operations backend hooks.", 
                     tags="Java,SQLite,FCI", slots_open=1, user_id=admin.id)
        db.session.add_all([p1, p2])
        db.session.commit()

# --- ROUTES ---

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    faculty_filter = request.args.get('faculty', '')

    query = Project.query
    if search_query:
        query = query.filter((Project.title.contains(search_query)) | (Project.subject_code.contains(search_query)))
    if faculty_filter:
        query = query.filter(Project.tags.contains(faculty_filter.upper()))

    projects = query.order_by(Project.date_posted.desc()).all()
    return render_template('index.html', projects=projects, search_query=search_query, faculty_filter=faculty_filter)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or Email already exists!', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please sign in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create-project', methods=['POST'])
@login_required
def create_project():
    subject_code = request.form.get('subject_code')
    title = request.form.get('title')
    description = request.form.get('description')
    tags = request.form.get('tags')
    slots = request.form.get('slots_open')

    new_project = Project(
        subject_code=subject_code, title=title, description=description,
        tags=tags, slots_open=int(slots), user_id=current_user.id
    )
    db.session.add(new_project)
    db.session.commit()
    return redirect(url_for('index'))

# --- AI CHATBOT API ENDPOINT ---
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '').lower()
    
    # Intelligent response router based on MMU keywords
    if 'hello' in user_message or 'hi' in user_message:
        reply = "Hello there! I'm the CrewFinder Assistant. Are you looking for a project partner, or do you want to recruit teammates?"
    elif 'fci' in user_message or 'programming' in user_message or 'flask' in user_message:
        reply = "FCI students are actively recruiting right now! Take a look at the TCP1201 (Mini IT Project) listing on your dashboard."
    elif 'partner' in user_message or 'group' in user_message:
        reply = "To join a crew, simply click the 'Request to Join' button on any project card. Make sure you are logged in!"
    elif 'create' in user_message or 'post' in user_message:
        reply = "You can list your own assignment team by clicking 'Create Team' in the navigation bar."
    else:
        reply = "I'm here to help you navigate CrewFinder! Try asking about 'FCI projects', 'how to join a group', or look at current trending options."
        
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(debug=True)
    