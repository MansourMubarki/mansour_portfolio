\
import os
import json
import argparse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, current_user, logout_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ---------- Config ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_PATH, exist_ok=True)

def create_app():
    app = Flask(__name__, instance_path=INSTANCE_PATH, instance_relative_config=True)
    # Secrets from env
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'change-me-please')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(INSTANCE_PATH, 'site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

    return app

app = create_app()
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------- Models ----------
class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<Section {self.slug}>"

class ContentBlock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    title = db.Column(db.String(200))
    subtitle = db.Column(db.String(300))
    body = db.Column(db.Text)
    image = db.Column(db.String(300))
    icon = db.Column(db.String(100))
    button_text = db.Column(db.String(100))
    button_url = db.Column(db.String(300))
    layout = db.Column(db.String(50), default="text-left-image-right")
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    section = db.relationship('Section', backref=db.backref('blocks', lazy=True, cascade="all, delete-orphan"))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.String(200))
    image = db.Column(db.String(300))
    link = db.Column(db.String(300))
    code_link = db.Column(db.String(300))
    is_published = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

# ---------- Helpers ----------
def get_setting(key, default=None):
    s = Setting.query.filter_by(key=key).first()
    return s.value if s else default

def set_setting(key, value):
    s = Setting.query.filter_by(key=key).first()
    if not s:
        s = Setting(key=key, value=value)
        db.session.add(s)
    else:
        s.value = value
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {"png", "jpg", "jpeg", "gif", "webp", "svg"}

# ---------- CLI init ----------
def init_data():
    db.create_all()
    # Seed settings
    defaults = {
        "site_name": "Mansour Mubarki",
        "theme_primary": "#0ea5e9",  # sky-500
        "hero_title": "مصوّر، مطوّر، ورائد أعمال رقمي",
        "hero_subtitle": "أصنع تجارب بصرية و حلول تقنية تربط الإبداع بالنتيجة.",
        "hero_button_text": "تواصل معي",
        "hero_button_url": "#contact",
    }
    for k, v in defaults.items():
        if not Setting.query.filter_by(key=k).first():
            db.session.add(Setting(key=k, value=v))

    # Seed sections
    sections = [
        ("البطل", "hero", 0),
        ("نبذة", "about", 1),
        ("الخدمات", "services", 2),
        ("الأعمال", "portfolio", 3),
        ("تواصل", "contact", 4),
    ]
    for name, slug, order in sections:
        if not Section.query.filter_by(slug=slug).first():
            db.session.add(Section(name=name, slug=slug, sort_order=order))

    # Seed blocks (about + services samples)
    about = Section.query.filter_by(slug="about").first()
    services = Section.query.filter_by(slug="services").first()
    if about and not about.blocks:
        db.session.add(ContentBlock(
            section=about,
            title="منصور مباركي",
            subtitle="مشرف إعلامي | مطوّر | صانع محتوى",
            body="أساعد الجهات التعليمية والتجارية على تحويل أفكارهم إلى منتجات رقمية وإعلانات فعّالة.",
            layout="text-center",
            sort_order=0
        ))
    if services and not services.blocks:
        demo_services = [
            ("إنتاج مرئي", "لقطات سينمائية وإعلانات قصيرة", "camera"),
            ("هوية بصرية", "شعارات، بوسترات، قوالب سوشيال", "palette"),
            ("مواقع وتطبيقات", "Flask, Bubble, Docker, Fly.io", "code"),
        ]
        for i, (t, b, ic) in enumerate(demo_services):
            db.session.add(ContentBlock(
                section=services, title=t, body=b, icon=ic, layout="card", sort_order=i
            ))

    # Seed a demo project
    if Project.query.count() == 0:
        db.session.add(Project(
            title="SEU Scheduler",
            description="منصة ذكية للجداول الدراسية لطلاب الجامعة السعودية الإلكترونية.",
            tags="Flask,SQLite,Fly.io",
            image="",
            link="#",
            code_link="#",
            sort_order=0
        ))

    # Create admin user if env vars provided and no user exists
    if User.query.count() == 0:
        username = os.getenv("ADMIN_USERNAME")
        password = os.getenv("ADMIN_PASSWORD")
        if username and password:
            u = User(username=username)
            u.set_password(password)
            db.session.add(u)

    db.session.commit()

