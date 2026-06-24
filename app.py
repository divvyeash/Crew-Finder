import os
import re
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
    search = request.args.get('search', '').strip() #Get the search query from the request query parameters-after the ? in url. If no search query is provided, default to an empty string. The .strip() method is used to remove any leading or trailing whitespace from the search query, ensuring that the search functionality works correctly even if the user accidentally adds extra spaces before or after their input.
    course_filter = request.args.get('course', '') #Get the course filter from the request query parameters-after the ? in url. If no course filter is provided, default to an empty string. This allows users to filter profiles based on their course of study.
    skill_filter = request.args.get('skill', '') #Get the skill filter from the request query parameters-after the ? in url. If no skill filter is provided, default to an empty string. This allows users to filter profiles based on their skills.
    current_tab = request.args.get('tab', 'groups') #Get the current tab from the request query parameters-after the ? in url. If no tab is specified, default to 'groups'. This allows the application to remember which tab the user was on when they performed a search or applied filters.

    group_query = Project.query   #Start looking at the Project table.
    if search:
        group_query = group_query.filter(Project.title.contains(search) | Project.subject_code.contains(search)) #Find groups where the title OR subject code contains the search word.
    groups = group_query.order_by(Project.date_posted.desc()).all() #Order the groups by the date they were posted, with the newest ones first, and get all of them.

    event_query = Event.query
    if search:
        event_query = event_query.filter(Event.title.contains(search) | Event.description.contains(search))
    events = event_query.order_by(Event.date_created.desc()).all()

    profile_query = User.query
    if course_filter:      #If the user has selected a course to filter by, narrow down the profiles to only those whose course contains the selected course. This allows for partial matches, so if someone selects "Computer Science", it will match profiles with "Computer Science", "Computer Science and IT", etc.
        profile_query = profile_query.filter(User.course.contains(course_filter)) #This line modifies the profile_query to only include users whose course field contains the text specified in course_filter. The .contains() method is used to allow for partial matches, so if course_filter is "Computer Science", it will match any user whose course includes "Computer Science" anywhere in the string (e.g., "Computer Science", "Computer Science and IT", "Applied Computer Science", etc.).
    if skill_filter:
        profile_query = profile_query.filter(User.skills.contains(skill_filter))
    if search:
        profile_query = profile_query.filter(User.username.contains(search) | User.skills.contains(search))
    profiles = profile_query.all()

    all_courses = sorted(list(set([u.course for u in User.query.all() if u.course and u.course != "Not specified yet"]))) #user.query.all() retrieves all user profiles from the database,u.course() extracts the course field from each profile, set() filters out any empty or default values,removes duplicates by converting to a set, sorted()sorts the unique courses alphabetically, and list()converts it back to a list. The resulting all_courses variable will contain a sorted list of unique courses that users have specified in their profiles, which can be used to populate the course filter dropdown in the UI.
    all_skills = sorted(list(set([s.strip() for u in User.query.all() if u.skills for s in u.skills.split(',') if u.skills != "None listed yet"]))) #This line retrieves all user profiles from the database, extracts the skills field from each profile, splits the skills by comma, strips any leading/trailing whitespace, filters out any empty values, removes duplicates by converting to a set, sorts the unique skills alphabetically, and converts it back to a list. The resulting all_skills variable will contain a sorted list of unique skills that users have specified in their profiles, which can be used to populate the skill filter dropdown in the UI.

    return render_template('index.html', 
                           groups=groups, events=events, profiles=profiles, 
                           all_courses=all_courses, all_skills=all_skills,
                           search_query=search, course_filter=course_filter, skill_filter=skill_filter,
                           current_tab=current_tab)

@app.route('/create-profile', methods=['GET', 'POST'])
@login_required
def create_profile():
    if request.method == 'POST': # If the user submits the form to create or update their profile, the following code will execute.
        current_user.course = request.form.get('course') # The request.form.get('course') retrieves the value of the 'course' field from the submitted form data. This value is then assigned to the current_user.course attribute, effectively updating the user's course information in the database.
        current_user.semester = request.form.get('semester')
        current_user.skills = request.form.get('skills')
        current_user.bio = request.form.get('bio')
        current_user.avatar_name = request.form.get('avatar_name', 'bottts')
        
        db.session.commit() # This line commits the changes made to the current_user object to the database. It saves the updated profile information (course, semester, skills, bio, and avatar_name) for the logged-in user. Without this commit, the changes would not be persisted in the database.
        return redirect(url_for('index', tab='profiles'))
        
    return render_template('create_profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        # Username does not exist
        if not user:
            flash('Username does not exist')
            return render_template('login.html')

        # Password check
        if not user.check_password(password):
            flash('Incorrect password')
            return render_template('login.html')

        login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Email format validation
        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not re.match(email_pattern, email):
            flash('Invalid email format.')
            return render_template('register.html')

        # MMU student email validation
        if not email.endswith('@student.mmu.edu.my'):
            flash('Please use your MMU student email.')
            return render_template('register.html')

        # Username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('register.html')

        # Email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.')
            return render_template('register.html')
        
        
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
def create_group():  # This function handles the creation of a new project group. It is triggered when a logged-in user submits the form to create a new group. The function retrieves the form data, creates a new Project instance with the provided information, adds it to the database session, commits the changes to save it in the database, and then redirects the user back to the index page with the 'groups' tab active.
    new_group = Project(  # This line creates a new instance of the Project class, which represents a project group in the database. The attributes of the new group are populated with data retrieved from the submitted form. The user_id is set to the current logged-in user's ID, linking the group to its creator.
        subject_code=request.form.get('subject_code'), title=request.form.get('title'), # The subject_code and title of the new group are retrieved from the form data submitted by the user. The request.form.get() method is used to access the values of the 'subject_code' and 'title' fields in the form.
        description=request.form.get('description'), tags=request.form.get('tags'),
        slots_open=int(request.form.get('slots_open')), user_id=current_user.id  # The description, tags, and slots_open attributes of the new group are also retrieved from the form data. The slots_open value is converted to an integer to ensure it is stored correctly in the database. The user_id is set to the ID of the currently logged-in user (current_user.id), establishing a relationship between the group and its creator.
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