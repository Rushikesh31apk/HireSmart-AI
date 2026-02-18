"""
HireSmart AI — ATS-Friendly Resume Generator
Flask Backend Application
"""

import os
import json
import random
import sqlite3
import smtplib
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from io import BytesIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, send_file, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# PDF generation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, Image as RLImage
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# ─── App Config ────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'hiresmart-ai-secret-key-2024-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Email config — update these or use environment variables
EMAIL_HOST     = os.environ.get('EMAIL_HOST',     'smtp.gmail.com')
EMAIL_PORT     = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USER     = os.environ.get('EMAIL_USER',     'narawaderushikesh18@gmail.com')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD', 'nkziakqypimfhlzo')
EMAIL_FROM     = os.environ.get('EMAIL_FROM',     'HireSmart AI <narawaderushikesh18@gmail.com>')

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ─── Database ──────────────────────────────────────────────────────────────────

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
    return g.db

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Create all tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            email       TEXT    NOT NULL UNIQUE,
            password    TEXT    NOT NULL,
            is_verified INTEGER NOT NULL DEFAULT 0,
            avatar      TEXT,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS otp_codes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            otp         TEXT    NOT NULL,
            purpose     TEXT    NOT NULL DEFAULT 'verify',
            expiry_time TEXT    NOT NULL,
            used        INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS resumes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL DEFAULT 'My Resume',
            resume_data TEXT    NOT NULL DEFAULT '{}',
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

# ─── Helpers ───────────────────────────────────────────────────────────────────

def allowed_file(filename):
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def get_current_user():
    if 'user_id' not in session:
        return None
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp, purpose='verify'):
    """Send OTP via SMTP. Logs OTP to console if email fails (dev mode)."""
    subject_map = {
        'verify':   'Verify your HireSmart AI account',
        'reset':    'Reset your HireSmart AI password',
    }
    subject = subject_map.get(purpose, 'HireSmart AI OTP')

    html_body = f"""
    <div style="font-family:'Segoe UI',Arial,sans-serif;max-width:500px;margin:auto;
                background:#0f0f1a;color:#e2e8f0;border-radius:16px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#00d4ff,#7c3aed);padding:32px;text-align:center;">
        <h1 style="margin:0;color:#fff;font-size:28px;letter-spacing:-1px;">HireSmart AI</h1>
        <p style="margin:8px 0 0;color:rgba(255,255,255,0.8);font-size:14px;">ATS-Friendly Resume Generator</p>
      </div>
      <div style="padding:40px 32px;">
        <h2 style="color:#00d4ff;margin-top:0;">{subject}</h2>
        <p style="color:#94a3b8;line-height:1.6;">Use the OTP below to {'verify your email' if purpose == 'verify' else 'reset your password'}. 
        This code expires in <strong style="color:#f59e0b;">10 minutes</strong>.</p>
        <div style="background:#1e1e3a;border:2px solid #00d4ff;border-radius:12px;
                    text-align:center;padding:24px;margin:24px 0;">
          <div style="font-size:42px;font-weight:900;letter-spacing:12px;color:#00d4ff;
                      font-family:monospace;">{otp}</div>
        </div>
        <p style="color:#64748b;font-size:12px;">If you didn't request this, please ignore this email.</p>
      </div>
      <div style="background:#0a0a14;padding:16px;text-align:center;">
        <p style="color:#475569;font-size:12px;margin:0;">© 2024 HireSmart AI. All rights reserved.</p>
      </div>
    </div>
    """

    # Try to send real email
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = EMAIL_FROM
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        # Dev fallback: print OTP to console
        print(f"\n{'='*50}")
        print(f"[DEV MODE] Email failed: {e}")
        print(f"OTP for {to_email}: {otp}")
        print(f"{'='*50}\n")
        return True   # return True so the flow continues in dev

