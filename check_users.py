import sqlite3
import bcrypt

conn = sqlite3.connect('grc_production.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check if users table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
if cursor.fetchone():
    print('✓ Users table exists')
    cursor.execute('SELECT id, email, first_name, last_name, role, password_hash FROM users')
    users = cursor.fetchall()
    print(f'Found {len(users)} users:')
    for user in users:
        print(f'  - {user["email"]} | Role: {user["role"]} | Hash: {user["password_hash"][:20]}...')
    
    # Test password verification
    print('\n--- Testing Password Verification ---')
    cursor.execute("SELECT email, password_hash FROM users WHERE email = ?", ("admin@demo.com",))
    admin = cursor.fetchone()
    if admin:
        try:
            pwd_bytes = "admin123".encode('utf-8')
            result = bcrypt.checkpw(pwd_bytes, admin["password_hash"].encode('utf-8'))
            print(f'admin@demo.com password "admin123" verification: {result}')
        except Exception as e:
            print(f'Error verifying password: {e}')
else:
    print('✗ Users table does not exist')

conn.close()
