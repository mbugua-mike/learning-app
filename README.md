# Educational Platform

A Flask-based educational platform that allows lecturers and students to interact through video uploads, document sharing, and Q&A.

## Features

- User authentication (Lecturer and Student roles)
- Video upload and viewing
- Document upload and viewing
- Q&A system between students and lecturers

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

4. Initialize the database:
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application:
```bash
flask run
```

## Usage

1. Register as either a lecturer or student
2. Log in to access the platform
3. Lecturers can:
   - Upload videos and documents
   - Answer student questions
4. Students can:
   - View uploaded videos and documents
   - Ask questions to lecturers 