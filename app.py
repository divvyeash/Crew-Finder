import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Project, Event, Message

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

# --- PLATFORM VIEW ROUTERS & ADVANCED SPECIFICATION FILTERS ---
@app.route('/')
def index():
    search_query = request.args.get('search', '').strip()
    faculty_filter = request.args.get('faculty', '')
    course_filter = request.args.get('course', '')
    skill_filter = request.args.get('skill', '')
    active_tab = request.args.get('tab', 'crews')

    # 1. Gather Projects (Crews) with filtering
    p_query = Project.query
    if search_query:
        p_query = p_query.filter((Project.title.contains(search_query)) | (Project.subject_code.contains(search_query)))
    if faculty_filter:
        p_query = p_query.filter(Project.tags.contains(faculty_filter.upper()))
    projects = p_query.order_by(Project.date_posted.desc()).all()

    # 2. Gather Events
    events = Event.query.order_by(Event.date_created.desc()).all()

    # 3. Gather Portfolios with Advanced Specification Filters
    u_query = User.query
    if course_filter:
        u_query = u_query.filter(User.course.contains(course_filter))
    if skill_filter:
        u_query = u_query.filter(User.skills.contains(skill_filter))
    if search_query:
        u_query = u_query.filter((User.username.contains(search_query)) | (User.skills.contains(search_query)))
    users = u_query.all()

    # Fetch unique courses and skills available for filter dropdown menus
    all_courses = sorted(list(set([u.course for u in User.query.all() if u.course])))
    
    # Calculate unique individual skills across entire database
    raw_skills = [u.skills.split(',') for u in User.query.all() if u.skills]
    all_skills = sorted(list(set([skill.strip() for sublist in raw_skills for skill in sublist])))

    return render_template('index.html', 
                           projects=projects, events=events, users=users, 
                           all_courses=all_courses, all_skills=all_skills,
                           search_query=search_query, faculty_filter=faculty_filter,
                           course_filter=course_filter, skill_filter=skill_filter,
                           active_tab=active_tab)

# --- PORTFOLIO INITIALIZATION & PROFILE EDITOR ---
@app.route('/create-profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        current_user.course = request.form.get('course')
        current_user.semester = request.form.get('semester')
        current_user.skills = request.form.get('skills')
        current_user.bio = request.form.get('bio')
        
        # Select an avatar style seed based on skill focus
        current_user.avatar_seed = request.form.get('avatar_seed', 'bottts')
        
        db.session.commit()
        flash('Your student profile card has been broadcasted to the hub workspace!', 'success')
        return redirect(url_for('index', tab='portfolios'))
        
    return render_template('create_profile.html')

# --- AUTHENTICATION FLOW NODES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Session mounted cleanly. Welcome back, {user.username}!', 'success')
            return redirect(url_for('index'))
        
        flash('Invalid credentials configuration.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Account credential configuration already exists.', 'error')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        # System automatically logs in user and routes them to finish their portfolio details
        login_user(new_user)
        return redirect(url_for('create_profile'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Session unmounted safely. See you next sprint!', 'info')
    return redirect(url_for('index'))

# --- RECRUITMENT & EVENT MANAGEMENT NODES ---
@app.route('/create-project', methods=['POST'])
@login_required
def create_project():
    new_project = Project(
        subject_code=request.form.get('subject_code'), title=request.form.get('title'),
        description=request.form.get('description'), tags=request.form.get('tags'),
        slots_open=int(request.form.get('slots_open')), user_id=current_user.id
    )
    db.session.add(new_project)
    db.session.commit()
    return redirect(url_for('index', tab='crews'))

@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    new_event = Event(
        title=request.form.get('title'), organizer=request.form.get('organizer'),
        date_time=request.form.get('date_time'), venue=request.form.get('venue'),
        description=request.form.get('description'), reward_points=int(request.form.get('reward_points', 50)),
        user_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    return redirect(url_for('index', tab='events'))

# --- REAL-TIME PEER MESSAGING FEATURES ---
@app.route('/api/messages', methods=['GET', 'POST'])
@login_required
def handle_messages():
    if request.method == 'POST':
        data = request.json
        recipient = User.query.filter_by(username=data.get('recipient_username')).first()
        if not recipient:
            return jsonify({"error": "Recipient user profile node not located"}), 404
            
        new_msg = Message(sender_id=current_user.id, recipient_id=recipient.id, content=data.get('content'))
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"success": True})

    # GET: Fetch messages exchanged between logged-in user and selected target partner
    partner_username = request.args.get('partner')
    partner = User.query.filter_by(username=partner_username).first()
    if not partner:
        return jsonify([])

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == partner.id)) |
        ((Message.sender_id == partner.id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    return jsonify([{"sender": m.sender.username, "content": m.content, "time": m.timestamp.strftime("%I:%M %p")} for m in messages])

# --- AI CHATBOT SYSTEM ASSISTANT ---
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '').lower()
    
    if 'hello' in user_message or 'hi' in user_message:
        reply = "Hello! I am your automated CrewFinder Assistant. Use the dashboard tabs to view project teams, check events, or build your portfolio profile card."
    elif 'filter' in user_message or 'specification' in user_message:
        reply = "You can filter peer candidates in the 'Student Portfolios' tab using our specification selectors (Course and Tech Skill matrices)."
    elif 'message' in user_message or 'chat' in user_message:
        reply = "To message a peer directly, click the 'Open Chat Pipeline' option on any profile card to start a secure, real-time message stream."
    else:
        reply = "I'm here to streamline your team formation! Try asking about 'how to filter specifications' or 'sending direct peer messages'."
        
    return jsonify({"reply": reply})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)