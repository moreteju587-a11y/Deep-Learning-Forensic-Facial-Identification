import os
from functools import wraps
import uuid
import secrets

from dotenv import load_dotenv
load_dotenv()  # reads a local .env file if present (see .env.example)

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_from_directory
)

from models import db, User, Case, bcrypt
from image_generator import generate_face as sd_generate_face
from match_face import find_best_match
from flask import send_file, session
import requests as http_requests

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor


import datetime


app = Flask(__name__)


# ---------------- CONFIGURATION ----------------
# All secrets/credentials now come from environment variables (see .env.example).
# A random key is generated as a fallback ONLY for local dev convenience — set
# SECRET_KEY yourself for anything beyond your own machine, since a key that
# changes on every restart will log everyone out each time you restart the app.

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
if not os.environ.get('SECRET_KEY'):
    print("⚠️  SECRET_KEY not set in environment — using a temporary random key "
          "for this run only. Set SECRET_KEY in your .env for production.")

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'mysql+mysqlconnector://root:@127.0.0.1:3306/thirdeye_db'
)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SKETCH_PARTS_FOLDER'] = 'static/sketch_parts'

app.config['ALLOWED_UPLOAD_EXTENSIONS'] = {'.png', '.jpg', '.jpeg', '.webp'}
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8 MB upload cap

ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')



# ---------------- INITIALIZE EXTENSIONS ----------------

db.init_app(app)
bcrypt.init_app(app)
# ---------------- CREATE DATABASE TABLES ----------------

