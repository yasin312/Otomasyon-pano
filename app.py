from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'gizli_anahtar'  # Deploy öncesi yine değiştir
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect('ilan.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
@app.route('/sayfa/<int:sayfa_no>')
def index(sayfa_no=1):
    conn = get_db_connection()
    toplam = conn.execute('SELECT COUNT(*) FROM ilanlar').fetchone()[0]
    sayfa_basi = 10
    toplam_sayfa = (toplam + sayfa_basi -1)//sayfa_basi
    offset = (sayfa_no -1)*sayfa_basi
    ilanlar = conn.execute('SELECT * FROM ilanlar ORDER BY id DESC LIMIT ? OFFSET ?', (sayfa_basi, offset)).fetchall()
    conn.close()
    return render_template('index.html', ilanlar=ilanlar, sayfa_no=sayfa_no, toplam_sayfa=toplam_sayfa)

@app.route('/ilan/<int:ilan_id>')
def ilan_detay(ilan_id):
    conn = get_db_connection()
    ilan = conn.execute('SELECT * FROM ilanlar WHERE id=?',(ilan_id,)).fetchone()
    resimler = os.listdir(f"static/uploads/{ilan_id}") if os.path.exists(f"static/uploads/{ilan_id}") else []
    conn.close()
    return render_template('detay.html', ilan=ilan, resimler=resimler)

@app.route('/login', methods=['GET','POST'])
def login():
    hata = None
    if request.method=='POST':
        if request.form['kullanici']=='acar_otomasyon' and request.form['sifre']=='1234567812Aa':
            session['admin']=True
            return redirect(url_for('admin'))
        else:
            hata='Kullanıcı adı ya da şifre yanlış'
    return render_template('login.html', hata=hata)

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET','POST'])
def admin():
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    if request.method=='POST':
        baslik = request.form['baslik']
        aciklama= request.form['aciklama']
        c = conn.cursor()
        c.execute('INSERT INTO ilanlar (baslik,aciklama) VALUES (?,?)',(baslik,aciklama))
        ilan_id = c.lastrowid
        conn.commit()
        path = os.path.join(app.config['UPLOAD_FOLDER'],str(ilan_id))
        os.makedirs(path, exist_ok=True)
        for file in request.files.getlist('resimler'):
            if file and allowed_file(file.filename):
                fn = secure_filename(file.filename)
                file.save(os.path.join(path,fn))
        return redirect(url_for('admin'))
    ilanlar = conn.execute('SELECT * FROM ilanlar ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin.html', ilanlar=ilanlar)

@app.route('/sil/<int:ilan_id>')
def sil(ilan_id):
    if not session.get('admin'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute('DELETE FROM ilanlar WHERE id=?',(ilan_id,))
    conn.commit()
    conn.close()
    path = f"static/uploads/{ilan_id}"
    if os.path.exists(path):
        for f in os.listdir(path):
            os.remove(os.path.join(path,f))
        os.rmdir(path)
    return redirect(url_for('admin'))

if __name__=='__main__':
    if not os.path.exists('ilan.db'):
        conn = sqlite3.connect('ilan.db')
        conn.execute('CREATE TABLE ilanlar (id INTEGER PRIMARY KEY AUTOINCREMENT, baslik TEXT, aciklama TEXT)')
        conn.close()
    os.makedirs('static/uploads', exist_ok=True)
    app.run(debug=True)