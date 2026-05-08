from flask import render_template, request, url_for, redirect
from models import db, User, Profile
from app import app


@app.route('/create_profile', methods=['POST'])
def create_profile():
    user = User.query.first() #gets current user from database
    if not user:
        return redirect(url_for('register'))

    new_profile = Profile(
        name=request.form['name'],
        course=request.form['course'],
        email=request.form['email'],
        bio=request.form['bio'],
        user_id=user.id
    )

    db.session.add(new_profile)
    db.session.commit()

    return redirect(url_for('profile')) #after saving profile, redirects to profile page

@app.route('/profile')
def profile():
    user = User.query.first() #gets current user from database
    if not user:
        return redirect(url_for('register'))

    profile = Profile.query.filter_by(user_id=user.id).first() #searches the database for the profile connected to the current user ID

    if profile:
        form_action = "/update_profile"
    else:
        form_action = "/create_profile"

    return render_template(     #sends profile data n form action variables into html template
        "profile.html",
        user=user,
        profile=profile,   #allows values to appear on form
        form_action=form_action
    )

@app.route('/update_profile', methods=['POST'])
def update_profile():
    user = User.query.first()
    if not user:
        return redirect(url_for('register'))

    profile = Profile.query.filter_by(user_id=user.id).first()  #gets current user's profile from database

    profile.name = request.form['name']      #replace current profile values with new values from form
    profile.course = request.form['course']
    profile.email = request.form['email']
    profile.bio = request.form['bio']

    db.session.commit()

    return redirect(url_for('profile'))