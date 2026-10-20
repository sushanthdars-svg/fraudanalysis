#!/usr/bin/env python3
"""Direct database setup with mysql.connector"""

import mysql.connector
import os

# Set UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='Sushanth2005@',
        autocommit=False
    )
    cursor = conn.cursor()
    
    # Create database
    cursor.execute('CREATE DATABASE IF NOT EXISTS fraud_detection_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    print('[OK] Database created')
    
    # Create user
    cursor.execute('DROP USER IF EXISTS `fraud_user`@`localhost`')
    cursor.execute('CREATE USER `fraud_user`@`localhost` IDENTIFIED BY \'Sushanth2005@\'')
    print('[OK] User created')
    
    # Grant privileges
    cursor.execute('GRANT ALL PRIVILEGES ON fraud_detection_db.* TO `fraud_user`@`localhost`')
    cursor.execute('FLUSH PRIVILEGES')
    print('[OK] Privileges granted')
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print('\n[SUCCESS] Database and user created successfully')
    
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()
