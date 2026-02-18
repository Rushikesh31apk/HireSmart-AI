# ⚡ HireSmart AI — ATS-Friendly Resume Generator

> Build professional, ATS-optimized resumes in minutes. Built for students & freshers.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Email (Optional)
Set these environment variables for real OTP emails:
```bash
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_USER=your_email@gmail.com
export EMAIL_PASSWORD=your_app_password
```

> 💡 **Dev Mode**: If email is not configured, OTPs are printed to the console. You can still use the full app!

#### Gmail Setup:
1. Go to Google Account → Security → 2-Step Verification → App Passwords
2. Generate an App Password for "Mail"
3. Use that 16-character password as `EMAIL_PASSWORD`

### 3. Run the App
```bash
python app.py
```

Visit: **http://localhost:5000**

---

## 📁 Project Structure

```
resume-ai/
├── app.py                  # Flask backend (auth, routes, PDF generation)
├── requirements.txt        # Python dependencies
├── database.db             # SQLite DB (auto-created on first run)
├── uploads/                # User uploaded photos
├── templates/
│   ├── base.html           # Base layout with navbar + footer
│   ├── index.html          # Landing page (hero, features, FAQ, CTA)
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── verify_otp.html     # Email OTP verification
│   ├── forgot_password.html
│   ├── reset_password.html
│   ├── dashboard.html      # User dashboard
│   ├── resume_form.html    # 8-step resume builder wizard
│   ├── preview.html        # Resume preview page
│   └── profile.html        # User profile & settings
└── static/
    ├── css/style.css       # Premium dark theme CSS
    └── js/main.js          # JavaScript (wizard, OTP, animations)
```

---

## ✨ Features

| Feature | Status |
|---------|--------|
| Student Registration & Login | ✅ |
| Email OTP Verification | ✅ |
| Forgot Password with OTP | ✅ |
| 8-Step Resume Builder | ✅ |
| Profile Photo Upload | ✅ |
| AI Summary Suggestions | ✅ |
| Live Resume Preview | ✅ |
| ATS-Friendly PDF Download | ✅ |
| Print Support | ✅ |
| Dashboard with Stats | ✅ |
| Profile Management | ✅ |
| Auto-save (every 30s) | ✅ |
| Responsive Design | ✅ |
| Premium Dark Theme | ✅ |

---

## 🗄️ Database Schema

```sql
-- Users table
users (id, name, email, password, is_verified, avatar, created_at)

-- OTP codes
otp_codes (id, user_id, otp, purpose, expiry_time, used)

-- Resumes (JSON stored resume data)
resumes (id, user_id, title, resume_data, created_at, updated_at)
```

---

## 🔐 Security Features
- Werkzeug password hashing (PBKDF2-SHA256)
- Session-based authentication
- OTP expiry (10 minutes)
- Email enumeration prevention
- File upload validation
- SQL injection prevention (parameterized queries)

---

## 📦 Dependencies
```
Flask==3.0.0
Werkzeug==3.0.1
reportlab==4.0.7
Pillow==10.1.0
python-dotenv==1.0.0
```

---

## 🎨 UI/UX

- **Theme**: Premium dark (navy/cyan/purple gradient)
- **Fonts**: Plus Jakarta Sans + Space Mono
- **Components**: Glassmorphism cards, animated hero, scroll animations
- **Framework**: Bootstrap 5 + Font Awesome 6

---

## 📄 License

Built for educational/portfolio purposes.
