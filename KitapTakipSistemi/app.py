import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__, template_folder="templates", static_folder="static")  
app.secret_key = "super_secret_key"  

# 📌 Veritabanı bağlantısı
def get_db_connection():
    db_path = os.path.abspath("database.db")  
    print("📌 Flask şu veritabanını kullanıyor:", db_path)  # Debug için
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# 📌 Boş ID’leri tekrar kullanacak fonksiyon
def get_next_available_id():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MIN(t1.id + 1) FROM books t1 
        WHERE NOT EXISTS (SELECT id FROM books t2 WHERE t2.id = t1.id + 1);
    """)
    
    result = cursor.fetchone()[0]

    if result is None:  # Eğer hiç ID yoksa 1’den başlat
        cursor.execute("SELECT MAX(id) FROM books")
        max_id = cursor.fetchone()[0]
        return 1 if max_id is None else max_id + 1

    return result

# 📌 Ana Sayfa
@app.route("/")
def index():
    return render_template("index.html")

# 📌 Kullanıcı giriş yapma
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        # 📌 Şifre kontrolü doğru yapılıyor mu?
        if user and check_password_hash(user["password"], password):
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return "Hata: Kullanıcı adı veya şifre yanlış!"

    return render_template("login.html")

# 📌 Kullanıcı kayıt olma
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Hata: Şifreler uyuşmuyor!"

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (first_name, last_name, email, username, password) VALUES (?, ?, ?, ?, ?)",
                           (first_name, last_name, email, username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Hata: Bu kullanıcı adı veya e-posta zaten kayıtlı!"
        finally:
            conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")

# 📌 Kullanıcı Paneli (Dashboard)
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session["username"])

# 📌 Kitap ekleme
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "username" not in session:
        return redirect(url_for("login"))

    # 📌 Kullanıcının seçebileceği kategoriler
    kategoriler = ["Korku", "Macera", "Bilim Kurgu", "Romantik", "Biyografi", "Anı", "Hikaye", "Çizgi Roman"]

    if request.method == "POST":
        author_name = request.form["author_name"]
        book_name = request.form["book_name"]
        location = request.form["location"]
        category = request.form["kategori"]  # 📌 Dropdown’dan gelen kategori

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (session["username"],))
        user = cursor.fetchone()

        if user:
            user_id = user["id"]
            new_id = get_next_available_id()  # 📌 Yeni boş ID'yi al

            cursor.execute("INSERT INTO books (id,author_name, book_name, location, kategori, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                           (new_id, author_name, book_name, location, category, user_id))
            conn.commit()
        conn.close()
        return redirect(url_for("dashboard"))

    return render_template("add_book.html", kategoriler=kategoriler)

# 📌 Kullanıcının eklediği kitapları listeleme
@app.route("/my_books", methods=["GET", "POST"])  # <---- POST EKLENDİ
def my_books():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    # 📌 Kullanıcının kitaplarının kategorilerini çek
    cursor.execute("SELECT DISTINCT kategori FROM books")
    kategoriler = [row["kategori"] for row in cursor.fetchall()]

    # 📌 Seçili kategori al
    secili_kategori = request.form.get("kategori", "")

    # 📌 Eğer kategori seçilmişse, sadece o kategorideki kitapları göster
    if secili_kategori:
        cursor.execute("""
            SELECT * FROM books WHERE user_id = (SELECT id FROM users WHERE username = ?) 
            AND kategori = ?
        """, (session["username"], secili_kategori))
    else:
        cursor.execute("""
            SELECT * FROM books WHERE user_id = (SELECT id FROM users WHERE username = ?)
        """, (session["username"],))

    books = cursor.fetchall()
    conn.close()

    return render_template("my_books.html", books=books, kategoriler=kategoriler, secili_kategori=secili_kategori)



# 📌 Kitap silme
@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM books WHERE id = ? AND user_id = 
        (SELECT id FROM users WHERE username = ?)
    """, (book_id, session["username"]))
    conn.commit()
    conn.close()

    return redirect(url_for("my_books"))

# 📌 Kitap güncelleme
@app.route("/edit_book/<int:book_id>", methods=["GET", "POST"])
def edit_book(book_id):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        author_name = request.form["author_name"]
        book_name = request.form["book_name"]
        location = request.form["location"]
        kategori = request.form["kategori"]  # 📌 Kategori eklemeyi unutmayalım

        cursor.execute("""
            UPDATE books 
            SET author_name = ?, book_name = ?, location = ?, kategori = ?
            WHERE id = ? AND user_id = (SELECT id FROM users WHERE username = ?)
        """, (author_name, book_name, location, kategori, book_id, session["username"]))
        conn.commit()
        conn.close()
        return redirect(url_for("my_books"))

    cursor.execute("""
        SELECT * FROM books WHERE id = ? AND user_id = 
        (SELECT id FROM users WHERE username = ?)
    """, (book_id, session["username"]))
    book = cursor.fetchone()
    conn.close()

    return render_template("edit_book.html", book=book)


# 📌 Kitap Arama
@app.route("/search_books", methods=["GET", "POST"])
def search_books():
    if "username" not in session:
        return redirect(url_for("login"))

    books = []
    if request.method == "POST":
        search_query = request.form["search_query"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM books 
            WHERE (CAST(id AS TEXT) LIKE ? 
            OR author_name LIKE ?
            OR book_name LIKE ?  
            OR location LIKE ?) 
            AND user_id = (SELECT id FROM users WHERE username = ?)
        """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", session["username"]))
        
        books = cursor.fetchall()
        conn.close()

    return render_template("search_books.html", books=books)

# 📌 Kitapları Düzenleme Sayfası
@app.route("/edit_books")
def edit_books():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE user_id = (SELECT id FROM users WHERE username = ?)", (session["username"],))
    books = cursor.fetchall()
    conn.close()
    
    return render_template("edit_books.html", books=books)

# 📌 Çıkış yapma
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)