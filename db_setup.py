import sqlite3

# 📌 Veritabanı bağlantısını aç
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# 📌 Kullanıcılar tablosu
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
''')

# 📌 Kitaplar tablosu (Kullanıcıların eklediği kitaplar)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_name TEXT NOT NULL,
        author_name TEXT NOT NULL,
        location TEXT NOT NULL,
        kategori TEXT,  -- 📌 Yeni kategori sütunu eklendi
        user_id INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
''')

conn.commit()
conn.close()

print("✅ Veritabanı ve tablolar başarıyla oluşturuldu.")
