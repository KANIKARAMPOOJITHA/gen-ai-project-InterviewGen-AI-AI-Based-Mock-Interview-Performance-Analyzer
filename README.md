# InterviewGen AI – AI-Based Mock Interview & Performance Analyzer

An AI-powered web application designed to help students and job seekers prepare for technical, HR, and behavioral interviews. It provides interactive mock interviews, AI-based answer evaluation, resume analysis, voice-based interaction, and personalised performance reports.

## 🌐 Live Demo

**Try InterviewGen AI here:**

🔗 [InterviewGen AI – Live Website](https://interviewgen-ai-rtnk.onrender.com)

---

## 🌟 Key Features

### 1. Interactive Mock Interview System
- **Multiple Job Roles:** Python Developer, Software Engineer, AI/ML Engineer, Data Scientist, Web Developer, and Java Developer.
- **Interview Types:** Technical, HR, Behavioral, and Mixed interviews.
- **Difficulty Levels:** Beginner, Intermediate, and Advanced.
- **Question Bank:** Role-based questions selected according to the interview type and difficulty level.
- **Time Management:** Provides a time limit for answering interview questions.
- **Voice-Based Interaction:** Supports voice-based question readout and spoken answers.
- **Advanced Interview Modes:** Supports live video interviews and text-based interviews.

### 2. AI-Based Answer Evaluation
- **LLM Integration:** Uses the GPT-OSS-120B model through the Groq API.
- **Automated Evaluation:** Analyses candidate answers based on relevance, technical accuracy, completeness, and communication.
- **Performance Scoring:** Provides scores for different evaluation criteria.
- **Strengths Identification:** Highlights the strong points in candidate answers.
- **Weakness Detection:** Identifies areas that need improvement.
- **AI Feedback:** Provides suggestions to improve interview performance.

### 3. Resume Analysis
- Supports PDF and DOCX resume uploads.
- Extracts text from uploaded resumes.
- Analyses resume content and relevant skills.
- Helps candidates understand their resume-related strengths and improvement areas.

### 4. Voice and Video Interview Features
- **Speech Recognition:** Converts spoken answers into text.
- **Text-to-Speech:** Reads interview questions aloud.
- **Webcam Integration:** Supports live video interview interaction.
- **Face Detection:** Uses OpenCV for webcam-based face detection.

### 5. Performance Analyzer Dashboard
- Displays interview scores and evaluation results.
- Tracks previous interview performance.
- Provides performance analytics and progress information.
- Highlights strengths and weaknesses.
- Offers personalised improvement suggestions.

### 6. AI Chatbot and Voice Practice
- Provides an AI chatbot for interview preparation.
- Supports additional interview practice.
- Helps candidates improve their interview readiness.

### 7. Certificate Generation and Rewards
- Generates interview performance certificates.
- Provides reward points for interview practice.
- Offers improvement plans based on performance.

---

## 🛠️ Technology Stack

### Frontend
- **HTML5** – Website structure.
- **CSS3** – Styling and responsive design.
- **JavaScript** – Interactive functionality and browser-based features.

### Backend
- **Python** – Main backend programming language.
- **Flask** – Web application framework.

### Database
- **SQLite** – Stores user information, interview history, scores, and related records.

### AI and Machine Learning Technologies
- **Groq API** – Connects the application with the language model.
- **GPT-OSS-120B** – Large Language Model used for answer evaluation and AI-generated feedback.
- **NLP Techniques** – Used for processing and analysing text responses.
- **OpenCV** – Used for webcam-based face detection.
- **Web Speech API** – Supports speech recognition and text-to-speech functionality.

### Supporting Libraries
- **PyPDF** – Extracts text from PDF resumes.
- **python-docx** – Extracts text from DOCX resumes.
- **ReportLab** – Generates PDF certificates.
- **NumPy** – Supports numerical operations.
- **python-dotenv** – Manages environment variables.

### Development and Deployment Tools
- **Visual Studio Code** – Development environment.
- **Git** – Version control.
- **GitHub** – Source code repository.
- **Gunicorn** – WSGI application server.
- **Render** – Cloud deployment and hosting platform.

---

## 🏗️ System Architecture

1. **User Interface:** Candidates interact with the application through the frontend.
2. **Interview Configuration:** Candidates select their job role, interview type, and difficulty level.
3. **Question Selection:** The system selects relevant questions from the question bank.
4. **Answer Submission:** Candidates submit answers through text or voice interaction.
5. **AI Evaluation:** The Groq API with GPT-OSS-120B evaluates candidate responses.
6. **Performance Analysis:** The system generates scores, strengths, weaknesses, and improvement suggestions.
7. **Report Generation:** Interview results are stored and presented through the dashboard.

---

## 📂 Project Structure

```text
InterviewGen-AI/
│
├── app.py
├── evaluator.py
├── requirements.txt
├── .env
├── .gitignore
│
├── ai_modules/
│   └── answer_evaluator.py
│
├── templates/
│   ├── index.html
│   └── other HTML templates
│
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   └── other static files
│
└── README.md
```

*Note: Update the structure above if your actual project contains additional files or folders.*

---

## 🚀 How to Run the Project Locally

### Prerequisites
- Python 3.10 or later (compatible with your installed dependencies).
- Visual Studio Code.
- Git.
- Groq API key.

### Step 1: Clone the Repository

```bash
git clone https://github.com/ChSivamowny15/InterviewGen-AI.git
```

### Step 2: Navigate to the Project Directory

```bash
cd InterviewGen-AI
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Configure the API Key

Create a `.env` file in the project root directory and add:

```env
GROQ_API_KEY=your_groq_api_key
```

Replace `your_groq_api_key` with your actual Groq API key.

**Important:** Never upload your `.env` file or API key to GitHub.

### Step 7: Run the Application

```bash
python app.py
```

### Step 8: Open the Website

Visit:

[http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## ☁️ Deployment

The InterviewGen AI application is deployed on **Render** using GitHub integration.

### Deployment Tools

| Tool | Purpose |
|---|---|
| GitHub | Source code management and repository integration |
| Render | Cloud hosting and deployment |
| Gunicorn | Runs the Flask application in the production environment |

### Deployment Configuration

**Build Command:**

```bash
pip install -r requirements.txt
```

**Start Command:**

```bash
gunicorn app:app
```

**Live Application:**

[https://interviewgen-ai-rtnk.onrender.com](https://interviewgen-ai-rtnk.onrender.com)

---

## 🔮 Future Enhancements

- **Retrieval-Augmented Generation (RAG):** Integrate a retrieval system to retrieve relevant resume information and technical knowledge for personalised interview questions and context-aware feedback.
- **Advanced Resume Intelligence:** Improve skill extraction and resume-based question generation.
- **Adaptive Interviews:** Dynamically adjust question difficulty based on candidate performance.
- **Detailed Speech Analytics:** Enhance speaking pace, filler-word detection, and communication analysis.
- **Advanced Performance Analytics:** Provide deeper insights into candidate progress and interview readiness.

---

## 🎯 Project Objective

The main objective of InterviewGen AI is to provide an intelligent and interactive interview preparation platform that helps candidates practise interviews, evaluate their answers, identify weaknesses, and continuously improve their technical knowledge and communication skills.

---

## 👩‍💻 Developed By

**InterviewGen AI – AI-Based Mock Interview & Performance Analyzer**

Developed as an academic project by the Computer Science and Engineering – Artificial Intelligence and Machine Learning team.

