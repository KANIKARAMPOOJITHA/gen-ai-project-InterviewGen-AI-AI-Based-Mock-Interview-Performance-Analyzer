import sqlite3
from datetime import datetime
import cv2
import numpy as np
import base64
from flask import jsonify
import os
import json
import uuid
import io
import requests
from flask import request, abort
from flask import Flask, render_template, request, send_file
from werkzeug.utils import secure_filename
from io import BytesIO
from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors

from evaluator import evaluate_answer
from ai_modules.answer_evaluator import evaluate_interview
from ai_modules.resume_intelligence import analyze_resume

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)


# ==================================================
# FLASK CONFIGURATION
# ==================================================

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(
    BASE_DIR,
    "uploads",
    "resumes"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
# ==================================================
# INTERVIEW HISTORY DATABASE
# ==================================================

# ==================================================
# INTERVIEW HISTORY DATABASE
# ==================================================

# ==================================================
# INTERVIEW HISTORY DATABASE
# ==================================================

DATABASE_PATH = os.path.join(BASE_DIR, "interviewgen.db")


def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS interview_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                interview_type TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                average_score REAL NOT NULL,
                total_questions INTEGER NOT NULL,
                results_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        columns = [
            row["name"]
            for row in connection.execute(
                "PRAGMA table_info(interview_history)"
            ).fetchall()
        ]

        if "reward_points" not in columns:
            connection.execute("""
                ALTER TABLE interview_history
                ADD COLUMN reward_points INTEGER NOT NULL DEFAULT 0
            """)

        connection.commit()

    finally:
        connection.close()


initialize_database()


def calculate_reward_points(score):
    if score >= 90:
        return 100
    elif score >= 75:
        return 80
    elif score >= 60:
        return 60
    elif score >= 40:
        return 40
    else:
        return 20
    # ==================================================
# DYNAMIC IMPROVEMENT PLAN
# ==================================================

def get_question_category(question):
    question = question.lower()

    categories = {
        "Python": ["python", "decorator", "generator", "list", "tuple"],
        "Java": ["java", "jvm", "jdk", "jre", "hashmap"],
        "SQL & Database": ["sql", "database", "query", "normalization", "nosql"],
        "Machine Learning": [
            "machine learning", "supervised", "unsupervised",
            "regression", "classification", "overfitting",
            "underfitting", "neural network", "gradient descent"
        ],
        "Web Development": [
            "html", "css", "javascript", "website",
            "frontend", "backend", "dom", "rest api"
        ],
        "Data Structures": [
            "array", "linked list", "stack", "queue",
            "tree", "graph", "sorting", "searching"
        ],
        "Software Engineering": [
            "software", "testing", "debugging", "deployment",
            "development life cycle", "microservices"
        ],
        "HR & Communication": [
            "tell me about yourself", "strengths", "weaknesses",
            "team", "leadership", "career goals", "motivation",
            "pressure", "failure", "feedback"
        ]
    }

    for category, keywords in categories.items():
        if any(keyword in question for keyword in keywords):
            return category

    return "General Interview Skills"


def generate_improvement_plan(interviews):

    category_scores = {}
    total_scores = []
    all_suggestions = []

    for interview in interviews:

        try:
            results = json.loads(interview["results_json"])

            if not isinstance(results, list):
                continue

        except (ValueError, TypeError):
            continue

        for result in results:

            if not isinstance(result, dict):
                continue

            question = result.get("question", "")
            score = safe_number(
                result.get("score", 0),
                default=0,
                minimum=0,
                maximum=100
            )

            category = get_question_category(question)
          if category not in category_scores:
                category_scores[category] = {
                    "total": 0,
                    "count": 0
                }

            category_scores[category]["total"] += score
            category_scores[category]["count"] += 1

            total_scores.append(score)

            suggestion = clean_text(
                result.get("suggestions", ""),
                300
            )

            if suggestion and suggestion not in all_suggestions:
                all_suggestions.append(suggestion)

    strengths = []
    areas_to_improve = []

    for category, data in category_scores.items():

        average = round(
            data["total"] / data["count"],
            1
        )

        category_info = {
            "name": category,
            "score": average
        }

        if average >= 70:
            strengths.append(category_info)

        elif average < 60:
            areas_to_improve.append(category_info)

    strengths.sort(key=lambda item: item["score"], reverse=True)
    areas_to_improve.sort(key=lambda item: item["score"])

    if not strengths and not areas_to_improve:
        if total_scores:
            strengths.append({
                "name": "Overall Interview Practice",
                "score": round(
                    sum(total_scores) / len(total_scores),
                    1
                )
            })

    recommendations = []

    for area in areas_to_improve[:3]:
        recommendations.append(
            f"Practise more questions in {area['name']}."
        )

    if all_suggestions:
        recommendations.extend(all_suggestions[:3])

    if not recommendations and total_scores:
        recommendations.append(
            "Continue practising mock interviews to improve your consistency."
        )

    if not total_scores:
        recommendations = [
            "Complete your first mock interview to receive personalised recommendations."
        ]

    if total_scores:
        weekly_goals = [
            "Practise 3 mock interviews this week.",
            "Solve 15 coding or technical questions.",
            "Review your incorrect answers and AI feedback."
        ]

        if areas_to_improve:
            weekly_goals.append(
                f"Spend extra time practising {areas_to_improve[0]['name']}."
            )
    else:
        weekly_goals = [
            "Complete your first mock interview.",
            "Practise 10 basic technical questions.",
            "Review your interview report and feedback."
        ]

    return {
        "strengths": strengths[:4],
        "areas_to_improve": areas_to_improve[:4],
        "recommendations": recommendations[:5],
        "weekly_goals": weekly_goals
    }

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx"}

MODEL_NAME = "qwen2.5:3b"

QUESTION_TIME_LIMIT = 120

# Ollama chatbot configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
CHAT_MODEL_NAME = "qwen2.5:3b"


# ==================================================
# INTERVIEW OPTIONS
# ==================================================

ROLES = [
    "Python Developer",
    "Software Engineer",
    "AI/ML Engineer",
    "Data Scientist",
    "Web Developer",
    "Java Developer"
]

INTERVIEW_TYPES = [
    "Technical",
    "HR",
    "Behavioral",
    "Mixed"
]

DIFFICULTIES = [
    "Beginner",
    "Intermediate",
    "Advanced"
]

QUESTION_COUNTS = {
    "Beginner": 10,
    "Intermediate": 15,
    "Advanced": 20
}


# ==================================================
# TECHNICAL QUESTION BANK
# ==================================================

QUESTION_BANK = {

    "Python Developer": [
        "What is Python and what are its main features?",
        "What is the difference between a list and a tuple?",
        "Explain Python variables and data types.",
        "What is the purpose of indentation in Python?",
        "What is the difference between == and is?",
        "What are Python dictionaries?",
        "Explain list comprehensions with an example.",
        "What is exception handling in Python?",
        "What are decorators in Python?",
        "Explain generators and iterators.",
        "What is the difference between shallow copy and deep copy?",
        "Explain object-oriented programming in Python.",
        "What is the Global Interpreter Lock?",
        "How does Python manage memory?",
        "Explain multithreading and multiprocessing.",
        "What is asynchronous programming?",
        "How would you optimize a slow Python application?",
        "Explain Python modules and packages.",
        "What are lambda functions?",
        "How do you test a Python application?"
    ],

    "Software Engineer": [
        "What is software engineering?",
        "Explain the software development life cycle.",
        "What is the difference between frontend and backend?",
        "What is object-oriented programming?",
        "What is the difference between a compiler and interpreter?",
        "Explain the four principles of OOP.",
        "What is the difference between an array and linked list?",
        "Explain stack and queue data structures.",
        "What is database normalization?",
        "What are REST APIs?",
        "Explain the SOLID principles.",
        "What is a design pattern?",
        "Explain microservices architecture.",
        "How do you identify performance bottlenecks?",
        "What is version control?",
        "Explain unit testing and integration testing.",
        "How would you design a scalable application?",
        "What is the difference between SQL and NoSQL?",
        "Explain software deployment.",
        "How do you debug a complex software issue?"
    ],

    "AI/ML Engineer": [
        "What is artificial intelligence?",
        "What is machine learning?",
        "Explain supervised and unsupervised learning.",
        "What is the difference between classification and regression?",
        "What is a training dataset?",
        "Explain overfitting and underfitting.",
        "What is the bias-variance trade-off?",
        "How does a decision tree work?",
        "What is cross-validation?",
        "Explain precision and recall.",
        "What is gradient descent?",
        "How does a neural network learn?",
        "Explain the vanishing gradient problem.",
        "How would you handle an imbalanced dataset?",
        "What is a confusion matrix?",
        "Explain feature engineering.",
        "What is regularization in machine learning?",
        "Explain ensemble learning.",
        "What is the purpose of an activation function?",
        "Explain the transformer architecture."
    ],

    "Data Scientist": [
        "What is data science?",
        "What is the difference between data and information?",
        "What is data preprocessing?",
        "Explain mean, median and mode.",
        "What is data visualization?",
        "How do you handle missing values?",
        "Explain correlation and covariance.",
        "What is feature engineering?",
        "What is hypothesis testing?",
        "Explain SQL and NoSQL databases.",
        "What is principal component analysis?",
        "How would you build a predictive model?",
        "Explain ensemble learning techniques.",
        "What is data leakage?",
        "How do you evaluate an imbalanced dataset?",
        "Explain statistical significance.",
        "What is exploratory data analysis?",
        "What is the difference between a population and a sample?",
        "How do you detect outliers?",
        "Explain model evaluation metrics."
    ],

    "Web Developer": [
        "What is HTML?",
        "What is the difference between HTML and CSS?",
        "What is JavaScript?",
        "What is the difference between id and class?",
        "What is responsive web design?",
        "Explain let, const and var.",
        "What is the Document Object Model?",
        "Explain synchronous and asynchronous JavaScript.",
        "What are JavaScript promises?",
        "How do REST APIs work?",
        "What is the virtual DOM?",
        "How would you optimize website performance?",
        "Explain authentication and authorization.",
        "What is cross-site scripting?",
        "What is responsive design?",
        "Explain CSS Flexbox and Grid.",
        "What is event bubbling?",
        "How does browser rendering work?",
        "What is a web server?",
        "How would you design a scalable website?"
    ],

    "Java Developer": [
        "What is Java?",
        "What are the main features of Java?",
        "Explain JDK, JRE and JVM.",
        "What is a class and an object?",
        "What is the difference between == and equals()?",
        "Explain inheritance and polymorphism.",
        "What is an interface?",
        "What is an abstract class?",
        "Explain exception handling in Java.",
        "What is the Java Collections Framework?",
        "Explain Java memory management.",
        "How does garbage collection work?",
        "Explain the internal working of HashMap.",
        "What is the difference between synchronized and volatile?",
        "Explain the Java Stream API.",
        "What is multithreading?",
        "What are constructors in Java?",
        "Explain method overloading and overriding.",
        "What is encapsulation?",
        "How does Java achieve platform independence?"
    ]
}


# ==================================================
# HR QUESTION BANK
# ==================================================

HR_QUESTIONS = [
    "Tell me about yourself.",
    "Why should we hire you?",
    "What are your strengths and weaknesses?",
    "Where do you see yourself in five years?",
  "Why do you want to work for our company?",
    "How do you handle pressure and deadlines?",
    "Describe your ideal work environment.",
    "What motivates you to perform well?",
    "How do you manage multiple responsibilities?",
    "What are your career goals?",
    "How do you respond to constructive feedback?",
    "What makes you a good team member?",
    "How would you handle a disagreement with your manager?",
    "Why did you choose this career?",
    "What do you expect from your first job?",
    "How do you adapt to new environments?",
    "What is your biggest professional achievement?",
    "How do you handle failure?",
    "Are you comfortable learning new technologies?",
    "Do you have any questions for the interviewer?"
]


# ==================================================
# BEHAVIORAL QUESTION BANK
# ==================================================

BEHAVIORAL_QUESTIONS = [
    "Describe a challenging situation you faced and how you handled it.",
    "Tell me about a time you worked successfully in a team.",
    "Describe a mistake you made and what you learned.",
    "How do you handle disagreements with teammates?",
    "Tell me about a time you showed leadership.",
    "Describe a time when you had to learn something quickly.",
    "Tell me about a time you solved a difficult problem.",
    "Describe a situation where you worked under pressure.",
    "Tell me about a time you received critical feedback.",
    "Describe a project where you took responsibility.",
    "Tell me about a time you helped another person.",
    "Describe a situation where you had to adapt to change.",
    "How did you handle a missed deadline?",
    "Tell me about a time you made an important decision.",
    "Describe a situation where you showed initiative.",
    "Tell me about a time you had conflicting priorities.",
    "Describe a time you resolved a team conflict.",
    "Tell me about a time you achieved a difficult goal.",
    "How do you respond when a plan does not work?",
    "Describe a time you went beyond your responsibilities."
]


# ==================================================
# QUESTION GENERATION
# FAST QUESTION LOADING - NO OLLAMA WAITING
# ==================================================

def get_question_count(difficulty):
    return QUESTION_COUNTS.get(difficulty, 10)


def get_fallback_questions(role, interview_type, difficulty):

    count = get_question_count(difficulty)

    technical = QUESTION_BANK.get(
        role,
        QUESTION_BANK["Software Engineer"]
    )

    if interview_type == "Technical":
        source = technical

    elif interview_type == "HR":
        source = HR_QUESTIONS

    elif interview_type == "Behavioral":
        source = BEHAVIORAL_QUESTIONS

    else:
        source = []

        for index in range(count):

            if index % 3 == 0:
                source.append(
                    technical[index % len(technical)]
                )

            elif index % 3 == 1:
                source.append(
                    HR_QUESTIONS[index % len(HR_QUESTIONS)]
                )

            else:
                source.append(
                    BEHAVIORAL_QUESTIONS[
                        index % len(BEHAVIORAL_QUESTIONS)
                    ]
                )

        return source[:count]

    return source[:count]


def generate_ai_questions(role, interview_type, difficulty):
    """
    Questions are loaded from the local question bank.
    Ollama is not called during interview startup.
    """

    questions = get_fallback_questions(
        role,
        interview_type,
        difficulty
    )

    print(
        f"Loaded {len(questions)} questions "
        f"for {role} - {interview_type} - {difficulty}"
    )

    return questions, "Question Bank"


# ==================================================
# COMMON HELPERS
# ==================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def clean_text(value, max_length=5000):

    if not isinstance(value, str):
        return ""

    return value.strip()[:max_length]


def safe_number(value, default=0, minimum=0, maximum=100000):

    try:
        number = float(value)

        if not (number >= minimum and number <= maximum):
            return default

        return number

    except (ValueError, TypeError):
        return default


def build_report_payload(
    results,
    average_score,
    role,
    interview_type,
    difficulty
):

    return {
        "results": results,
        "average_score": average_score,
        "role": role,
        "interview_type": interview_type,
        "difficulty": difficulty,
        "model_name": MODEL_NAME
    }


# ==================================================
# HOME PAGE
# ==================================================

@app.route("/")
def home():
    return dashboard()

# ==================================================
# DASHBOARD
# ==================================================

# ==================================================
# DASHBOARD
# ==================================================

@app.route("/dashboard")
def dashboard():

    connection = get_db_connection()

    try:

        total_interviews = connection.execute("""
            SELECT COUNT(*) AS total
            FROM interview_history
        """).fetchone()["total"]

        total_points = connection.execute("""
            SELECT COALESCE(SUM(reward_points), 0) AS points
            FROM interview_history
        """).fetchone()["points"]

        interviews = connection.execute("""
            SELECT *
            FROM interview_history
            ORDER BY id DESC
        """).fetchall()

        total_certificates = total_interviews

    finally:
        connection.close()

    # Generate improvement plan from actual interview results
    improvement_plan = generate_improvement_plan(interviews)

    return render_template(
        "dashboard.html",
        total_interviews=total_interviews,
        total_points=total_points,
        total_certificates=total_certificates,
        improvement_plan=improvement_plan
    )
# ==================================================
# ANALYTICS DASHBOARD
# ==================================================

@app.route("/analytics")
def analytics():

    connection = get_db_connection()

    try:
        interviews = connection.execute("""
            SELECT *
            FROM interview_history
            ORDER BY id DESC
        """).fetchall()

    finally:
        connection.close()

    total_interviews = len(interviews)

    average_score = (
        round(
            sum(item["average_score"] for item in interviews)
            / total_interviews,
            1
        )
        if total_interviews else 0
    )

    total_questions = sum(
        item["total_questions"] for item in interviews
    )

    recent_interviews = []

    for item in interviews[:10]:
        recent_interviews.append({
            "id": item["id"],
            "role": item["role"],
            "interview_type": item["interview_type"],
            "difficulty": item["difficulty"],
            "average_score": item["average_score"],
            "total_questions": item["total_questions"],
            "created_at": item["created_at"]
        })

    score_history = [
        {
            "date": item["created_at"],
            "score": item["average_score"]
        }
        for item in reversed(interviews)
    ]

    return render_template(
        "analytics.html",
        total_interviews=total_interviews,
        average_score=average_score,
        total_questions=total_questions,
        recent_interviews=recent_interviews,
        score_history=score_history
    )

# ==================================================
# CERTIFICATES AND GRADE POINTS
# ==================================================

@app.route("/certificates")
def certificates():

    connection = get_db_connection()

    try:
        interviews = connection.execute("""
            SELECT *
            FROM interview_history
            ORDER BY id DESC
        """).fetchall()

        total_points = connection.execute("""
            SELECT COALESCE(SUM(reward_points), 0) AS points
            FROM interview_history
        """).fetchone()["points"]

    finally:
        connection.close()

    total_certificates = len(interviews)

    return render_template(
        "certificates.html",
        interviews=interviews,
        total_points=total_points,
        total_certificates=total_certificates
    )
# ==================================================
# DOWNLOAD INTERVIEW CERTIFICATE
# ==================================================

@app.route("/download-certificate/<int:interview_id>", methods=["POST"])
def download_certificate(interview_id):

    # Get the student's name from the form
    student_name = request.form.get("student_name", "").strip()

    if not student_name:
        return "Please enter your name before downloading the certificate.", 400

    if len(student_name) > 100:
        return "Student name is too long.", 400

    # Fetch the selected completed interview
    connection = get_db_connection()

    try:
        interview = connection.execute("""
            SELECT *
            FROM interview_history
            WHERE id = ?
        """, (interview_id,)).fetchone()

    finally:
        connection.close()

    if interview is None:
        abort(404, description="Interview record not found.")

    # Read interview details
    role = interview["role"]
    interview_type = interview["interview_type"]
    difficulty = interview["difficulty"]
    score = float(interview["average_score"])
    points = interview["reward_points"]
    interview_date = interview["created_at"]

    # Determine performance level
    if score >= 90:
        performance_level = "Outstanding Performance"
    elif score >= 75:
        performance_level = "Excellence"
    elif score >= 60:
        performance_level = "Good Performance"
    else:
        performance_level = "Participation"

    # Create the PDF in memory
    pdf_buffer = BytesIO()

    page_size = landscape(A4)
    pdf = canvas.Canvas(pdf_buffer, pagesize=page_size)

    page_width, page_height = page_size

    # Background
    pdf.setFillColor(colors.white)
    pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

    # Outer certificate border
    pdf.setStrokeColor(colors.HexColor("#172554"))
    pdf.setLineWidth(5)
    pdf.rect(25, 25, page_width - 50, page_height - 50)

    # Inner gold border
    pdf.setStrokeColor(colors.HexColor("#D4AF37"))
    pdf.setLineWidth(2)
    pdf.rect(36, 36, page_width - 72, page_height - 72)

    # Organization name
    pdf.setFillColor(colors.HexColor("#6D28D9"))
    pdf.setFont("Helvetica-Bold", 25)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 90,
        "INTERVIEWGEN AI"
    )

    # Certificate heading
    pdf.setFillColor(colors.HexColor("#172554"))
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 140,
        "CERTIFICATE OF ACHIEVEMENT"
    )

    # Subtitle
    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 170,
        "This certificate is proudly presented to"
    )

    # Student name
    pdf.setFillColor(colors.HexColor("#6D28D9"))
    pdf.setFont("Helvetica-Bold", 27)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 220,
        student_name
    )

    # Description
    pdf.setFillColor(colors.HexColor("#334155"))
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 255,
        "For successfully completing a mock interview on InterviewGen AI."
    )

    # Performance level
    pdf.setFillColor(colors.HexColor("#172554"))
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(
        page_width / 2,
        page_height - 300,
        performance_level
    )

    # Interview details
    pdf.setFillColor(colors.HexColor("#334155"))
    pdf.setFont("Helvetica", 12)

    details = [
        f"Role: {role}",
        f"Interview Type: {interview_type}",
        f"Difficulty: {difficulty}",
        f"Final Score: {score:.1f}%",
        f"Grade Points Earned: {points}",
        f"Completion Date: {interview_date}"
    ]

    y_position = page_height - 340

    for detail in details:
        pdf.drawCentredString(
            page_width / 2,
            y_position,
            detail
        )
        y_position -= 19

    # Unique certificate ID
    certificate_id = f"IGA-{interview_id}-{uuid.uuid4().hex[:8].upper()}"

    pdf.setFillColor(colors.HexColor("#64748B"))
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        page_width / 2,
        75,
        f"Certificate ID: {certificate_id}"
    )

    pdf.drawCentredString(
        page_width / 2,
        58,
        "Generated by InterviewGen AI"
    )

    # Finish PDF
    pdf.save()
    pdf_buffer.seek(0)

    # Download the certificate
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"InterviewGenAI_Certificate_{interview_id}.pdf"
  messages.append({

                    "role": role,

                    "content": content[:3000]

                })

        # Add the current user message.
        messages.append({

            "role": "user",

            "content": message

        })

        payload = {

            "model": CHAT_MODEL_NAME,

            "messages": messages,

            "stream": False,

            "options": {

                "temperature": 0.7

            }

        }

        response = requests.post(

            OLLAMA_URL,

            json=payload,

            timeout=180

        )

        response.raise_for_status()

        result = response.json()

        reply = result.get(
            "message", {}
        ).get(
            "content", ""
        )

        if not reply:

            reply = (
                "I couldn't generate a response. "
                "Please try asking your question again."
            )

        return {

            "reply": reply.strip()

        }

    except requests.exceptions.ConnectionError:

        print("CHATBOT ERROR: Ollama is not running.")

        return {

            "reply": (
                "I cannot connect to Ollama right now. "
                "Please make sure Ollama is running on your computer."
            )

        }, 503

    except requests.exceptions.Timeout:

        print("CHATBOT ERROR: Ollama request timed out.")

        return {

            "reply": (
                "The AI is taking too long to respond. "
                "Please try again with a shorter question."
            )

        }, 504

    except requests.exceptions.RequestException as error:

        print("CHATBOT REQUEST ERROR:", error)

        return {

            "reply": (
                "There was a problem communicating with the AI model. "
                "Please try again."
            )

        }, 500

    except Exception as error:

        print("CHATBOT ERROR:", error)

        return {

            "reply": "Something went wrong. Please try again."

        }, 500


# ==================================================
# FILE SIZE ERROR
# ==================================================

@app.errorhandler(413)
def file_too_large(error):

    return render_template(
        "resume_analysis.html",
        error="File is too large. Please upload a file below 5 MB."
    ), 413


# ==================================================
# PAGE NOT FOUND
# ==================================================

@app.errorhandler(404)
def page_not_found(error):

    return "Page not found. Please check the URL.", 404


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )
