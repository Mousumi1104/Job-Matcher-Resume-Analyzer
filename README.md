# 🧠 Resume Analyzer

Resume Analyzer is a **Django-based AI web application** that intelligently analyzes resumes, extracts skills, and matches them to relevant job descriptions using NLP and ML models. It simplifies recruitment by automating resume parsing, scoring, and job recommendation processes.

---

## 🚀 Features

- 📄 **Smart Resume Parsing** – Extracts structured data (skills, education, experience) from PDF/DOCX resumes.  
- 🧩 **AI-Powered Skill Matching** – Uses NLP (spaCy + scikit-learn) to compute skill similarity with job requirements.  
- 💼 **Job Recommendations** – Suggests best-fit jobs for each candidate.  
- 🧠 **Machine Learning & NLP** – Employs spaCy, scikit-learn, and custom matching algorithms.  
- ⚙️ **Asynchronous Tasks** – Uses **Celery + Redis** for background processing.  
- 🔐 **JWT Authentication** – Secures APIs using `djangorestframework_simplejwt`.  
- 📊 **Dashboard & Analytics** – Displays match statistics, resume counts, and candidate insights.  
- 🌐 **REST API Support** – Built using Django REST Framework for scalability and integration.  

---

## 🏗️ Tech Stack

| Category | Tools / Libraries |
|-----------|-------------------|
| **Framework** | Django 5.2.7 |
| **Backend** | Python 3.12+, Celery, Redis |
| **Frontend** | HTML, CSS, JS (Django Templates) |
| **Database** | PostgreSQL |
| **AI / NLP** | spaCy, scikit-learn, PyMuPDF, Python-Docx |
| **Auth** | JWT (SimpleJWT) |
| **Task Queue** | Celery + Redis |
| **Cloud / APIs** | Google GenAI, Cohere, OpenAI integrations supported |

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/Mousumi1104/Job-Matcher-Resume-Analyzer.git
cd Job-Matcher-Resume-Analyzer