def store_otp(user_id, otp, purpose='verify'):
    db = get_db()
    expiry = (datetime.utcnow() + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M:%S')
    # Invalidate old OTPs for same purpose
    db.execute("UPDATE otp_codes SET used=1 WHERE user_id=? AND purpose=? AND used=0",
               (user_id, purpose))
    db.execute("INSERT INTO otp_codes (user_id, otp, purpose, expiry_time) VALUES (?,?,?,?)",
               (user_id, otp, purpose, expiry))
    db.commit()

def verify_otp_code(user_id, otp, purpose='verify'):
    db = get_db()
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    row = db.execute(
        """SELECT * FROM otp_codes
           WHERE user_id=? AND otp=? AND purpose=? AND used=0 AND expiry_time > ?
           ORDER BY id DESC LIMIT 1""",
        (user_id, otp, purpose, now)
    ).fetchone()
    if row:
        db.execute("UPDATE otp_codes SET used=1 WHERE id=?", (row['id'],))
        db.commit()
        return True
    return False

# ─── Auth Routes ───────────────────────────────────────────────────────────────

@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not all([name, email, password, confirm]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('register'))

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        if existing:
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        hashed = generate_password_hash(password)
        cur = db.execute(
            "INSERT INTO users (name, email, password) VALUES (?,?,?)",
            (name, email, hashed)
        )
        db.commit()
        user_id = cur.lastrowid

        otp = generate_otp()
        store_otp(user_id, otp, 'verify')
        send_otp_email(email, otp, 'verify')

        session['pending_verify_id'] = user_id
        flash('Account created! Please verify your email with the OTP sent.', 'success')
        return redirect(url_for('verify_otp'))

    return render_template('register.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('pending_verify_id') or session.get('reset_user_id')
    if not user_id:
        return redirect(url_for('register'))

    purpose = 'verify' if 'pending_verify_id' in session else 'reset'

    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        if verify_otp_code(user_id, otp, purpose):
            if purpose == 'verify':
                db = get_db()
                db.execute("UPDATE users SET is_verified=1 WHERE id=?", (user_id,))
                db.commit()
                session.pop('pending_verify_id', None)
                session['user_id'] = user_id
                flash('Email verified! Welcome to HireSmart AI!', 'success')
                return redirect(url_for('dashboard'))
            else:
                session['reset_verified'] = True
                return redirect(url_for('reset_password'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')

    return render_template('verify_otp.html', purpose=purpose)

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    user_id = session.get('pending_verify_id') or session.get('reset_user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Session expired.'})
    purpose = 'verify' if 'pending_verify_id' in session else 'reset'
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if user:
        otp = generate_otp()
        store_otp(user_id, otp, purpose)
        send_otp_email(user['email'], otp, purpose)
        return jsonify({'success': True, 'message': 'OTP resent successfully!'})
    return jsonify({'success': False, 'message': 'User not found.'})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user['password'], password):
            if not user['is_verified']:
                session['pending_verify_id'] = user['id']
                otp = generate_otp()
                store_otp(user['id'], otp, 'verify')
                send_otp_email(email, otp, 'verify')
                flash('Please verify your email first. OTP resent.', 'warning')
                return redirect(url_for('verify_otp'))
            session['user_id'] = user['id']
            flash(f"Welcome back, {user['name'].split()[0]}!", 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user:
            otp = generate_otp()
            store_otp(user['id'], otp, 'reset')
            send_otp_email(email, otp, 'reset')
            session['reset_user_id'] = user['id']
        # Always show success to prevent email enumeration
        flash('If that email exists, an OTP has been sent.', 'info')
        return redirect(url_for('verify_otp'))
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_verified'):
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password'))
        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('reset_password'))
        user_id = session.get('reset_user_id')
        db = get_db()
        db.execute("UPDATE users SET password=? WHERE id=?",
                   (generate_password_hash(password), user_id))
        db.commit()
        session.pop('reset_user_id', None)
        session.pop('reset_verified', None)
        flash('Password reset successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_password.html')

# ─── Dashboard ─────────────────────────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    user = get_current_user()
    db = get_db()
    resumes = db.execute(
        "SELECT * FROM resumes WHERE user_id=? ORDER BY updated_at DESC",
        (user['id'],)
    ).fetchall()
    return render_template('dashboard.html', user=user, resumes=resumes)

# ─── Profile ───────────────────────────────────────────────────────────────────

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    if request.method == 'POST':
        action = request.form.get('action')
        db = get_db()
        if action == 'update_profile':
            name = request.form.get('name', '').strip()
            if name:
                db.execute("UPDATE users SET name=? WHERE id=?", (name, user['id']))
                db.commit()
                flash('Profile updated successfully!', 'success')
        elif action == 'change_password':
            current = request.form.get('current_password', '')
            new_pw  = request.form.get('new_password', '')
            confirm = request.form.get('confirm_password', '')
            if not check_password_hash(user['password'], current):
                flash('Current password is incorrect.', 'danger')
            elif new_pw != confirm:
                flash('New passwords do not match.', 'danger')
            elif len(new_pw) < 8:
                flash('Password must be at least 8 characters.', 'danger')
            else:
                db.execute("UPDATE users SET password=? WHERE id=?",
                           (generate_password_hash(new_pw), user['id']))
                db.commit()
                flash('Password changed successfully!', 'success')
        elif action == 'upload_avatar':
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"avatar_{user['id']}.{ext}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    db.execute("UPDATE users SET avatar=? WHERE id=?",
                               (filename, user['id']))
                    db.commit()
                    flash('Avatar updated!', 'success')
        return redirect(url_for('profile'))
    db = get_db()
    resume_count = db.execute(
        "SELECT COUNT(*) as cnt FROM resumes WHERE user_id=?", (user['id'],)
    ).fetchone()['cnt']
    return render_template('profile.html', user=user, resume_count=resume_count)

# ─── Resume Builder ────────────────────────────────────────────────────────────

@app.route('/resume/new')
@login_required
def new_resume():
    user = get_current_user()
    db = get_db()
    # Create a blank resume record
    cur = db.execute(
        "INSERT INTO resumes (user_id, title, resume_data) VALUES (?,?,?)",
        (user['id'], 'My Resume', json.dumps({}))
    )
    db.commit()
    resume_id = cur.lastrowid
    return redirect(url_for('resume_form', resume_id=resume_id))

@app.route('/resume/<int:resume_id>/edit')
@login_required
def resume_form(resume_id):
    user = get_current_user()
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id=? AND user_id=?", (resume_id, user['id'])
    ).fetchone()
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('dashboard'))
    data = json.loads(resume['resume_data'] or '{}')
    return render_template('resume_form.html', user=user, resume=resume, data=data)

