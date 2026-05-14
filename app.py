from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Profile
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crewfinder.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'
db.init_app(app)

import view_edit


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/routes')
def routes():
    rules = []
    for rule in app.url_map.iter_rules():
        rules.append(f"{rule.methods} {rule.rule}")
    return '<br>'.join(sorted(rules))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Shivanie's frontend will send data here
        hashed_pw = generate_password_hash(request.form['password'])
        new_user = User(email=request.form['email'], password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        return "User Registered!"
    return render_template("register.html")

@app.route('/login')
def login():
    return render_template('login.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Creates the database tables
    app.run(debug=True)