# 🐾 DongoPet Backend

Powering the DongoPet mobile app with fast, secure, and intelligent APIs for pet nutrition analysis, user management, and AI-powered pet care guidance.

---

## 📝 Overview

**DongoPet Backend** provides REST APIs for the DongoPet mobile app—a smart pet management platform. The backend features:

- **Scanner/Analyzer API** — AI/ML endpoints for pet food and treat analysis (ingredients, nutritional value, pet safety, etc.)
- **AI Vet Assistant** — Integrates with AI APIs for instant pet care Q&A
- **Pet Profiles** — CRUD for multiple pets per user, including health, preferences, and emergency data
- **User Auth** — Email & social login (Google OAuth)
- **Emergency Card** — Store and retrieve pet emergency info
- **Admin Tools** — Manage users, analytics, and flagged scans
- **Secure** — JWT auth, CORS, and input validation

---

## ⚙️ Tech Stack

- **Python 3.10+**
- **FastAPI** (REST framework)
- **Uvicorn** (ASGI server)
- **SQLAlchemy** (ORM)
- **Alembic** (Migrations)
- **PostgreSQL** (Database)
- **OAuth2** (Google/social login)
- **Pydantic** (Validation)
- **Docker & Docker Compose**
- **Pytest** (Testing)
- **External AI/ML APIs** (ingredient analysis, vet Q&A)

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/DongoPet-Pet-Management-Mobile-App/backend.git
cd backend
```

### 2. Set Up Environment

- Recommended: [virtualenv](https://virtualenv.pypa.io/) or [Poetry](https://python-poetry.org/)
- Install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

- Copy `.env.example` to `.env` and fill in secrets (DB, JWT, OAuth, API keys).

### 3. Run Database (Docker/Postgres)

```bash
docker-compose up db
```

### 4. Run the Server

```bash
uvicorn app.main:app --reload
```

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📚 API Endpoints

### Auth & User

- `POST /auth/signup` — Sign up with email
- `POST /auth/login` — Login with email
- `POST /auth/google` — Google OAuth login

### Pet Profiles

- `GET /pets` — List user’s pets
- `POST /pets` — Add a pet
- `PUT /pets/{pet_id}` — Update pet
- `DELETE /pets/{pet_id}` — Remove pet

### Scanner & Analyzer

- `POST /scan/food` — Upload food/treat image for analysis
- `GET /scan/result/{scan_id}` — Get analysis result

### AI Vet Assistant

- `POST /ai/vet` — Ask pet care questions, get AI answers

### Emergency Card

- `GET /emergency` — Get emergency data
- `PUT /emergency` — Update emergency info

### User & Profile

- `GET /user/profile`
- `PUT /user/profile`

---

## 🗂️ Project Structure

```
app/
 ├── main.py         # FastAPI app entry
 ├── models/         # SQLAlchemy models
 ├── schemas/        # Pydantic schemas
 ├── routers/        # API endpoints
 ├── services/       # Business logic, AI integrations
 ├── db/             # DB sessions, migrations
 ├── utils/          # Helpers (JWT, file upload, etc)
 └── tests/          # Pytest suites
```

---

## 🧪 Development

- **Lint:** `flake8 app/`
- **Test:** `pytest`
- **Run:** `uvicorn app.main:app --reload`
- **Format:** `black app/`

---

## 🚢 Deployment

- Docker-ready (`Dockerfile` and `docker-compose.yml` provided)
- Deploy to: Heroku, Render, AWS, GCP, etc.

---

## 🤝 Contributing

Pull requests and issues are welcome!  
Please open issues for bugs or feature requests.

---

## 📄 License

MIT

---

## 📬 Contact

- [denysbakin@gmail.com](mailto:denysbakin@gmail.com)
- [@denysbakin](https://github.com/denysbakin)

---

**DongoPet** — *Smart pet care, made simple!* 🦴