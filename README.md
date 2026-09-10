# College Management System (Flask + MySQL)
Demo Video Link : https://drive.google.com/file/d/1RKBKjnR-CMl7hloTQG_rAvUYI90YyZTe/view?usp=sharing
## Option A — Run with Docker (recommended)
1. Install Docker & Docker Compose
2. From project root:
   docker-compose up --build
3. App: http://localhost:5000  
   phpMyAdmin: http://localhost:8080 (user: root, password: rootpassword)

4. After DB is up, exec into web container and run:
   docker exec -it cms_web python seed.py  
   (This hashes the seeded passwords)

## Option B — Run locally (without Docker)
1. Install Python 3.11 and MySQL server
2. Create database and apply mysql/init.sql (use MySQL Workbench or CLI)
3. pip install -r backend/requirements.txt
4. Set env vars (or edit db_config.py):  
   DB_USER, DB_PASS, DB_HOST, DB_NAME, SECRET_KEY
5. Run backend/seed.py to hash seed passwords
6. Start app:  
   python backend/app.py
7. Open http://localhost:5000

### Default seeded accounts (before hashing):
- Admin → `admin / admin123`  
- Faculty → `patel@college.edu / facpass`  
- Student → `amit@college.edu / studpass`

(After running seed.py, passwords are hashed — use the same plaintext to login.)
