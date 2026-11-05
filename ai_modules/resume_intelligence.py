import os
import re

from pypdf import PdfReader
from docx import Document


# ==================================================
# 1. SKILLS DATABASE
# ==================================================

SKILLS_LIST = [
    "Python", "Java", "C", "C++", "JavaScript",
    "HTML", "CSS", "React", "Flask", "Django",
    "SQL", "MySQL", "MongoDB", "Spring",
    "Machine Learning", "Deep Learning",
    "Artificial Intelligence", "Data Science",
    "TensorFlow", "PyTorch", "Scikit-learn",
    "Pandas", "NumPy", "Power BI", "Tableau",
    "Data Structures", "Algorithms", "OOP",
    "Git", "GitHub", "REST API", "Testing",
    "Statistics", "Data Visualization",
    "Computer Vision", "Natural Language Processing",
    "Communication", "Leadership", "Problem Solving",
    "Excel", "AWS", "Azure", "Docker",
    "Kubernetes", "Linux", "HTML5", "CSS3",
    "Node.js", "Express.js", "PostgreSQL",
    "OpenCV", "Generative AI", "Large Language Models"
]


# ==================================================
# 2. ROLE-BASED SKILLS
# ==================================================

ROLE_SKILLS = {
    "Python Developer": [
        "Python", "OOP", "SQL", "Flask", "Django",
        "REST API", "Data Structures", "Algorithms", "Git"
    ],

    "Software Engineer": [
        "Python", "Java", "OOP", "Data Structures",
        "Algorithms", "SQL", "Git", "REST API", "Testing"
    ],

    "AI/ML Engineer": [
        "Python", "Machine Learning", "Deep Learning",
        "TensorFlow", "PyTorch", "Scikit-learn",
        "Pandas", "NumPy", "SQL"
    ],

    "Data Scientist": [
        "Python", "SQL", "Statistics", "Pandas",
        "NumPy", "Scikit-learn", "Data Visualization",
        "Power BI", "Machine Learning"
    ],

    "Web Developer": [
        "HTML", "CSS", "JavaScript", "React",
        "Flask", "Django", "REST API", "SQL", "Git"
    ],

    "Java Developer": [
        "Java", "OOP", "Data Structures", "Algorithms",
        "SQL", "Spring", "REST API", "Git"
    ]
}


# ==================================================
# 3. RESUME SECTION DATABASE
# ==================================================

RESUME_SECTIONS = {
    "Education": [
        "education",
        "academic qualification",
        "educational qualification",
        "academic background",
        "education qualification",
        "qualification"
    ],

    "Skills": [
        "skills",
        "technical skills",
        "key skills",
        "core competencies",
        "technical competencies",
        "skill set"
    ],

    "Projects": [
        "projects",
        "academic projects",
        "personal projects",
        "project experience",
        "key projects",
        "major projects"
    ],

    "Experience": [
        "experience",
        "work experience",
        "professional experience",
        "internship",
        "internships",
        "employment history"
    ],

    "Certifications": [
        "certifications",
        "certificates",
        "courses",
        "licenses",
        "training and certifications"
    ]
}


# ==================================================
# 4. TEXT NORMALIZATION
# ==================================================

def normalize_text(text):
    """Normalize text for reliable matching."""

    if not text:
        return ""

    text = text.lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+#.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_heading(line):
    """Normalize a possible resume heading."""

    line = line.lower().strip()
    line = line.replace("&", " and ")
    line = re.sub(r"[\s:|_\-]+", " ", line)
    line = re.sub(r"[^a-z0-9\s]", "", line)

    return re.sub(r"\s+", " ", line).strip()


# ==================================================
# 5. EXTRACT RESUME TEXT
# ==================================================

def extract_resume_text(file_path):
    """Extract readable text from PDF or DOCX resumes."""

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            "The uploaded resume file was not found."
        )

    extension = os.path.splitext(file_path)[1].lower()
    extracted_text = []

    try:
        if extension == ".pdf":

            reader = PdfReader(file_path)

            if reader.is_encrypted:
                try:
                    result = reader.decrypt("")
                    if not result:
                        raise ValueError(
                            "The PDF is password protected. "
                            "Please upload an unlocked PDF."
                        )
                except Exception:
                    raise ValueError(
                        "The PDF is password protected. "
                        "Please upload an unlocked PDF."
                    )

            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_text.append(page_text)

        elif extension == ".docx":

            document = Document(file_path)

            # Extract paragraphs
            for paragraph in document.paragraphs:
                if paragraph.text.strip():
                    extracted_text.append(paragraph.text)

            # Extract tables
            for table in document.tables:
                for row in table.rows:
                    row_text = [
                        cell.text.strip()
                        for cell in row.cells
                        if cell.text.strip()
                    ]

                    if row_text:
                        extracted_text.append(" ".join(row_text))

        else:
            raise ValueError(
                "Only PDF and DOCX files are supported."
            )

    except ValueError:
        raise

    except Exception as error:
        raise ValueError(
            f"Unable to read the uploaded resume: {error}"
        )

    resume_text = "\n".join(extracted_text).strip()

    if not resume_text:
        raise ValueError(
            "No readable text was found in your resume. "
            "Your PDF may be scanned or image-based. "
            "Please upload a text-based PDF or DOCX."
        )

    return resume_text


