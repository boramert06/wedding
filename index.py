from flask import Flask, request, redirect, url_for, render_template, send_from_directory, make_response
import os
from werkzeug.utils import secure_filename
import uuid
import io
import zipfile
import qrcode
from flask import send_file
import psycopg2
import psycopg2.extras

UPLOAD_FOLDER = 'uploads'
AUDIO_FOLDER = 'audio_uploads'
DB_HOST = 'localhost'
DB_NAME = 'weddingphoto'
DB_USER = 'postgres'
DB_PASSWORD = '123456'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
AUDIO_ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'm4a', 'webm'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['AUDIO_FOLDER'] = AUDIO_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

def get_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print("Veritabanı bağlantı hatası:", e)
        raise

def init_db():
    try:
        conn = get_db()
        c = conn.cursor()
        # Fotoğraf tablosu oluştur
        c.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                filename TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT
            )
        ''')
        # Ses tablosu oluştur
        c.execute('''
            CREATE TABLE IF NOT EXISTS audios (
                filename TEXT PRIMARY KEY,
                user_id TEXT,
                name TEXT
            )
        ''')
        # Fotoğraf tablosuna data sütunu ekle
        c.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS data BYTEA")
        # Ses tablosuna data sütunu ekle
        c.execute("ALTER TABLE audios ADD COLUMN IF NOT EXISTS data BYTEA")
        conn.commit()
        conn.close()
    except Exception as e:
        print("Veritabanı başlatılamadı:", e)
        exit(1)

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_audio(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in AUDIO_ALLOWED_EXTENSIONS

def get_user_id():
    user_id = request.cookies.get('user_id')
    if not user_id:
        user_id = str(uuid.uuid4())
    return user_id

def get_user_photos(user_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("SELECT filename, name FROM photos WHERE user_id=%s", (user_id,))
    photos = c.fetchall()
    conn.close()
    return [(row['filename'], row['name']) for row in photos]

def add_photo_meta(filename, user_id, name, filedata):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO photos (filename, user_id, name, data) VALUES (%s, %s, %s, %s)", (filename, user_id, name, psycopg2.Binary(filedata)))
    conn.commit()
    conn.close()

def get_all_photos():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename, name FROM photos")
    photos = c.fetchall()
    conn.close()
    return [(row['filename'], row['name']) for row in photos]

def add_audio_meta(filename, user_id, name, filedata):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO audios (filename, user_id, name, data) VALUES (%s, %s, %s, %s)", (filename, user_id, name, psycopg2.Binary(filedata)))
    conn.commit()
    conn.close()

def get_user_audios(user_id):
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("SELECT filename FROM audios WHERE user_id=%s", (user_id,))
    audios = c.fetchall()
    conn.close()
    return [row['filename'] for row in audios]

def get_all_audios():
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    c.execute("SELECT filename, name FROM audios")
    audios = c.fetchall()
    conn.close()
    return [(row['filename'], row['name']) for row in audios]

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'düğün'

@app.route('/', methods=['GET', 'POST'])
def index():
    user_id = get_user_id()
    if request.method == 'POST':
        if ('file' not in request.files and 'audio' not in request.files) or 'name' not in request.form:
            return redirect(request.url)
        files = request.files.getlist('file')
        audio = request.files.get('audio')
        name = request.form.get('name', '').strip()
        for file in files:
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(str(uuid.uuid4()) + "_" + file.filename)
                filedata = file.read()
                file.seek(0)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                add_photo_meta(filename, user_id, name, filedata)
        if (audio and audio.filename != '' and allowed_audio(audio.filename)):
            audio_filename = secure_filename(str(uuid.uuid4()) + "_" + audio.filename)
            audiodata = audio.read()
            audio.seek(0)
            audio.save(os.path.join(app.config['AUDIO_FOLDER'], audio_filename))
            add_audio_meta(audio_filename, user_id, name, audiodata)
        resp = make_response(redirect(url_for('index')))
        resp.set_cookie('user_id', user_id)
        return resp
    photos = get_user_photos(user_id)
    audios = get_user_audios(user_id)
    resp = make_response(render_template('index.html', photos=photos, audios=audios))
    resp.set_cookie('user_id', user_id)
    return resp

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT data FROM photos WHERE filename=%s", (filename,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return send_file(io.BytesIO(row[0]), mimetype='image/jpeg', download_name=filename)
    # Dosya veri tabanında yoksa dosya sisteminden gönder
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/audio/<filename>')
def uploaded_audio(filename):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT data FROM audios WHERE filename=%s", (filename,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return send_file(io.BytesIO(row[0]), mimetype='audio/mpeg', download_name=filename)
    return send_from_directory(app.config['AUDIO_FOLDER'], filename)

@app.route('/admin', methods=['GET'])
def admin_panel():
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    photos = get_all_photos()
    audios = get_all_audios()
    return render_template('admin.html', photos=photos, audios=audios)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            resp = make_response(redirect(url_for('admin_panel')))
            resp.set_cookie('is_admin', 'true')
            return resp
        else:
            return render_template('admin_login.html', error="Hatalı giriş!")
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    resp = make_response(redirect(url_for('admin_login')))
    resp.set_cookie('is_admin', '', expires=0)
    return resp

@app.route('/admin/download/<filename>')
def admin_download(filename):
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/admin/download_audio/<filename>')
def admin_download_audio(filename):
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    return send_from_directory(app.config['AUDIO_FOLDER'], filename, as_attachment=True)

@app.route('/admin/download_all_photos')
def admin_download_all_photos():
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    photos = get_all_photos()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for fname, _ in photos:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=fname)
    zip_buffer.seek(0)
    return app.response_class(zip_buffer.getvalue(), mimetype='application/zip',
                             headers={"Content-Disposition": "attachment;filename=photos.zip"})

@app.route('/qr')
def qr_page():
    url = request.url_root.rstrip('/') + '/'
    qr_img = qrcode.make(url)
    img_io = io.BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

@app.route('/admin/download_qr')
def admin_download_qr():
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    url = request.url_root.rstrip('/') + '/'
    qr_img = qrcode.make(url)
    img_io = io.BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='dugun_qr.png')

@app.route('/admin/delete_photo/<filename>', methods=['POST'])
def admin_delete_photo(filename):
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM photos WHERE filename=%s", (filename,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/delete_audio/<filename>', methods=['POST'])
def admin_delete_audio(filename):
    is_admin = request.cookies.get('is_admin')
    if is_admin != 'true':
        return redirect(url_for('admin_login'))
    file_path = os.path.join(app.config['AUDIO_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM audios WHERE filename=%s", (filename,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(debug=True)
