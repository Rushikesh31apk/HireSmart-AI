# ⚡ HireSmart AI — ATS-Friendly Resume Generator

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=flat-square&logo=bootstrap&logoColor=white)](https://getbootstrap.com/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Engine-FF6B6B?style=flat-square)](https://www.reportlab.com/)
[![ATS Score](https://img.shields.io/badge/ATS%20Score-98%2F100-success?style=flat-square)](#)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](#license)

A modern, full-stack resume builder that generates **ATS-optimized PDFs** with two professional styles, AI-assisted writing, email OTP auth, and a guided 8-step wizard.

[Features](#-features) · [Quick Start](#-quick-start) · [Project Structure](#-project-structure) · [API Reference](#-api-reference)

</div>

---

## 🌟 Overview

HireSmart AI helps students and professionals build recruiter-ready resumes in minutes. Users fill in a step-by-step form, preview **two distinct resume designs side by side**, choose their preferred style, and download a pixel-perfect PDF — all without leaving the browser.

---

## ✨ Features

### 🔐 Authentication
- Registration with email OTP verification (6-digit, 10-min expiry)
- Secure login with bcrypt password hashing
- Password reset via OTP flow
- Profile management with avatar upload

### 📝 8-Step Resume Wizard

| Step | Section | Highlights |
|------|---------|------------|
| 1 | Personal Info | Photo upload, name, role, contacts, LinkedIn/GitHub |
| 2 | Professional Summary | AI-generated suggestions, writing tips |
| 3 | Technical Skills | Languages, frameworks, tools, databases, core subjects |
| 4 | Education | Dynamic add/remove, GPA, multiple entries |
| 5 | Projects | Tech stack, descriptions, live links |
| 6 | Certifications | Issuer, year, multiple entries |
| 7 | Achievements | Bullet-point format, unlimited entries |
| 8 | Hobbies & Interests | Optional personal section |

- Auto-save every 30 seconds
- Progress bar with clickable step indicators
- Full client + server validation

### 🎨 Two Resume Styles (Preview + PDF)

| | Style A — Classic Prestige | Style B — Modern Edge |
|---|---|---|
| **Layout** | Single-column | Sidebar + main |
| **Typography** | Serif-feel, Playfair-inspired | Syne bold, geometric |
| **Accent** | Navy `#1e3a5f` + Gold `#c9a84c` | Navy sidebar + Teal `#14b8a6` |
| **Best for** | Corporate, finance, academia | Tech, startups, design |
| **ATS Safe** | ✅ | ✅ |

Users preview both styles simultaneously, click to select, then download the matching PDF.

### 📄 PDF Generation
- ReportLab engine — no browser dependencies
- Style A & B PDFs match the HTML preview exactly
- Photo embedding, teal rules, chip-style skill cells, project border strips
- Passed to `?style=A` or `?style=B` query param

### 📊 Dashboard
- Resume list with last-updated timestamps
- One-click edit, preview, and download
- Delete with confirmation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone
git clone https://github.com/yourusername/hiresmart-ai.git
cd hiresmart-ai

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Run
python app.py
```

Open **http://localhost:5000** — done. 🎉

The database and upload folder are created automatically on first run.

### Environment Variables (Optional)

Copy `.env.example` to `.env` and configure:

```env
SECRET_KEY=your-secret-key-here
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=you@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=HireSmart AI <you@gmail.com>
```

> **Dev mode:** If email is not configured, OTPs are printed to the console automatically.

### Dependencies

```
Flask>=3.0
Werkzeug>=3.0
reportlab>=4.0
Pillow>=10.1
python-dotenv>=1.0
```

---

## 📁 Project Structure

```
hiresmart-ai/
├── app.py                  # Flask app — routes, auth, PDF generation
├── requirements.txt
├── .env.example
├── database.db             # Auto-created SQLite database
│
├── templates/
│   ├── base.html           # Shared navbar + footer
│   ├── index.html          # Landing page
│   ├── register.html
│   ├── login.html
│   ├── verify_otp.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   ├── dashboard.html
│   ├── profile.html
│   ├── resume_form.html    # 8-step builder wizard
│   └── preview_resume.html # Side-by-side style selector + preview
│
└── static/
    ├── css/main.css
    ├── js/main.js          # Wizard logic, style selector, scale/restore
    └── uploads/            # User photos (auto-created)
```

---

## 🔗 API Reference

### Auth

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/register` | Create account |
| GET/POST | `/login` | Sign in |
| GET | `/logout` | Sign out |
| GET/POST | `/verify-otp` | Email OTP verification |
| POST | `/resend-otp` | Resend OTP (JSON) |
| GET/POST | `/forgot-password` | Request password reset |
| GET/POST | `/reset-password` | Submit new password |

### Resume

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/dashboard` | Resume list |
| GET | `/resume/new` | Create blank resume |
| GET | `/resume/<id>/edit` | Open builder wizard |
| POST | `/resume/<id>/save` | Auto-save (JSON) |
| GET | `/resume/<id>/preview` | Style selector preview |
| GET | `/resume/<id>/pdf?style=A` | Download PDF (A or B) |
| POST | `/resume/<id>/delete` | Delete resume |

### Utilities

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/suggest-summary` | AI summary suggestion (JSON) |
| GET | `/uploads/<filename>` | Serve uploaded photos |

---


## 🔒 Security

- Passwords hashed with Werkzeug `pbkdf2:sha256`
- OTPs expire in 10 minutes and are single-use
- Email enumeration prevented on forgot-password route
- File uploads restricted to image types, max 5 MB
- `login_required` decorator on all protected routes
- Session-based auth with a configurable secret key

---

## 🛠️ How Style Selection Works

1. **Preview page** renders both resume designs from the same Jinja2 data
2. User clicks a card → `selectStyle('A'|'B')` fires in `main.js`
3. Choice is persisted in `sessionStorage` keyed by resume ID
4. On "Download PDF" click, `?style=A` or `?style=B` is appended to the URL
5. `download_pdf` route reads the param and calls `generate_pdf_style_a` or `generate_pdf_style_b`
6. Both PDF generators mirror their HTML counterparts exactly — same colors, layout, spacing

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

Built with Flask, ReportLab, Bootstrap 5, and ☕

**⭐ Star the repo if it helped you land a job!**

© 2026 HireSmart AI

</div>