@app.route('/resume/<int:resume_id>/save', methods=['POST'])
@login_required
def save_resume(resume_id):
    user = get_current_user()
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id=? AND user_id=?", (resume_id, user['id'])
    ).fetchone()
    if not resume:
        return jsonify({'success': False, 'message': 'Not found'}), 404

    payload = request.get_json(force=True)
    title   = payload.get('title', 'My Resume')
    data    = payload.get('data', {})

    # Handle photo saved as base64 inside data — save to disk
    photo_b64 = data.get('photo_b64')
    if photo_b64 and photo_b64.startswith('data:image'):
        import base64, re
        match = re.match(r'data:image/(\w+);base64,(.*)', photo_b64, re.DOTALL)
        if match:
            ext    = match.group(1)
            raw    = base64.b64decode(match.group(2))
            fname  = f"resume_{resume_id}_photo.{ext}"
            fpath  = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            with open(fpath, 'wb') as fh:
                fh.write(raw)
            data['photo_file'] = fname
            data.pop('photo_b64', None)

    db.execute(
        "UPDATE resumes SET title=?, resume_data=?, updated_at=datetime('now') WHERE id=?",
        (title, json.dumps(data), resume_id)
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Resume saved!'})

@app.route('/resume/<int:resume_id>/delete', methods=['POST'])
@login_required
def delete_resume(resume_id):
    user = get_current_user()
    db = get_db()
    db.execute("DELETE FROM resumes WHERE id=? AND user_id=?", (resume_id, user['id']))
    db.commit()
    flash('Resume deleted.', 'info')
    return redirect(url_for('dashboard'))

# ─── Preview ───────────────────────────────────────────────────────────────────

@app.route('/resume/<int:resume_id>/preview')
@login_required
def preview_resume(resume_id):
    user = get_current_user()
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id=? AND user_id=?", (resume_id, user['id'])
    ).fetchone()
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('dashboard'))
    data = json.loads(resume['resume_data'] or '{}')
    return render_template('preview.html', user=user, resume=resume, data=data)

# ─── PDF Generation ────────────────────────────────────────────────────────────

@app.route('/resume/<int:resume_id>/pdf')
@login_required
def download_pdf(resume_id):
    user = get_current_user()
    db = get_db()
    resume = db.execute(
        "SELECT * FROM resumes WHERE id=? AND user_id=?", (resume_id, user['id'])
    ).fetchone()
    if not resume:
        return "Resume not found", 404

    data = json.loads(resume['resume_data'] or '{}')
    pdf_bytes = generate_pdf(data, user)

    buf = BytesIO(pdf_bytes)
    buf.seek(0)
    name = (data.get('full_name') or user['name'] or 'Resume').replace(' ', '_')
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f"{name}_Resume.pdf")

