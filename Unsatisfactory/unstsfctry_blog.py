from flask import Flask,render_template,flash,url_for,session,logging,request
from flask_mysqldb import MySQL
from werkzeug.utils import redirect
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.handlers.sha2_crypt import sha256_crypt
from functools import wraps
app = Flask(__name__)
app.secret_key = "Hello_darkness Old friend"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "unsatifactory"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
mysql=MySQL(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" in session:

            return f(*args, **kwargs)
        else:
            flash("Oturumunuz sonlanmıştır, lütfen giriş yapınız.","danger")
            session.clear()
            return redirect(url_for("admin_giris"))
    return decorated_function


class RegisterForm(Form):
    name_surname = StringField("Adınız-Soyadınız",validators=[validators.Length(min=4,max = 25),validators.DataRequired(message = "")])
    username = StringField("Username",validators=[validators.Length(min=4,max = 25),validators.DataRequired(message = "")])
    email = StringField("email",validators=[validators.Email(message = "Lütfen, geçerli bir mail adresi girin...."),validators.DataRequired(message = "")])
    password = PasswordField("Parola",validators=[validators.DataRequired(message = " "),validators.EqualTo(fieldname = "confirm", message="şifreleriniz uyuşmuyor.")])
    confirm = PasswordField("Parola Doğrula")
@app.route("/")
def ana_sayfa():
    return render_template("main_page.html")
@app.route("/iletisim")
def iletisim():
    return render_template("iletisim.html")
@app.route("/hakkimda")
def hakkimda():
    return render_template("hakkimda.html")
#@app.route("/admin_kayıt", methods = ["GET","POST"])
#def register():
    #form = RegisterForm(request.form)
    #if request.method == "POST" and form.validate():
        #name_surname = form.name_surname.data
        #username = form.username.data
        #email = form.email.data
        #password =sha256_crypt.encrypt(form.password.data)    
        #cursor = mysql.connection.cursor()
        #sorgu = "Insert into admin(name_surname, email, username,password) Values(%s,%s,%s,%s)"
        #cursor.execute(sorgu,(name_surname,email,username,password))
        #mysql.connection.commit()
        #cursor.close()
        #return redirect(url_for("ana_sayfa"))    
    #else:
        #return render_template("admin_kayıt.html", form = form)
class loginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Şifreniz")
@app.route("/admin_giris", methods = ["GET","POST"])
def admin_giris():
    form = loginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data
        cursor = mysql.connection.cursor()
        sorgu = "Select * from admin where username = %s"
        result = cursor.execute(sorgu,(username,))
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Tebrikler " + username + " başarıyla giriş yaptınız.","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("ana_sayfa"))
            else:
                flash("Böyle bir admin bulunmamaktadır.","danger")
                return redirect(url_for("admin_giris"))
    return render_template("admin_giris.html",form = form)
@app.route("/admin_cıkıs")
@login_required
def admin_cıkıs():
    session.clear()
    flash("Çıkış yapılmıştır","danger")
    return redirect(url_for("ana_sayfa"))
@app.route("/dashboard")
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu = "Select * from content WHERE Author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        icerikler = cursor.fetchall()
        
        return render_template("dashboard.html", icerikler = icerikler)
    else:
        flash("Maalesef Hiçbir İçerik Yok!","danger")
        return render_template("dashboard.html")
    
@app.route("/add_content",methods = ["GET", "POST"])
def content():
    form = ContentForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        cursor = mysql.connection.cursor()
        sorgu = "Insert into content(Title,Content,Author) Values(%s,%s,%s)"
        cursor.execute(sorgu,(title,content,session["username"]))
        mysql.connection.commit()
        cursor.close()
        flash("İçerik Başarıyla Eklenmiştir.","success")
        return redirect(url_for("dashboard"))


    
    return render_template("add_content.html",form = form)
@app.route("/contents")
def icerikler():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From content"
    result = cursor.execute(sorgu)
    if result > 0:
        icerikler = cursor.fetchall()
        
        return render_template("contents.html", icerikler = icerikler)
    else:
        flash("Maalesef Hiçbir İçerik Yok!","danger")
        return render_template("contents.html")
@app.route("/content/<string:id>")
def content_1(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * From content where id = %s"
    result = cursor.execute(sorgu,(id,))
    if result > 0:
        icerik = cursor.fetchone()
        return render_template("content.html", icerik = icerik)
    else:
        return render_template("content.html")

@app.route("/del/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from content where Author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete from content where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir içerik yok veya bu içeriği silmek için gerekli izne sahip değilsiniz.", "danger")
        return redirect(url_for("ana_sayfa"))
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * From content where id = %s and Author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))
        if result == 0:
            flash("Böyle bir içerik bulunmamaktadır","danger")
            return redirect(url_for("ana_sayfa"))
        else:
            icerik = cursor.fetchone()
            form = ContentForm()
            form.title.data = icerik["Title"]
            form.content.data = icerik["Content"]
            return render_template("update.html", form = form)
    else:
        form = ContentForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update content set Title = %s,Content = %s Where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("İçeriğiniz Güncellenmiştir", "success")
        return redirect(url_for("dashboard"))
@app.route("/search", methods = ["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("ana_sayfa"))
    else:
        keyword = request.form.get("keyword")
        cursor = mysql.connection.cursor()
        sorgu = "Select * from content Where Title like '%" + keyword + "%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun içerik bulunamadı.","warning")
            return redirect(url_for("icerikler"))
        else:
            icerikler = cursor.fetchall()
            return render_template("contents.html",icerikler = icerikler)
class ContentForm(Form):
    title = StringField("Başlık",validators=[validators.DataRequired(message = "Lütfen Başlık Giriniz...")])
    content = TextAreaField("İçerik",validators=[validators.DataRequired(message = "Lütfen İçeriğinizi Oluşturunuz...")])
if __name__ == "__main__":
    app.run(debug = True)