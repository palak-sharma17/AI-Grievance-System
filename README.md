# AI-Grievance-System
#  AI Grievance Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**An AI-powered citizen grievance portal that automatically classifies, prioritizes, and routes public complaints to the right government department using NLP and Machine Learning.**

[Features](#-features) • [Demo](#-demo) • [Tech Stack](#-tech-stack) • [Setup](#-setup) • [API Docs](#-api-reference) • [Screenshots](#-screenshots)

</div>

---

##  Overview

The **AI Grievance Management System** is a full-stack web application that allows citizens to submit complaints about civic issues (water, roads, electricity, sanitation, etc.) and automatically:

-  **Classifies** the complaint to the correct government department using a TF-IDF + Naive Bayes ML model trained on Bangalore civic data
-  **Analyzes sentiment** (Positive / Negative / Critical) to set complaint priority
- **Provides an admin dashboard** for officials to track, update, and resolve grievances
-  **Exports filtered reports** as CSV for record keeping

---

##  Features

| Feature | Description |
|---|---|
|  AI Classification | Auto-routes grievances to the right department (6 categories) |
|  Sentiment Analysis | Detects urgency — Critical, Negative, or Positive |
|  JWT Authentication | Secure login for both citizens and admins |
|  Status Tracking | Real-time status updates with full activity history |
|  Admin Dashboard | Stats overview, grievance management, assignment |
|  CSV Export | Filtered export with date range, status, priority filters |
| Activity Timeline | Every status change is logged with timestamp + actor |
|  REST API | Fully documented via Swagger UI at `/docs` |

---

##  AI Model

The classifier is trained on **250 real Bangalore civic complaints** (`bangalore_dataset.csv`) and can identify:

| Department | Example Complaint |
|---|---|
|  Electricity | "Transformer issue in Basavanagudi" |
|  Transport | "Bus delay in Jayanagar" |
|  Water Supply | "Pipe leak in Koramangala" |
|  Roads | "Pothole on MG Road" |
|  Sanitation | "Garbage not collected in BTM Layout" |
|  Public Safety | "Street lights not working in HSR Layout" |

**Model Pipeline:** `TF-IDF Vectorizer (bigrams) → Multinomial Naive Bayes`  
Confidence score is returned with every prediction so admins can verify low-confidence classifications.

---

## Project Structure

```
AI-Grievance-System/
│
├── main.py              # FastAPI app entry point, startup tasks
├──  models.py            # SQLAlchemy DB models (User, Grievance, History)
├──  schemas.py           # Pydantic request/response schemas
├──  routes.py            # All API route handlers
├──  auth.py              # JWT auth, password hashing, role guards
├──  database.py          # SQLite DB connection & session
├──  ai_classifier.py     # ML model training + prediction logic
│
├──  index.html           # Frontend — single-file full-stack UI
│
├── bangalore_dataset.csv    # Training data (250 Bangalore complaints)
├──  processed_dataset.csv    # Cleaned/processed version
│
├──  requirements.txt     # Python dependencies
├──  .gitignore
└──  README.md
```

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — High-performance Python API framework
- [SQLAlchemy](https://www.sqlalchemy.org/) — ORM for database operations
- [SQLite](https://www.sqlite.org/) — Zero-config embedded database
- [scikit-learn](https://scikit-learn.org/) — TF-IDF vectorizer + Naive Bayes classifier
- [python-jose](https://github.com/mpdavis/python-jose) — JWT token creation & verification
- [passlib](https://passlib.readthedocs.io/) — Bcrypt password hashing

**Frontend**
- Vanilla HTML / CSS / JavaScript (single `index.html`, no build step)
- Google Fonts (Syne + DM Sans)
- Dark theme dashboard with modals, filters, toast notifications

---

## Setup & Run

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Clone the repository
```bash
git clone https://github.com/palak-sharma17/AI-Grievance-System.git
cd AI-Grievance-System
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the server
```bash
uvicorn main:app --reload
```

The server starts at **http://localhost:8000**

On first run, it will automatically:
-  Create the SQLite database (`grievance.db`)
- Train the AI classifier on `bangalore_dataset.csv`
-  Seed a default admin account

### 5. Open the frontend
Open `index.html` directly in your browser (double-click or `File → Open`).

> Make sure the backend is running at `http://localhost:8000` before opening the UI.

---

##  Default Admin Credentials

```
Email:    admin@grievance.gov
Password: Admin@1234
```

>  Change these in production by updating `main.py` → `seed_admin()`

---

## API Reference

Full interactive docs available at: **http://localhost:8000/docs**

### Auth Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Register a new citizen |
| `POST` | `/auth/login` | Login and receive JWT token |
| `GET` | `/auth/me` | Get current user info |

### Grievance Endpoints
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/grievances` | Optional | Submit a new grievance (AI classifies it) |
| `GET` | `/grievances` | Required | List grievances (citizens see own; admin sees all) |
| `GET` | `/grievances/{id}` | Required | Get grievance details + history |
| `PUT` | `/grievances/{id}` | Admin | Update status, priority, assignment |
| `GET` | `/grievances/{id}/history` | Required | Get activity timeline |

### Admin Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/dashboard` | Stats: total, in-progress, critical, by-dept |
| `GET` | `/admin/export` | Download filtered CSV report |

### Example: Submit a Grievance
```bash
curl -X POST http://localhost:8000/grievances \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your_token>" \
  -d '{
    "name": "Rahul Verma",
    "phone": "9876543210",
    "location": "Indiranagar, Bangalore",
    "description": "Street lights have not been working for 3 days near 100 Feet Road"
  }'
```

**Response:**
```json
{
  "grievance_id": "GRV-A3F9C21B",
  "category": "electricity",
  "department": "Electricity Department",
  "priority": "medium",
  "ai_sentiment": "negative",
  "ai_confidence": 0.87,
  "status": "ai_analyzed"
}
```

---

## Database Schema

```
users
  id, name, email, phone, password (bcrypt), is_admin, is_active, created_at

grievances
  id, grievance_id (GRV-XXXXXXXX), user_id → users
  name, phone, location, description
  category (enum), priority (enum), status (enum)
  department, ai_confidence, ai_sentiment
  assigned_to, resolution_note
  created_at, updated_at

grievance_history
  id, grievance_id → grievances
  status, note, changed_by, created_at
```

---

## Grievance Lifecycle

```
submitted → ai_analyzed → assigned → in_progress → resolved → closed
                                                  ↘ rejected
```

Every transition is logged in `grievance_history` with the actor and timestamp.

---

## Future Improvements

- [ ] Image upload support for complaints
- [ ] Email/SMS notifications on status change
- [ ] Multi-language support (Hindi, Kannada)
- [ ] Map view to visualize grievances by area
- [ ] Duplicate complaint detection
- [ ] Mobile app (React Native)
- [ ] Docker containerization

---

## Contributing

Pull requests are welcome! For major changes, please open an issue first.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add some feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

\
  License
This project is licensed under the MIT License.
