# Mansour Portfolio (Flask)

موقع بورتفوليو عربي مع **لوحة تحكم** لإدارة الأقسام والمحتوى والتصاميم، مبني بـ Flask + SQLite.

## الميزات
- أقسام ديناميكية: البطل (Hero) – نبذة – خدمات – الأعمال – تواصل.
- إدارة كاملة من لوحة تحكم (إضافة/تعديل/حذف وترتيب).
- رفع صور إلى `static/uploads`.
- سمة ألوان قابلة للتخصيص (CSS variables).
- دعم RTL وخط Cairo.
- زر لوحة تحكم مخفي يظهر باختصار لوحة المفاتيح **Shift + A**.
- تصدير/استيراد نسخة JSON من البيانات.
- واجهات API بسيطة (`/api/sections` و`/api/projects`).

## التشغيل محليًا
```bash
python -m venv .venv
source .venv/bin/activate  # على ويندوز: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_APP=app.py
export FLASK_ENV=development
# (اختياري) تحميل متغيرات .env يدويًا
python app.py --init
flask run
```

أول مرة: افتح `/setup` لإنشاء مستخدم الإدمن.

## النشر على Fly.io (مختصر)
1) ثبّت CLI: `flyctl auth signup` ثم `flyctl launch`
2) اختر اسم التطبيق، وحدد Python.
3) تأكد من وجود ملف `Dockerfile` و `fly.toml` (مرفقة هنا).
4) عيّن المتغيرات الحساسة:
```bash
flyctl secrets set FLASK_SECRET_KEY=... ADMIN_USERNAME=... ADMIN_PASSWORD=...
```
5) انشر: `flyctl deploy`

## مفاتيح مخفية
- زر الإدمن لا يظهر إلا عند الضغط على **Shift + A**.