with app.app_context():
    db.create_all()

    # Create default admin user if it doesn't exist. Set ADMIN_PASSWORD in your
    # .env before first run; otherwise a random one-time password is generated
    # and printed to the console so it's never a guessable default.
    if not User.query.filter_by(username="admin").first():
        admin_password = os.environ.get('ADMIN_PASSWORD')
        generated = False
        if not admin_password:
            admin_password = secrets.token_urlsafe(9)
            generated = True

        admin = User(
            username="admin",
            password=admin_password,
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

        if generated:
            print(f"✅ Admin user created — username: admin | password: {admin_password}")
            print("   (Set ADMIN_PASSWORD in .env to choose your own instead.)")
        else:
            print("✅ Admin user created with the password from ADMIN_PASSWORD.")



# ---------------- LOGIN REQUIRED ----------------

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if 'user_id' not in session:
            flash(
                'Please log in to access this page.',
                'danger'
            )
            return redirect(url_for('login'))

        return f(*args, **kwargs)

    return decorated_function



# ---------------- DATABASE INIT ----------------

@app.cli.command("init-db")
def init_db_command():

    db.create_all()

    print("Database initialized.")



# ---------------- HOME ----------------

@app.route('/')
def home():

    return render_template('home.html')



# ---------------- LOGIN ----------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']


        user = User.query.filter_by(
            username=username
        ).first()


        if user and user.check_password(password):

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role


            flash(
                f'Welcome, {user.username}!',
                'success'
            )


            return redirect(
                url_for('dashboard')
            )


        else:

            flash(
                'Invalid username or password.',
                'danger'
            )


    return render_template('login.html')



# ---------------- REGISTER ----------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip() or None
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return redirect(url_for('register'))

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(
            username=username
        ).first()


        if existing_user:

            flash(
                'Username already exists.',
                'danger'
            )

            return redirect(
                url_for('register')
            )

        if email and User.query.filter_by(email=email).first():
            flash('An account with that email already exists.', 'danger')
            return redirect(url_for('register'))

        new_user = User(
            username=username,
            password=password,
            email=email
        )


        db.session.add(new_user)

        db.session.commit()


        flash(
            'Account created successfully!',
            'success'
        )


        return redirect(
            url_for('login')
        )


    return render_template('register.html')



# ---------------- LOGOUT ----------------

@app.route('/logout')
def logout():

    session.clear()


    flash(
        'You have been logged out.',
        'info'
    )


    return redirect(
        url_for('home')
    )



# ---------------- DASHBOARD ----------------

@app.route('/dashboard')
@login_required
def dashboard():

    user_cases = (
        Case.query
        .filter_by(user_id=session['user_id'])
        .order_by(Case.created_at.desc())
        .all()
    )

    matched = [c for c in user_cases if c.similarity is not None]

    stats = {
        'total_cases': len(user_cases),
        'matches_found': len(matched),
        'avg_similarity': round(sum(c.similarity for c in matched) / len(matched), 1) if matched else '—',
        'reports': len(matched),  # a report can be generated for every match
    }

    cases = [
        {
            'sketch_image': None,
            'matched_image': (
                url_for('criminal_database', filename=c.matched_image) if c.matched_image else None
            ),
            'matched_name': c.matched_name,
            'similarity': round(c.similarity) if c.similarity is not None else None,
            'created_at': c.created_at.strftime('%d %b %Y'),
            'report_url': None,  # reports are generated on demand from the recognition page
        }
        for c in user_cases[:10]
    ]

    return render_template('dashboard.html', stats=stats, cases=cases)


# ---------------- SKETCH CONSTRUCTOR ----------------

@app.route('/sketch')
@login_required
def sketch_constructor():

    parts = {}

    base_path = app.config['SKETCH_PARTS_FOLDER']


    if os.path.exists(base_path):

        for category in sorted(
            os.listdir(base_path)
        ):

            cat_path = os.path.join(
                base_path,
                category
            )


            if os.path.isdir(cat_path):

                files = sorted(
                    [
                        f"{category}/{f}"
                        for f in os.listdir(cat_path)
                        if f.lower().endswith(
                            (
                                '.png',
                                '.jpg',
                                '.jpeg',
                                '.webp'
                            )
                        )
                    ]
                )


                if files:

                    parts[category] = files


    return render_template(
        'sketch.html',
        parts=parts
    )



# ---------------- VOICE ANSWER INTERPRETATION (AI FALLBACK) ----------------
# Called from sketch.html when simple keyword matching can't map what the
# witness said to one of the allowed feature labels. Runs server-side so the
# Anthropic API key is never exposed to the browser.

@app.route('/api/interpret-feature', methods=['POST'])
@login_required
def interpret_feature():

    data = request.get_json(silent=True) or {}
    raw_text = (data.get('rawText') or '').strip()
    feature_label = data.get('featureLabel', 'feature')
    options = data.get('options') or []

    if not raw_text or not options:
        return jsonify({'label': 'Unknown'})

    if not ANTHROPIC_API_KEY:
        # Feature works without this key too — keyword matching on the client
        # handles most answers. This is only the fallback for unusual phrasing.
        return jsonify({'label': 'Unknown'})

    system_prompt = f"""You are an expert forensic facial feature interpreter.

Speech input:
"{raw_text}"

Allowed values:
- {chr(10).join('- ' + o for o in options)}

Rules:
1. Fix only speech recognition mistakes.
2. Return exactly one allowed value.
3. Never create new labels.
4. If uncertain return Unknown.

Return JSON only:
{{"label": "value"}}"""

    try:
        resp = http_requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 80,
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": f"Feature: {feature_label}\n\nWitness said:\n\"{raw_text}\""}
                ],
            },
            timeout=15,
        )
        resp.raise_for_status()
        content = resp.json().get('content', [])
        raw = ''.join(block.get('text', '') for block in content)

        import json as _json
        cleaned = raw.replace('```json', '').replace('```', '').strip()
        parsed = _json.loads(cleaned)
        label = parsed.get('label', 'Unknown')

        if label not in options:
            label = 'Unknown'

        return jsonify({'label': label})

    except Exception as e:
        print(f"interpret-feature error: {e}")
        return jsonify({'label': 'Unknown'})


# ---------------- AI FACE GENERATION ----------------