# ==================================================
# 6. DETECT SKILLS
# ==================================================

def detect_skills(resume_text):
    """Detect technical and soft skills in resume text."""

    normalized_resume = normalize_text(resume_text)
    detected_skills = []

    for skill in SKILLS_LIST:

        normalized_skill = normalize_text(skill)

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(normalized_skill)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, normalized_resume):
            detected_skills.append(skill)

    return detected_skills


# ==================================================
# 7. DETECT RESUME SECTIONS
# ==================================================

def detect_sections(resume_text):
    """
    Detect resume headings.
    Supports headings such as EDUCATION, EDUCATION &
    QUALIFICATIONS, TECHNICAL SKILLS and PROJECTS.
    """

    found_sections = []

    lines = [
        normalize_heading(line)
        for line in resume_text.splitlines()
        if line.strip()
    ]

    for section, keywords in RESUME_SECTIONS.items():

        normalized_keywords = [
            normalize_heading(keyword)
            for keyword in keywords
        ]

        for line in lines:

            # Exact heading match
            if line in normalized_keywords:
                found_sections.append(section)
                break

            # Heading with an additional descriptive word
            if any(
                line.startswith(keyword + " ")
                or line.endswith(" " + keyword)
                for keyword in normalized_keywords
            ):
                found_sections.append(section)
                break

    return found_sections


# ==================================================
# 8. DETECT CONTACT INFORMATION
# ==================================================

def detect_contact_information(resume_text):
    """Detect email addresses and phone numbers."""

    email_pattern = (
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    )

    phone_pattern = (
        r"(?<!\w)\+?\d[\d\s().-]{7,}\d(?!\w)"
    )

    email_match = re.search(
        email_pattern,
        resume_text,
        re.IGNORECASE
    )

    phone_match = re.search(
        phone_pattern,
        resume_text
    )

    return {
        "email_found": bool(email_match),
        "phone_found": bool(phone_match)
    }


# ==================================================
# 9. CALCULATE RESUME SCORE
# ==================================================

def calculate_resume_score(
    resume_text,
    skills,
    sections,
    matched_role_skills,
    required_role_skills
):
    """
    Rule-based resume review score.

    Section completeness: 25
    Role skill match: 35
    Resume content: 15
    Projects and experience: 15
    Contact information: 10

    Total: 100
    """

    score_breakdown = {}

    # Section completeness: 25 points
    if RESUME_SECTIONS:
        section_score = (
            len(set(sections)) / len(RESUME_SECTIONS)
        ) * 25
    else:
        section_score = 0

    score_breakdown["Section Completeness"] = round(
        section_score
    )

    # Role skill match: 35 points
    if required_role_skills:
        skill_score = (
            len(matched_role_skills)
            / len(required_role_skills)
        ) * 35
    else:
        skill_score = 0

    score_breakdown["Role Skill Match"] = round(
        skill_score
    )

    # Resume content: 15 points
    word_count = len(resume_text.split())

    if 200 <= word_count <= 800:
        length_score = 15
    elif 150 <= word_count < 200 or 800 < word_count <= 1000:
        length_score = 10
    elif 100 <= word_count < 150:
        length_score = 6
    else:
        length_score = 3

    score_breakdown["Resume Content"] = length_score

    # Projects and experience: 15 points
    evidence_score = 0

    if "Projects" in sections:
        evidence_score += 8

    if "Experience" in sections:
        evidence_score += 7

    score_breakdown["Projects and Experience"] = evidence_score

    # Contact information: 10 points
    contact = detect_contact_information(resume_text)

    contact_score = 0

    if contact["email_found"]:
        contact_score += 5

    if contact["phone_found"]:
        contact_score += 5

    score_breakdown["Contact Information"] = contact_score

    total_score = sum(score_breakdown.values())
    total_score = max(0, min(100, round(total_score)))

    return total_score, score_breakdown


# ==================================================
# 10. GENERATE RESUME SUGGESTIONS
# ==================================================

def generate_suggestions(
    skills,
    sections,
    missing_role_skills,
    word_count
):

    suggestions = []

    if missing_role_skills:
        suggestions.append(
            "Consider adding relevant skills only if you genuinely "
            "have experience with: "
            + ", ".join(missing_role_skills)
        )

    if "Education" not in sections:
        suggestions.append(
            "Add an Education section containing your degree, "
            "institution and graduation details."
        )

    if "Skills" not in sections:
        suggestions.append(
            "Add a clearly labelled Technical Skills section."
        )

    if "Projects" not in sections:
        suggestions.append(
            "Add a Projects section describing your academic "
            "or personal projects."
        )

    if "Experience" not in sections:
        suggestions.append(
            "Include internships, work experience or practical "
            "experience if available."
        )

    if "Certifications" not in sections:
        suggestions.append(
            "Include relevant certifications and completed courses "
            "if available."
        )

    if word_count < 200:
        suggestions.append(
            "Your resume has limited content. Add meaningful "
            "project details, technical skills and achievements."
        )

    if len(skills) < 5:
        suggestions.append(
            "Include relevant technical skills that you can "
            "confidently demonstrate."
        )

    if not suggestions:
        suggestions.append(
            "Your resume covers the main checks. Improve it further "
            "with measurable project results and relevant achievements."
        )

    return suggestions