def generate_pdf(data, user):
    """Generate ATS-friendly PDF resume using ReportLab."""
    buf = BytesIO()

    # Page setup
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm,  bottomMargin=1.5*cm
    )

    # Color palette
    navy  = colors.HexColor('#1a1a4e')
    teal  = colors.HexColor('#00b4d8')
    gray  = colors.HexColor('#555555')
    lgray = colors.HexColor('#888888')
    line  = colors.HexColor('#dee2e6')
    white = colors.white

    # Styles
    styles = getSampleStyleSheet()

    def st(name, **kw):
        return ParagraphStyle(name, **kw)

    name_style = st('Name', fontName='Helvetica-Bold', fontSize=22,
                    textColor=navy, spaceAfter=2)
    role_style = st('Role', fontName='Helvetica', fontSize=12,
                    textColor=teal, spaceAfter=4)
    contact_style = st('Contact', fontName='Helvetica', fontSize=9,
                       textColor=gray, spaceAfter=2)
    section_style = st('Section', fontName='Helvetica-Bold', fontSize=11,
                       textColor=navy, spaceBefore=10, spaceAfter=4)
    body_style = st('Body', fontName='Helvetica', fontSize=9.5,
                    textColor=gray, leading=14, spaceAfter=2)
    bullet_style = st('Bullet', fontName='Helvetica', fontSize=9.5,
                      textColor=gray, leading=14, leftIndent=12, spaceAfter=1,
                      bulletIndent=4)
    small_style = st('Small', fontName='Helvetica', fontSize=8.5,
                     textColor=lgray, spaceAfter=2)

    story = []

    # ── HEADER ──────────────────────────────────────────────────────────────────
    full_name = data.get('full_name') or user['name'] or ''
    role      = data.get('role', '')
    phone     = data.get('phone', '')
    email     = data.get('email') or user['email'] or ''
    address   = data.get('address', '')
    linkedin  = data.get('linkedin', '')
    github    = data.get('github', '')

    # Photo
    photo_file = data.get('photo_file')
    photo_path = (os.path.join(app.config['UPLOAD_FOLDER'], photo_file)
                  if photo_file else None)
    has_photo  = photo_path and os.path.exists(photo_path)

    contact_parts = [p for p in [phone, email, address] if p]
    link_parts    = [p for p in [linkedin, github] if p]

    if has_photo:
        try:
            img = RLImage(photo_path, width=2.5*cm, height=2.5*cm)
            img.hAlign = 'RIGHT'
            name_block = [
                Paragraph(full_name, name_style),
                Paragraph(role, role_style),
                Paragraph(' | '.join(contact_parts), contact_style),
                Paragraph(' | '.join(link_parts), contact_style) if link_parts else Spacer(1,1),
            ]
            tbl = Table([[name_block, img]], colWidths=['*', 2.8*cm])
            tbl.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('ALIGN',  (1,0), (1,0),  'RIGHT'),
            ]))
            story.append(tbl)
        except Exception:
            story.append(Paragraph(full_name, name_style))
            story.append(Paragraph(role, role_style))
            story.append(Paragraph(' | '.join(contact_parts), contact_style))
    else:
        story.append(Paragraph(full_name, name_style))
        story.append(Paragraph(role, role_style))
        story.append(Paragraph(' | '.join(contact_parts), contact_style))
        if link_parts:
            story.append(Paragraph(' | '.join(link_parts), contact_style))

    story.append(HRFlowable(width='100%', thickness=1.5, color=teal, spaceAfter=8))

    def section_header(title):
        story.append(Paragraph(title.upper(), section_style))
        story.append(HRFlowable(width='100%', thickness=0.5, color=line, spaceAfter=4))

    # ── ABOUT ────────────────────────────────────────────────────────────────────
    about = data.get('about', '').strip()
    if about:
        section_header('Professional Summary')
        story.append(Paragraph(about, body_style))

    # ── SKILLS ───────────────────────────────────────────────────────────────────
    skills = data.get('skills', {})
    if any(skills.values() if isinstance(skills, dict) else [skills]):
        section_header('Technical Skills')
        if isinstance(skills, dict):
            rows = []
            labels = {
                'languages':  'Languages',
                'tools':      'Tools & Frameworks',
                'databases':  'Databases',
                'core':       'Core Subjects',
            }
            for key, label in labels.items():
                val = skills.get(key, '').strip()
                if val:
                    rows.append([
                        Paragraph(f'<b>{label}:</b>', body_style),
                        Paragraph(val, body_style)
                    ])
            if rows:
                skill_tbl = Table(rows, colWidths=[3.5*cm, '*'])
                skill_tbl.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING',    (0,0), (-1,-1), 2),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 2),
                ]))
                story.append(skill_tbl)
        else:
            story.append(Paragraph(str(skills), body_style))

    # ── EDUCATION ────────────────────────────────────────────────────────────────
    education = data.get('education', [])
    if education:
        section_header('Education')
        for edu in education:
            if not isinstance(edu, dict): continue
            deg    = edu.get('degree', '')
            school = edu.get('school', '')
            year   = edu.get('year', '')
            gpa    = edu.get('gpa', '')
            right  = f"{year}  {gpa}".strip()
            row = Table(
                [[Paragraph(f'<b>{deg}</b>', body_style),
                  Paragraph(right, small_style)]],
                colWidths=['*', 4*cm]
            )
            row.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT'),
                                     ('TOPPADDING', (0,0), (-1,-1), 1),
                                     ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))
            story.append(row)
            if school:
                story.append(Paragraph(school, small_style))
            story.append(Spacer(1, 3))

    # ── PROJECTS ─────────────────────────────────────────────────────────────────
    projects = data.get('projects', [])
    if projects:
        section_header('Projects')
        for proj in projects:
            if not isinstance(proj, dict): continue
            name  = proj.get('name', '')
            tech  = proj.get('tech', '')
            desc  = proj.get('description', '')
            link  = proj.get('link', '')
            header_txt = f'<b>{name}</b>'
            if tech: header_txt += f'  <font color="#888888" size="8">| {tech}</font>'
            story.append(Paragraph(header_txt, body_style))
            if desc:
                for line_txt in desc.split('\n'):
                    line_txt = line_txt.strip()
                    if line_txt:
                        story.append(Paragraph(f'• {line_txt}', bullet_style))
            if link:
                story.append(Paragraph(f'<font color="#00b4d8">🔗 {link}</font>', small_style))
            story.append(Spacer(1, 4))

    # ── CERTIFICATIONS ───────────────────────────────────────────────────────────
    certs = data.get('certifications', [])
    if certs:
        section_header('Certifications')
        for cert in certs:
            if not isinstance(cert, dict): continue
            n    = cert.get('name', '')
            issuer = cert.get('issuer', '')
            year = cert.get('year', '')
            txt  = f'<b>{n}</b>'
            if issuer: txt += f' — {issuer}'
            row = Table(
                [[Paragraph(txt, body_style), Paragraph(year, small_style)]],
                colWidths=['*', 3*cm]
            )
            row.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT'),
                                     ('VALIGN', (0,0), (-1,-1), 'TOP'),
                                     ('TOPPADDING', (0,0), (-1,-1), 1),
                                     ('BOTTOMPADDING', (0,0), (-1,-1), 1)]))
            story.append(row)

    # ── ACHIEVEMENTS ─────────────────────────────────────────────────────────────
    achievements = data.get('achievements', '').strip()
    if achievements:
        section_header('Achievements')
        for line_txt in achievements.split('\n'):
            line_txt = line_txt.strip()
            if line_txt:
                story.append(Paragraph(f'• {line_txt}', bullet_style))

    # ── HOBBIES ──────────────────────────────────────────────────────────────────
    hobbies = data.get('hobbies', '').strip()
    if hobbies:
        section_header('Interests & Hobbies')
        story.append(Paragraph(hobbies, body_style))

    doc.build(story)
    return buf.getvalue()

