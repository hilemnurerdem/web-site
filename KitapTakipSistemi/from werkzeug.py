from werkzeug.security import generate_password_hash
import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Şifreleri güncelle (!!! ESKİ ŞİFRELERİNİ BİLİYORSAN)
users = [
    ("eski_kullanici1", "eski_sifre1"),
    ("eski_kullanici2", "eski_sifre2"),
    # Buraya eski kullanıcıları ekle
]

for username, plain_password in users:
    hashed_password = generate_password_hash(plain_password)
    cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password, username))

conn.commit()
conn.close()
print("Şifreler başarıyla güncellendi!")