# ==================================================
# 11. GENERATE RESUME-BASED INTERVIEW QUESTIONS
# ==================================================

def generate_practice_questions(skills, target_role):

    role_questions = {
        "Python Developer": [
            "What are the main features of Python?",
            "Explain the difference between a list and a tuple.",
            "What is exception handling in Python?"
        ],

        "Software Engineer": [
            "Explain the four pillars of OOP.",
            "What is the difference between a process and a thread?",
            "How do you approach debugging a software application?"
        ],

        "AI/ML Engineer": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain overfitting and how to prevent it.",
            "What is the purpose of feature engineering?"
        ],

        "Data Scientist": [
            "What is the difference between classification and regression?",
            "How do you handle missing data?",
            "Explain the importance of data visualization."
        ],

        "Web Developer": [
            "What is the difference between frontend and backend development?",
            "Explain how REST APIs work.",
            "What is the difference between HTML, CSS and JavaScript?"
        ],

        "Java Developer": [
            "What is the difference between JDK, JRE and JVM?",
            "Explain inheritance in Java.",
            "What is the difference between an interface and an abstract class?"
        ]
    }

    skill_questions = {
        "Python": "Explain an important Python project you have developed.",
        "Java": "How have you used Java in your projects?",
        "SQL": "Explain the difference between JOIN and GROUP BY.",
        "Machine Learning": "Describe a machine learning algorithm you have implemented.",
        "Deep Learning": "What is the difference between machine learning and deep learning?",
        "Flask": "How do you create and manage routes in Flask?",
        "React": "What are React components and how do they work?",
        "TensorFlow": "How have you used TensorFlow in a project?",
        "Pandas": "How do you use Pandas for data preprocessing?",
        "NumPy": "What is the purpose of NumPy arrays?",
        "PyTorch": "What is PyTorch and how is it used in deep learning?",
        "Scikit-learn": "How do you use Scikit-learn to build a machine learning model?",
        "Computer Vision": "Explain an application of computer vision you have worked on.",
        "Natural Language Processing": "What is tokenization in NLP?"
    }

    questions = list(role_questions.get(target_role, []))

    for skill in skills:
        question = skill_questions.get(skill)

        if question:
            questions.append(question)

    return list(dict.fromkeys(questions))[:8]


# ==================================================
# 12. COMPLETE RESUME ANALYSIS
# ==================================================

def analyze_resume(file_path, target_role=None):
    """Run complete rule-based resume analysis."""

    # Extract resume text
    resume_text = extract_resume_text(file_path)

    if not resume_text.strip():
        raise ValueError(
            "The uploaded resume does not contain readable text."
        )

    # Validate selected job role
    if target_role not in ROLE_SKILLS:
        target_role = None

    # Detect skills and sections
    skills = detect_skills(resume_text)
    sections = detect_sections(resume_text)

    # Match role-specific skills
    required_role_skills = ROLE_SKILLS.get(target_role, [])

    matched_role_skills = [
        skill for skill in required_role_skills
        if skill in skills
    ]

    missing_role_skills = [
        skill for skill in required_role_skills
        if skill not in skills
    ]

    # Calculate word count
    word_count = len(resume_text.split())

    # Calculate score
    score, score_breakdown = calculate_resume_score(
        resume_text,
        skills,
        sections,
        matched_role_skills,
        required_role_skills
    )

    # Calculate skill match percentage
    if required_role_skills:
        skill_match_percentage = round(
            len(matched_role_skills)
            / len(required_role_skills)
            * 100
        )
    else:
        skill_match_percentage = 0

    # Detect contact information
    contact_information = detect_contact_information(resume_text)

    # Generate suggestions
    suggestions = generate_suggestions(
        skills,
        sections,
        missing_role_skills,
        word_count
    )

    # Generate practice questions
    practice_questions = generate_practice_questions(
        skills,
        target_role
    )

    # Return complete analysis
    return {
        "resume_text": resume_text,
        "skills": skills,
        "sections": sections,

        "missing_sections": [
            section for section in RESUME_SECTIONS
            if section not in sections
        ],

        "word_count": word_count,
        "score": score,
        "ats_score": score,
        "target_role": target_role,

        "matched_role_skills": matched_role_skills,
        "missing_role_skills": missing_role_skills,
        "skill_match_percentage": skill_match_percentage,

        "score_breakdown": score_breakdown,
        "contact_information": contact_information,
        "suggestions": suggestions,
        "practice_questions": practice_questions
    }
