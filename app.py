    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        email_pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'

        if not username or not email or not password:
            flash('All fields are required.')
            return render_template('register.html')

        if not re.match(email_pattern, email):
            flash('Invalid email format.')
            return render_template('register.html')

        if not email.endswith(MMU_EMAIL_DOMAIN):
            flash('Please use your MMU student email (@student.mmu.edu.my).')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return render_template('register.html')

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
def create_group():
    new_group = Project(
        subject_code=request.form.get('subject_code'),
        title=request.form.get('title'),
        description=request.form.get('description'),
        tags=request.form.get('tags'),
        slots_open=int(request.form.get('slots_open', 1)),
        user_id=current_user.id
    )
    db.session.add(new_group)
    db.session.commit()
    flash('Group posted!')
    return redirect(url_for('index', tab='groups'))


@app.route('/create-event', methods=['POST'])
@login_required
def create_event():
    new_event = Event(
        title=request.form.get('title'),
        organizer=request.form.get('organizer'),
        date_time=request.form.get('date_time'),
        venue=request.form.get('venue'),
        description=request.form.get('description'),
        mmu_points=int(request.form.get('mmu_points', 50)),
        user_id=current_user.id
    )
    db.session.add(new_event)
    db.session.commit()
    flash('Event posted!')
    return redirect(url_for('index', tab='events'))


@app.route('/api/messages', methods=['GET', 'POST'])
@login_required
def handle_messages():
    if request.method == 'POST':
        data = request.json or {}
        receiver_username = data.get('receiver')
        text = (data.get('message') or '').strip()

        if not receiver_username or not text:
            return jsonify({"success": False, "error": "Missing receiver or message"}), 400

        receiver = User.query.filter_by(username=receiver_username).first()
        if not receiver:
            return jsonify({"success": False, "error": "Recipient not found"}), 404

        new_msg = Message(
            sender_username=current_user.username,
            receiver_username=receiver_username,
            text_content=text
        )
        db.session.add(new_msg)
        db.session.commit()

        # Notify the recipient via their MMU Outlook inbox -> triggers Outlook's
        # own notification (desktop/mobile/web) just like any other email.
        sent = send_new_message_email(
            to_email=receiver.email,
            sender_username=current_user.username,
            message_preview=text,
            app_url=APP_URL
        )
        new_msg.notified = sent
        db.session.commit()

        return jsonify({"success": True, "notified": sent})

    chat_partner = request.args.get('partner')
    chat_history = Message.query.filter(
        ((Message.sender_username == current_user.username) & (Message.receiver_username == chat_partner)) |
        ((Message.sender_username == chat_partner) & (Message.receiver_username == current_user.username))
    ).order_by(Message.time_sent.asc()).all()

    return jsonify([
        {"sender": m.sender_username, "message": m.text_content, "time": m.time_sent.strftime("%I:%M %p")}
        for m in chat_history
    ])


@app.route('/api/chatbot', methods=['POST'])
def chatbot_endpoint():
    user_msg = (request.json or {}).get('message', '').strip()
    if not user_msg:
        return jsonify({"reply": "Ask me anything about finding groups, events, or messaging teammates!"})
    reply = get_chatbot_reply(user_msg)
    return jsonify({"reply": reply})


def add_sample_data():
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            u1 = User(username="Divyyeash", email="divyyeash@student.mmu.edu.my", course="Computer Science",
                       semester="Trimester 2, Year 2", bio="Python backend coder.", skills="Python, Flask, SQL",
                       avatar_name="divy")
            u1.set_password("password123")
            u2 = User(username="Shivanie", email="shivanie@student.mmu.edu.my", course="Information Technology",
                       semester="Trimester 1, Year 3", bio="Frontend visual designer.", skills="HTML, CSS, Figma",
                       avatar_name="shivi")
            u2.set_password("password123")
            db.session.add_all([u1, u2])
            db.session.commit()

            g1 = Project(subject_code="TCP1201", title="Mini IT Project",
                         description="Looking for a frontend designer!", tags="Flask, CSS",
                         slots_open=2, user_id=u1.id)
            db.session.add(g1)

            e1 = Event(title="MMU Innovators Hackathon", organizer="FCI Club",
                      date_time="June 12th @ 09:00 AM", venue="Dewan Canselor",
                      description="A 48-hour challenge.", mmu_points=120, user_id=u1.id)
            db.session.add(e1)
            db.session.commit()


# Runs on import too (not just `python app.py`), so it also works under
# gunicorn/production servers that import `app` directly without __main__.
add_sample_data()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