# ---------- Auth ----------
@app.route("/setup", methods=["GET", "POST"])
def setup():
    if User.query.count() > 0:
        return redirect(url_for("login"))
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        if not username or not password:
            flash("الرجاء تعبئة البيانات", "danger")
        else:
            u = User(username=username)
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("تم إنشاء حساب الإدمن. سجل الدخول الآن.", "success")
            return redirect(url_for("login"))
    return render_template("admin/setup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin_dashboard"))
        flash("بيانات الدخول غير صحيحة", "danger")
    return render_template("admin/login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("تم تسجيل الخروج.", "info")
    return redirect(url_for("login"))

# ---------- Admin ----------
@app.route("/admin")
@login_required
def admin_dashboard():
    stats = {
        "sections": Section.query.count(),
        "blocks": ContentBlock.query.count(),
        "projects": Project.query.count()
    }
    return render_template("admin/dashboard.html", stats=stats)

@app.route("/admin/sections", methods=["GET", "POST"])
@login_required
def admin_sections():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        slug = request.form.get("slug","").strip()
        order = int(request.form.get("sort_order","0"))
        if name and slug:
            if Section.query.filter_by(slug=slug).first():
                flash("الـ slug مستخدم من قبل.", "danger")
            else:
                db.session.add(Section(name=name, slug=slug, sort_order=order))
                db.session.commit()
                flash("تمت إضافة القسم.", "success")
        return redirect(url_for("admin_sections"))
    sections = Section.query.order_by(Section.sort_order.asc()).all()
    return render_template("admin/sections.html", sections=sections)

@app.route("/admin/sections/<int:section_id>/toggle")
@login_required
def toggle_section(section_id):
    s = db.session.get(Section, section_id) or abort(404)
    s.is_enabled = not s.is_enabled
    db.session.commit()
    return redirect(url_for("admin_sections"))

@app.route("/admin/sections/<int:section_id>/delete")
@login_required
def delete_section(section_id):
    s = db.session.get(Section, section_id) or abort(404)
    db.session.delete(s)
    db.session.commit()
    flash("تم حذف القسم.", "info")
    return redirect(url_for("admin_sections"))

@app.route("/admin/blocks/<int:section_id>", methods=["GET", "POST"])
@login_required
def admin_blocks(section_id):
    section = db.session.get(Section, section_id) or abort(404)
    if request.method == "POST":
        data = {
            "title": request.form.get("title",""),
            "subtitle": request.form.get("subtitle",""),
            "body": request.form.get("body",""),
            "icon": request.form.get("icon",""),
            "button_text": request.form.get("button_text",""),
            "button_url": request.form.get("button_url",""),
            "layout": request.form.get("layout","card"),
            "sort_order": int(request.form.get("sort_order","0")),
            "is_published": request.form.get("is_published","on") == "on",
            "image": ""
        }
        # File upload
        f = request.files.get("image")
        if f and f.filename and allowed_file(f.filename):
            fname = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + secure_filename(f.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            f.save(save_path)
            data["image"] = save_path
        cb = ContentBlock(section=section, **data)
        db.session.add(cb)
        db.session.commit()
        flash("تمت إضافة المحتوى.", "success")
        return redirect(url_for("admin_blocks", section_id=section.id))
    blocks = ContentBlock.query.filter_by(section_id=section.id).order_by(ContentBlock.sort_order.asc()).all()
    return render_template("admin/blocks.html", section=section, blocks=blocks)

@app.route("/admin/blocks/<int:block_id>/delete")
@login_required
def delete_block(block_id):
    b = db.session.get(ContentBlock, block_id) or abort(404)
    sid = b.section_id
    db.session.delete(b)
    db.session.commit()
    flash("تم حذف المحتوى.", "info")
    return redirect(url_for("admin_blocks", section_id=sid))

@app.route("/admin/projects", methods=["GET", "POST"])
@login_required
def admin_projects():
    if request.method == "POST":
        data = {
            "title": request.form.get("title",""),
            "description": request.form.get("description",""),
            "tags": request.form.get("tags",""),
            "link": request.form.get("link",""),
            "code_link": request.form.get("code_link",""),
            "sort_order": int(request.form.get("sort_order","0")),
            "is_published": request.form.get("is_published","on") == "on",
            "image": ""
        }
        f = request.files.get("image")
        if f and f.filename and allowed_file(f.filename):
            fname = datetime.utcnow().strftime("%Y%m%d_%H%M%S_") + secure_filename(f.filename)
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], fname)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            f.save(save_path)
            data["image"] = save_path
        prj = Project(**data)
        db.session.add(prj)
        db.session.commit()
        flash("تمت إضافة المشروع.", "success")
        return redirect(url_for("admin_projects"))
    projects = Project.query.order_by(Project.sort_order.asc()).all()
    return render_template("admin/projects.html", projects=projects)

@app.route("/admin/projects/<int:project_id>/delete")
@login_required
def delete_project(project_id):
    p = db.session.get(Project, project_id) or abort(404)
    db.session.delete(p)
    db.session.commit()
    flash("تم حذف المشروع.", "info")
    return redirect(url_for("admin_projects"))

@app.route("/admin/settings", methods=["GET", "POST"])
@login_required
def admin_settings():
    keys = ["site_name", "theme_primary", "hero_title", "hero_subtitle", "hero_button_text", "hero_button_url",
            "email", "whatsapp", "x_url", "instagram_url", "tiktok_url"]
    if request.method == "POST":
        for k in keys:
            set_setting(k, request.form.get(k, ""))
        # Change admin password
        new_user = request.form.get("admin_username","").strip()
        new_pw = request.form.get("admin_password","").strip()
        if new_user:
            current_user.username = new_user
        if new_pw:
            current_user.set_password(new_pw)
        db.session.commit()
        flash("تم حفظ الإعدادات.", "success")
        return redirect(url_for("admin_settings"))
    settings = {k: get_setting(k, "") for k in keys}
    return render_template("admin/settings.html", settings=settings)

