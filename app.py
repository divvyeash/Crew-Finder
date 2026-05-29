import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Project, Event, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'crewfinder_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crewfinder.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    search = request.args.get('search', '').strip()
    course_filter = request.args.get('course', '')
    skill_filter = request.args.get('skill', '')
    current_tab = request.args.get('tab', 'groups')

    group_query = Project.query
    if search:
        group_query = group_query.filter(Project.title.contains(search) | Project.subject_code.contains(search))
    groups = group_query.order_by(Project.date_posted.desc()).all()

    event_query = Event.query
    if search:
        event_query = event_query.filter(Event.title.contains(search) | Event.description.contains(search))
    events = event_query.order_by(Event.date_created.desc()).all()

    profile_query = User.query
    if course_filter:
        profile_query = profile_query.filter(User.course.contains(course_filter))
    if skill_filter:
        profile_query = profile_query.filter(User.skills.contains(skill_filter))
    if search:
        profile_query = profile_query.filter(User.username.contains(search) | User.skills.contains(search))
    profiles = profile_query.all()

    all_courses = sorted(list(set([u.course for u in User.query.all() if u.course and u.course != "Not specified yet"])))
    all_skills = sorted(list(set([s.strip() for u in User.query.all() if u.skills for s in u.skills.split(',') if u.skills != "None listed yet"])))

    return render_template('index.html', 
                           groups=groups, events=events, profiles=profiles, 
                           all_courses=all_courses, all_skills=all_skills,
                           search_query=search, course_filter=course_filter, skill_filter=skill_filter,
                           current_tab=current_tab)

@app.route('/create-profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST':
        current_user.course = request.form.get('course')
        current_user.semester = request.form.get('semester')
        current_user.skills = request.form.get('skills')
        current_user.bio = request.form.get('bio')
        current_user.avatar_name = request.form.get('avatar_name', 'bottts')
        
        db.session.commit()
        return redirect(url_for('index', tab='profiles'))
        
    return render_template('create_profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if not User.query.filter_by(username=username).first() and not User.query.filter_by(email=email).first():
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('create_profile'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create-group', methods=['POST'])
@login_required
def create_group():
    new_group = Project(
        subject_code=request.form.get('subject_code'), title=request.form.get('title'),
        description=request.form.get('description'), tags=request.form.get('tags'),
        slots_open=int(request.form.get('slots_open')), user_id=current_user.id
    )
    db.session.add(new_group)
    db.session.commit()
    return redirect(url_for('index', tab='groups'))

@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    new_event = Event(
        title=request.form.get('title'), organizer=request.form.get('organizer'),
        date_time=request.form.get('date_time'), venue=request.form.get('venue'),
        description=request.form.get('description'), mmu_points=int(request.form.get('mmu_points', 50)),
        user_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    return redirect(url_for('index', tab='events'))

@app.route('/api/messages', methods=['GET', 'POST'])
@login_required
def handle_messages():
    if request.method == 'POST':
        data = request.json
        new_msg = Message(sender_username=current_user.username, receiver_username=data.get('receiver'), text_content=data.get('message'))
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"success": True})

    chat_partner = request.args.get('partner')
    chat_history = Message.query.filter(
        ((Message.sender_username == current_user.username) & (Message.receiver_username == chat_partner)) |
        ((Message.sender_username == chat_partner) & (Message.receiver_username == current_user.username))
    ).order_by(Message.time_sent.asc()).all()

    return jsonify([{"sender": m.sender_username, "message": m.text_content, "time": m.time_sent.strftime("%I:%M %p")} for m in chat_history])

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    user_msg = request.json.get('message', '').lower()
    if 'filter' in user_msg or 'search' in user_msg:
        reply = "Go to the 'Student Portfolios' tab to filter profiles by Course or Skills."
    elif 'message' in user_msg or 'chat' in user_msg:
        reply = "Click 'Message Leader' or 'Send Message' on any card to open a private chat."
    else:
        reply = "Hi! I'm the CrewFinder Assistant. Ask me about finding groups or chatting with teammates."
    return jsonify({"reply": reply})

def add_sample_data():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            u1 = User(username="Divyyeash", email="divyyeash@student.mmu.edu.my", course="Computer Science", semester="Trimester 2, Year 2", bio="Python backend coder.", skills="Python, Flask, SQL", avatar_name="divy")
            u1.set_password("password123")
            u2 = User(username="Shivanie", email="shivanie@student.mmu.edu.my", course="Information Technology", semester="Trimester 1, Year 3", bio="Frontend visual designer.", skills="HTML, CSS, Figma", avatar_name="shivi")
            u2.set_password("password123")
            db.session.add_all([u1, u2])
            db.session.commit()

            g1 = Project(subject_code="TCP1201", title="Mini IT Project", description="Looking for a frontend designer!", tags="Flask, CSS", slots_open=2, user_id=u1.id)
            db.session.add(g1)
            
            e1 = Event(title="MMU Innovators Hackathon", organizer="FCI Club", date_time="June 12th @ 09:00 AM", venue="Dewan Canselor", description="A 48-hour challenge.", mmu_points=120, user_id=u1.id)
            db.session.add(e1)
            db.session.commit()

if __name__ == '__main__':
    add_sample_data()
    app.run(debug=True)