@app.route('/generate-face', methods=['POST'])
@login_required
def generate_face():

    try:

        data = request.get_json()

        if not data or 'features' not in data:
            return jsonify({
                'error': 'No features provided'
            }), 400

        features = data['features']

        prompt = build_face_prompt(features)

        image_path = sd_generate_face(prompt)

        return jsonify({
            "success": True,
            "image": "/" + image_path.replace("\\", "/"),
            "prompt": prompt
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500


def build_face_prompt(features):

    gender = features.get(
        "gender",
        "person"
    )


    parts = []


    mapping = {

        'skin': '{} skin tone',
        'head': '{} face shape',
        'hair': '{} hairstyle',
        'eyebrows': '{} eyebrows',
        'eyes': '{} eyes',
        'nose': '{} nose',
        'lips': '{} lips',
        'mustach': '{} facial hair'

    }


    for key, template in mapping.items():

        value = features.get(key)


        if value and value != "Skipped":

            parts.append(
                template.format(value)
            )


    description = ", ".join(parts)


    return f"""
Ultra realistic forensic police portrait of a {gender}.

Features:
{description}

Front facing.
Neutral facial expression.
Natural skin texture.
Professional DSLR portrait.
Passport style.
White background.
Highly detailed.
"""


# ---------------- FACE RECOGNITION ----------------

@app.route('/recognition', methods=['GET', 'POST'])
@login_required
def recognition():

    results = None
    uploaded_filename = None

    if request.method == "POST":

        if "sketch" not in request.files:
            flash("Please select an image.", "warning")
            return redirect(request.url)

        file = request.files["sketch"]

        if file.filename == "":
            flash("Please select an image.", "warning")
            return redirect(request.url)

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in app.config['ALLOWED_UPLOAD_EXTENSIONS']:
            flash("Unsupported file type. Please upload a PNG, JPG or WEBP image.", "danger")
            return redirect(request.url)

        UPLOAD_FOLDER = os.path.join("static", "uploads")
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        filename = f"{uuid.uuid4().hex}.png"
        upload_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(upload_path)

        uploaded_filename = filename

        best_match = find_best_match(upload_path)

        if best_match:
            results = [best_match]

            session["report"] = {
                "name": best_match["name"],
                "age": best_match["age"],
                "crime": best_match["crime"],
                "last_seen": best_match["last_seen"],
                "similarity": best_match["similarity"],
                "criminal_image": best_match["image"],
                "uploaded_image": upload_path
            }

            case = Case(
                user_id=session['user_id'],
                uploaded_image=uploaded_filename,
                matched_name=best_match["name"],
                matched_image=best_match["image"],
                similarity=best_match["similarity"],
                crime=best_match["crime"],
                last_seen=best_match["last_seen"],
            )
        else:
            results = []
            case = Case(
                user_id=session['user_id'],
                uploaded_image=uploaded_filename,
                similarity=None,
            )

        db.session.add(case)
        db.session.commit()

    return render_template(
        "recognition.html",
        results=results,
        uploaded_filename=uploaded_filename
    )
# ---------------- CRIMINAL DATABASE IMAGE SERVING ----------------

@app.route('/criminal_database/<filename>')
@login_required
def criminal_database(filename):

    return send_from_directory(
        'synthetic_database',
        filename
    )
    # ---------------- GENERATE REPORT ----------------

@app.route("/generate-report")
@login_required
def generate_report():

    report = session.get("report")

    if report is None:
        flash("No investigation report found.", "warning")
        return redirect(url_for("recognition"))

    try:
        reports_dir = os.path.join(app.root_path, "static", "reports")
        os.makedirs(reports_dir, exist_ok=True)

        unique_name = f"Investigation_Report_{uuid.uuid4().hex}.pdf"
        pdf_path = os.path.join(reports_dir, unique_name)

        doc = SimpleDocTemplate(
            pdf_path,
            rightMargin=25,
            leftMargin=25,
            topMargin=15,
            bottomMargin=12
        )

        styles = getSampleStyleSheet()

        title = ParagraphStyle(
            "CompactTitle",
            parent=styles["Title"],
            fontSize=16,
            leading=19,
            spaceAfter=0,
            alignment=TA_CENTER,
            textColor=HexColor("#003366")
        )

        heading = ParagraphStyle(
            "CompactHeading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=13,
            spaceBefore=0,
            spaceAfter=4,
            textColor=HexColor("#003366")
        )

        normal = ParagraphStyle(
            "CompactNormal",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12
        )

        elements = []

        # ---------------- TITLE ----------------
        elements.append(Paragraph("FORENSIC FACIAL IDENTIFICATION REPORT", title))
        elements.append(Spacer(1, 10))

        # ---------------- REPORT DETAILS ----------------
        now = datetime.datetime.now()
        report_id = f"FFI-{now.strftime('%Y%m%d%H%M%S')}"
        case_id = f"CASE-{now.strftime('%Y%m%d%H%M%S')}"
        officer = session.get("username", "Administrator")

        report_info = Table([
            ["Report ID", report_id],
            ["Case ID", case_id],
            ["Generated", now.strftime("%d-%m-%Y %I:%M %p")],
            ["Officer", officer]
        ], colWidths=[120, 250])
        report_info.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#DCEEFF")),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
        ]))
        elements.append(report_info)
        elements.append(Spacer(1, 8))

        # ---------------- SUSPECT DETAILS ----------------
        elements.append(Paragraph("<b>SUSPECT DETAILS</b>", heading))

        suspect = Table([
            ["Name", report["name"]],
            ["Age", report["age"]],
            ["Crime", report["crime"]],
            ["Last Seen", report["last_seen"]],
            ["Similarity", str(report["similarity"]) + " %"]
        ], colWidths=[120, 250])
        suspect.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (0, -1), HexColor("#EAF4FF")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
        ]))
        elements.append(suspect)
        elements.append(Spacer(1, 8))

        # ---------------- IMAGE SECTION ----------------
        elements.append(Paragraph("<b>IMAGE COMPARISON</b>", heading))

        uploaded_path = os.path.join(app.root_path, report["uploaded_image"])
        criminal_path = os.path.join(app.root_path, "synthetic_database", report["criminal_image"])

        # Fail with a clear, readable message instead of a blank 500 error
        if not os.path.isfile(uploaded_path):
            flash(f"Uploaded image missing on disk: {uploaded_path}", "danger")
            return redirect(url_for("recognition"))

        if not os.path.isfile(criminal_path):
            flash(f"Matched criminal image missing on disk: {criminal_path}", "danger")
            return redirect(url_for("recognition"))

        uploaded_img = Image(uploaded_path, width=1.3 * inch, height=1.5 * inch)
        criminal_img = Image(criminal_path, width=1.3 * inch, height=1.5 * inch)

        image_table = Table([
            ["Uploaded Suspect", "Matched Criminal"],
            [uploaded_img, criminal_img]
        ], colWidths=[220, 220])
        image_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#DCEEFF")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)
        ]))
        elements.append(image_table)
        elements.append(Spacer(1, 4))

        # ---------------- SUMMARY ----------------
        elements.append(Paragraph("<b>INVESTIGATION SUMMARY</b>", heading))
        elements.append(Spacer(1, 4))

        summary = f"""
        The uploaded suspect face was analysed using the AI-powered
        Forensic Facial Identification System. A matching criminal record was identified.<br/>
        Match Found : {report['name']} &nbsp;|&nbsp;
        Similarity : {report['similarity']} % &nbsp;|&nbsp;
        Crime : {report['crime']} &nbsp;|&nbsp;
        Last Seen : {report['last_seen']}<br/><br/>

        <b>Conclusion:</b> The facial recognition system identified the above individual
        as the closest match in the criminal database.<br/>

        <b>Recommendation:</b> The suspect should undergo fingerprint, iris or DNA
        verification before legal proceedings.
        """
        elements.append(Paragraph(summary, normal))
        elements.append(Spacer(1, 4))

        # ---------------- SIGNATURE ----------------
        signature = Table([
            ["Investigating Officer"],
            ["____________________________"],
            ["Digital Signature"]
        ], colWidths=[220])
        signature.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica")
        ]))
        elements.append(signature)
        elements.append(Spacer(1, 4))

        footer = Paragraph(
            "<font size='8' color='grey'>AI-Based Forensic Face Recognition System</font>",
            normal
        )
        elements.append(footer)

        # ---------------- CREATE PDF ----------------
        doc.build(elements)

        return send_file(
            pdf_path,
            as_attachment=(request.args.get("mode") != "view"),
            download_name="Investigation_Report.pdf",
            mimetype="application/pdf",
            conditional=False,
            max_age=0
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Could not generate report: {e}", "danger")
        return redirect(url_for("recognition"))
# ---------------- ERROR PAGES ----------------

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False,
        threaded=True
    )