@app.route("/admin/export")
@login_required
def export_json():
    data = {
        "settings": {s.key: s.value for s in Setting.query.all()},
        "sections": [],
        "projects": []
    }
    for s in Section.query.order_by(Section.sort_order.asc()).all():
        data["sections"].append({
            "id": s.id, "name": s.name, "slug": s.slug, "is_enabled": s.is_enabled, "sort_order": s.sort_order,
            "blocks": [
                {
                    "id": b.id, "title": b.title, "subtitle": b.subtitle, "body": b.body,
                    "image": b.image, "icon": b.icon, "button_text": b.button_text, "button_url": b.button_url,
                    "layout": b.layout, "is_published": b.is_published, "sort_order": b.sort_order
                } for b in ContentBlock.query.filter_by(section_id=s.id).order_by(ContentBlock.sort_order.asc()).all()
            ]
        })
    for p in Project.query.order_by(Project.sort_order.asc()).all():
        data["projects"].append({
            "id": p.id, "title": p.title, "description": p.description, "tags": p.tags,
            "image": p.image, "link": p.link, "code_link": p.code_link,
            "is_published": p.is_published, "sort_order": p.sort_order
        })
    return jsonify(data)

@app.route("/admin/import", methods=["POST"])
@login_required
def import_json():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "JSON غير صالح"}), 400
    # Wipe and import
    ContentBlock.query.delete()
    Project.query.delete()
    Section.query.delete()
    db.session.commit()

    for k, v in data.get("settings", {}).items():
        set_setting(k, v)

    id_map = {}
    for s in data.get("sections", []):
        sx = Section(name=s.get("name",""), slug=s.get("slug",""), is_enabled=s.get("is_enabled", True), sort_order=s.get("sort_order",0))
        db.session.add(sx); db.session.flush()
        id_map[s.get("id")] = sx.id
        for b in s.get("blocks", []):
            db.session.add(ContentBlock(
                section_id=sx.id,
                title=b.get("title",""), subtitle=b.get("subtitle",""), body=b.get("body",""),
                image=b.get("image",""), icon=b.get("icon",""),
                button_text=b.get("button_text",""), button_url=b.get("button_url",""),
                layout=b.get("layout","card"), is_published=b.get("is_published", True),
                sort_order=b.get("sort_order", 0)
            ))
    for p in data.get("projects", []):
        db.session.add(Project(
            title=p.get("title",""), description=p.get("description",""), tags=p.get("tags",""),
            image=p.get("image",""), link=p.get("link",""), code_link=p.get("code_link",""),
            is_published=p.get("is_published", True), sort_order=p.get("sort_order",0)
        ))
    db.session.commit()
    return jsonify({"status": "ok"})

# ---------- Public API ----------
@app.route("/api/sections")
def api_sections():
    out = []
    for s in Section.query.filter_by(is_enabled=True).order_by(Section.sort_order.asc()).all():
        blocks = ContentBlock.query.filter_by(section_id=s.id, is_published=True).order_by(ContentBlock.sort_order.asc()).all()
        out.append({
            "name": s.name, "slug": s.slug, "blocks": [
                {
                    "title": b.title, "subtitle": b.subtitle, "body": b.body,
                    "image": b.image, "icon": b.icon, "button_text": b.button_text, "button_url": b.button_url, "layout": b.layout
                } for b in blocks
            ]
        })
    return jsonify(out)

@app.route("/api/projects")
def api_projects():
    prjs = Project.query.filter_by(is_published=True).order_by(Project.sort_order.asc()).all()
    return jsonify([
        {
            "title": p.title, "description": p.description, "tags": p.tags,
            "image": p.image, "link": p.link, "code_link": p.code_link
        } for p in prjs
    ])

# ---------- Public Views ----------
@app.route("/")
def index():
    sections = Section.query.filter_by(is_enabled=True).order_by(Section.sort_order.asc()).all()
    blocks_by_section = {s.slug: ContentBlock.query.filter_by(section_id=s.id, is_published=True).order_by(ContentBlock.sort_order.asc()).all() for s in sections}
    projects = Project.query.filter_by(is_published=True).order_by(Project.sort_order.asc()).all()
    theme_primary = get_setting("theme_primary", "#0ea5e9")
    return render_template("index.html",
                           sections=sections,
                           blocks=blocks_by_section,
                           projects=projects,
                           theme_primary=theme_primary,
                           get_setting=get_setting)

# ---------- Uploads ----------
@app.route("/uploads/<path:filename>")
def uploads(filename):
    return send_from_directory(os.path.join("static","uploads"), filename)

# ---------- Main ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--init", action="store_true", help="Initialize database with seed data")
    args = parser.parse_args()
    with app.app_context():
        if args.init:
            init_data()
        else:
            db.create_all()
    app.run(debug=True)
