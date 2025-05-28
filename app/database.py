import sqlite3
from app.utils.security import hash_password

def get_db():
    conn = sqlite3.connect("app/data/school.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabel users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT CHECK(role IN ('guru', 'orang_tua')) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel kelas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS kelas (
            kelas_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_kelas TEXT NOT NULL,
            wali_kelas_id INTEGER NOT NULL,
            FOREIGN KEY (wali_kelas_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
    # Seed data untuk kelas: wali kelas hanya dari role 'guru' (user_id 1 dan 2)

    # Tabel siswa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS siswa (
            siswa_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            kelas_id INTEGER NOT NULL,
            orang_tua_id INTEGER,
            kode_siswa TEXT UNIQUE,
            FOREIGN KEY (kelas_id) REFERENCES kelas(kelas_id) ON DELETE CASCADE,
            FOREIGN KEY (orang_tua_id) REFERENCES users(user_id) ON DELETE SET NULL
        )
    """)
    # Seed data untuk siswa: orang_tua_id dari role 'orang_tua' (user_id 3 dan 4)
  
    
    # Tabel mata_pelajaran
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mata_pelajaran (
            mata_pelajaran_id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE,
            kode TEXT UNIQUE,
            deskripsi TEXT
        )
    """)
   
    
    # Tabel absensi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS absensi (
            absensi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL,
            tanggal DATE NOT NULL,
            status TEXT CHECK(status IN ('Hadir', 'Izin', 'Sakit', 'Alpa')) NOT NULL,
            FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE
        )
    """)
 
    
    # Tabel jadwal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jadwal (
            jadwal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            kelas_id INTEGER NOT NULL,
            hari TEXT CHECK(hari IN ('Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu')) NOT NULL,
            jam_mulai TIME NOT NULL,
            jam_selesai TIME NOT NULL,
            mata_pelajaran_id INTEGER NOT NULL,
            FOREIGN KEY (kelas_id) REFERENCES kelas(kelas_id) ON DELETE CASCADE,
            FOREIGN KEY (mata_pelajaran_id) REFERENCES mata_pelajaran(mata_pelajaran_id) ON DELETE RESTRICT
        )
    """)
  
    
    # Tabel perilaku
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS perilaku (
            perilaku_id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL,
            guru_id INTEGER NOT NULL,
            deskripsi TEXT NOT NULL,
            rating TEXT CHECK(rating IN ('Sangat Baik', 'Baik', 'Cukup', 'Kurang', 'Buruk')) NOT NULL,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE,
            FOREIGN KEY (guru_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
   
    
    # Tabel notifikasi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifikasi (
            notifikasi_id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL,
            orang_tua_id INTEGER NOT NULL,
            jenis TEXT CHECK(jenis IN ('Tugas', 'Perilaku', 'Absensi', 'Pengumuman')) NOT NULL,
            deskripsi TEXT NOT NULL,
            status TEXT CHECK(status IN ('Belum Dibaca', 'Dibaca')) DEFAULT 'Belum Dibaca',
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE,
            FOREIGN KEY (orang_tua_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    """)
   
    
    # Tabel tugas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tugas (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            guru_id INTEGER NOT NULL,
            kelas_id INTEGER NOT NULL,
            deskripsi TEXT NOT NULL,
            batas_waktu DATE NOT NULL,
            FOREIGN KEY (guru_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (kelas_id) REFERENCES kelas(kelas_id) ON DELETE CASCADE
        )
    """)
  
    
    # Tabel rekapan_siswa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rekapan_siswa (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,
            siswa_id INTEGER NOT NULL,
            guru_id INTEGER NOT NULL,
            mata_pelajaran_id INTEGER NOT NULL,
            rating TEXT CHECK(rating IN ('Sangat Baik', 'Baik', 'Cukup', 'Kurang', 'Buruk')) NOT NULL,
            catatan TEXT,
            tanggal DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (siswa_id) REFERENCES siswa(siswa_id) ON DELETE CASCADE,
            FOREIGN KEY (guru_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (mata_pelajaran_id) REFERENCES mata_pelajaran(mata_pelajaran_id) ON DELETE RESTRICT
        )
    """)
  
    
    conn.commit()
    conn.close()