# ─── AI Suggestion (simple rule-based) ────────────────────────────────────────

@app.route('/api/suggest-summary', methods=['POST'])
@login_required
def suggest_summary():
    payload = request.get_json(force=True)
    role   = payload.get('role', 'Software Developer')
    skills = payload.get('skills', '')
    name   = payload.get('name', 'Student')

    templates = [
        f"Motivated {role} and enthusiastic Computer Science student with hands-on experience in "
        f"{skills or 'full-stack development'}. Passionate about building scalable, user-centric "
        f"applications and eager to contribute to innovative tech teams. Strong foundation in "
        f"data structures, algorithms, and modern software development practices.",

        f"Dedicated {role} seeking to leverage technical expertise in {skills or 'software development'} "
        f"to create impactful solutions. Quick learner with strong problem-solving skills, collaborative "
        f"team player, and a commitment to writing clean, maintainable code.",

        f"Passionate {role} with experience in {skills or 'programming and development'}. "
        f"Proven ability to deliver projects on time with attention to detail and quality. "
        f"Seeking an opportunity to grow professionally while contributing meaningfully to "
        f"organizational goals.",
    ]
    suggestion = random.choice(templates)
    return jsonify({'success': True, 'suggestion': suggestion})

# ─── Serve uploaded files ──────────────────────────────────────────────────────

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    print("✅ HireSmart AI started at http://localhost:5000")
    print("⚠️  Configure EMAIL_USER and EMAIL_PASSWORD env vars for real email delivery.")
    print("⚠️  OTPs will be printed to console in dev mode if email is not configured.")
    app.run(debug=True, host='0.0.0.0', port=5000)