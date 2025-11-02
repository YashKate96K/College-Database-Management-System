from db_config import get_connection
from werkzeug.security import generate_password_hash

def hash_passwords():
    conn = get_connection()
    cur = conn.cursor()
    # admin
    cur.execute("UPDATE admin SET password=%s WHERE username=%s", (generate_password_hash('admin123'), 'admin'))
    # faculty
    cur.execute("UPDATE faculty SET password=%s WHERE email=%s", (generate_password_hash('facpass'), 'patel@college.edu'))
    # student
    cur.execute("UPDATE student SET password=%s WHERE email=%s", (generate_password_hash('studpass'), 'amit@college.edu'))
    conn.commit()
    cur.close()
    conn.close()
    print("Seed passwords hashed.")

if __name__ == "__main__":
    hash_passwords()
