import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Project, Event

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

# --- ROUTER VIEW LOGIC ---

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    faculty_filter = request.args.get('faculty', '')
    active_tab = request.args.get('tab', 'crews') # Tab router context toggle

    # 1. Gather Projects (Crews)
    p_query = Project.query
    if search_query:
        p_query = p_query.filter((Project.title.contains(search_query)) | (Project.subject_code.contains(search_query)))
    if faculty_filter:
        p_query = p_query.filter(Project.tags.contains(faculty_filter.upper()))
    projects = p_query.order_by(Project.date_posted.desc()).all()

    # 2. Gather Events
    e_query = Event.query
    if search_query:
        e_query = e_query.filter((Event.title.contains(search_query)) | (Event.description.contains(search_query)))
    events = e_query.order_by(Event.date_created.desc()).all()

    # 3. Gather Portfolios
    u_query = User.query
    if search_query:
        u_query = u_query.filter((User.username.contains(search_query)) | (User.skills.contains(search_query)))
    users = u_query.all()

    return render_template('index.html', 
                           projects=projects, 
                           events=events, 
                           users=users, 
                           search_query=search_query, 
                           faculty_filter=faculty_filter,
                           active_tab=active_tab)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        course = request.form.get('course')
        semester = request.form.get('semester')
        bio = request.form.get('bio')
        skills = request.form.get('skills')

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Account with credentials already exists!', 'error')
            return redirect(url_for('register'))

        new_user = User(
            username=username, email=email, course=course,
            semester=semester, bio=bio, skills=skills,
            avatar_seed=username.lower()
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Portfolio and account created successfully!', 'success')
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
        
        flash('Invalid username or password configuration.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/create-project', methods=['POST'])
@login_required
def create_project():
    new_project = Project(
        subject_code=request.form.get('subject_code'),
        title=request.form.get('title'),
        description=request.form.get('description'),
        tags=request.form.get('tags'),
        slots_open=int(request.form.get('slots_open')),
        user_id=current_user.id
    )
    db.session.add(new_project)
    db.session.commit()
    return redirect(url_for('index', tab='crews'))

@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    new_event = Event(
        title=request.form.get('title'),
        organizer=request.form.get('organizer'),
        date_time=request.form.get('date_time'),
        venue=request.form.get('venue'),
        description=request.form.get('description'),
        reward_points=int(request.form.get('reward_points', 50)),
        user_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    return redirect(url_for('index', tab='events'))

# --- AI CHATBOT SYSTEM ---
@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '').lower()
    if 'hello' in user_message or 'hi' in user_message:
        reply = "Hello! I'm your CrewFinder Agent. Ready to build a portfolio, track events, or source project partners?"
    elif 'fci' in user_message or 'flask' in user_message:
        reply = "FCI groups are dominating current boards. Check out standard TCP1201 Web App listings!"
    elif 'event' in user_message or 'hackathon' in user_message:
        reply = "Toggle over to our new 'Events Hub' tab to sign up for hackathons and score structural MMU activity metrics."
    else:
        reply = "Explore the dashboard tabs to seamlessly jump between project squads, upcoming campus events, or student portfolios."
    return jsonify({"reply": reply})

# --- SEED LIFECYCLE CONTROLLER ---
def seed_database():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            # 1. Build Diverse Structural Portfolios
            u1 = User(username="Divyyeash", email="divyyeash.k@student.mmu.edu.my", course="Bachelor of Computer Science (Data Science)", semester="Trimester 2, Year 2", bio="Python backend script engineer. Passionate about machine learning processing loops, architectural design, and SQLite operations hooks.", skills="Python,Flask,SQL,Pandas", avatar_seed="divy")
            u1.set_password("password123")

            u2 = User(username="Shivanie", email="shivanie.k@student.mmu.edu.my", course="Bachelor of Information Technology (Security)", semester="Trimester 1, Year 3", bio="UI/UX Specialist and absolute CSS ninja. Love crafting responsive glassmorphism workspaces and accessibility clean UI schemas.", skills="Figma,CSS,JavaScript,Vue", avatar_seed="shivi")
            u2.set_password("password123")

            u3 = User(username="Ransly", email="ransly.m@student.mmu.edu.my", course="Bachelor of Business Administration (FOM)", semester="Trimester 3, Year 1", bio="Product manager and market layout engineer. Can handle business reporting decks, documentation setups, and agile workflow sprint planning.", skills="Agile,Scrum,Documentation,Pitching", avatar_seed="rans")
            u3.set_password("password123")

            db.session.add_all([u1, u2, u3])
            db.session.commit()

            # 2. Add Project Listings
            p1 = Project(subject_code="TCP1201", title="Mini IT Project (Web App Hub)", description="Building a peer-to-peer student matching dynamic dashboard via Flask framework. Seeking full-stack interface specialist for layout components optimization.", tags="Flask,CSS,FCI", slots_open=2, user_id=u1.id)
            p2 = Project(subject_code="PRG2111", title="Java Inventory Automation Suite", description="Constructing multi-threaded warehouse tracking platform. Need back-end validation layers built out cleanly.", tags="Java,OOP,FCI", slots_open=1, user_id=u2.id)
            p3 = Project(subject_code="MKT1021", title="Digital Marketing Transformation Sprint", description="Assembling consumer acquisition map models for local business scaling options. Need designers for structural collateral setups.", tags="Marketing,Strategy,FOM", slots_open=3, user_id=u3.id)
            
            db.session.add_all([p1, p2, p3])

            # 3. Add Event Records
            e1 = Event(title="MMU Grand Innovators Hackathon 2026", organizer="FCI Faculty Board", date_time="June 12th @ 09:00 AM", venue="Dewan Canselor, Cyberjaya", description="48-hour continuous product engineering challenge. Teams will build production applications addressing localized environment concerns. Great portfolio booster!", reward_points=120, user_id=u1.id)
            e2 = Event(title="UI/UX Interactive Masterclass Workshop", organizer="CrewFinder Elite Guild", date_time="June 18th @ 02:00 PM", venue="FCI SMART Lab 3012", description="Deep dive technical acceleration training on modern CSS grids, tailwind components integration, and custom framework component builds.", reward_points=40, user_id=u2.id)
            
            db.session.add_all([e1, e2])
            db.session.commit()

if __name__ == '__main__':
    seed_database()
    app.run(debug=True)