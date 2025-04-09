from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'lecturer' or 'student'
    questions = db.relationship('Question', backref='author', lazy=True)
    answers = db.relationship('Answer', backref='author', lazy=True)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'video' or 'document'
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lecturer = db.relationship('User', backref='uploads')

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        role = request.form.get('role')

        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))

        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            role=role
        )
        db.session.add(user)
        db.session.commit()
        flash('Registration successful')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'lecturer':
        contents = Content.query.filter_by(lecturer_id=current_user.id).all()
        questions = Question.query.all()
    else:
        contents = Content.query.all()
        questions = Question.query.filter_by(student_id=current_user.id).all()
    return render_template('dashboard.html', contents=contents, questions=questions)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if current_user.role != 'lecturer':
        flash('Only lecturers can upload content')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        content_type = request.form.get('content_type')
        file = request.files['file']

        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], content_type + 's', filename))
            
            content = Content(
                title=title,
                description=description,
                filename=filename,
                content_type=content_type,
                lecturer_id=current_user.id
            )
            db.session.add(content)
            db.session.commit()
            flash('Content uploaded successfully')
            return redirect(url_for('dashboard'))

    return render_template('upload.html')

@app.route('/ask_question', methods=['GET', 'POST'])
@login_required
def ask_question():
    if current_user.role != 'student':
        flash('Only students can ask questions')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        
        question = Question(
            title=title,
            content=content,
            student_id=current_user.id
        )
        db.session.add(question)
        db.session.commit()
        flash('Question posted successfully')
        return redirect(url_for('dashboard'))

    return render_template('ask_question.html')

@app.route('/answer_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def answer_question(question_id):
    if current_user.role != 'lecturer':
        flash('Only lecturers can answer questions')
        return redirect(url_for('dashboard'))

    question = Question.query.get_or_404(question_id)

    if request.method == 'POST':
        content = request.form.get('content')
        
        answer = Answer(
            content=content,
            question_id=question_id,
            lecturer_id=current_user.id
        )
        db.session.add(answer)
        db.session.commit()
        flash('Answer posted successfully')
        return redirect(url_for('dashboard'))

    return render_template('answer_question.html', question=question)

@app.route('/uploads/<content_type>/<filename>')
@login_required
def uploaded_file(content_type, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], content_type + 's'), filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=False) 
