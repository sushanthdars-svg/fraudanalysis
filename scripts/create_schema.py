#!/usr/bin/env python3
"""Create database tables using direct mysql.connector"""

import mysql.connector
import os

os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    print("[INFO] Connecting to database as app user...")
    conn = mysql.connector.connect(
        host='localhost',
        user='fraud_user',
        password='Sushanth2005@',
        database='fraud_detection_db'
    )
    cursor = conn.cursor()
    
    # Load the SQL schema
    schema_sql = """
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(255) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('Admin', 'Analyst', 'Viewer') NOT NULL DEFAULT 'Viewer',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_role (role)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS customer (
        id INT AUTO_INCREMENT PRIMARY KEY,
        external_id VARCHAR(50) UNIQUE,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        email VARCHAR(255),
        phone VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_email (email),
        INDEX idx_phone (phone)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS transaction_record (
        id INT AUTO_INCREMENT PRIMARY KEY,
        customer_id INT NOT NULL,
        amount DECIMAL(12, 2) NOT NULL,
        currency VARCHAR(3) DEFAULT 'USD',
        merchant_id VARCHAR(100),
        merchant_name VARCHAR(255),
        merchant_category VARCHAR(100),
        transaction_date TIMESTAMP,
        transaction_type VARCHAR(50),
        card_last_four VARCHAR(4),
        device_id VARCHAR(100),
        device_type VARCHAR(50),
        location_city VARCHAR(100),
        location_country VARCHAR(100),
        location_latitude DECIMAL(10, 8),
        location_longitude DECIMAL(11, 8),
        is_synthetic BOOLEAN DEFAULT FALSE,
        fraud_label BOOLEAN DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customer(id) ON DELETE CASCADE,
        INDEX idx_customer (customer_id),
        INDEX idx_date (transaction_date),
        INDEX idx_amount (amount),
        INDEX idx_type (transaction_type)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS fraud_rule (
        id INT AUTO_INCREMENT PRIMARY KEY,
        rule_code VARCHAR(20) NOT NULL UNIQUE,
        rule_name VARCHAR(255) NOT NULL,
        description TEXT,
        rule_type VARCHAR(50),
        threshold_value DECIMAL(15, 2),
        operator VARCHAR(20),
        is_active BOOLEAN DEFAULT TRUE,
        severity_level INT DEFAULT 1,
        risk_weight DECIMAL(5, 3) DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_code (rule_code),
        INDEX idx_active (is_active)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS fraud_assessment (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_id INT NOT NULL,
        risk_score DECIMAL(5, 2),
        risk_level VARCHAR(20),
        ml_prediction DECIMAL(5, 4),
        ml_confidence DECIMAL(5, 4),
        rules_triggered INT DEFAULT 0,
        assessment_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transaction_record(id) ON DELETE CASCADE,
        INDEX idx_transaction (transaction_id),
        INDEX idx_score (risk_score)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS triggered_rule (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_id INT NOT NULL,
        rule_id INT NOT NULL,
        triggered_value DECIMAL(15, 2),
        triggered_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transaction_record(id) ON DELETE CASCADE,
        FOREIGN KEY (rule_id) REFERENCES fraud_rule(id) ON DELETE CASCADE,
        INDEX idx_transaction (transaction_id),
        INDEX idx_rule (rule_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS fraud_alert (
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_id INT NOT NULL,
        alert_status VARCHAR(20) DEFAULT 'Pending',
        risk_score DECIMAL(5, 2),
        alert_reason TEXT,
        assigned_to INT,
        review_notes TEXT,
        review_decision VARCHAR(20),
        reviewed_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (transaction_id) REFERENCES transaction_record(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_to) REFERENCES user(id),
        INDEX idx_status (alert_status),
        INDEX idx_date (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

    CREATE TABLE IF NOT EXISTS audit_log (
        id INT AUTO_INCREMENT PRIMARY KEY,
        actor_id INT,
        action VARCHAR(50) NOT NULL,
        target_entity VARCHAR(100),
        target_id INT,
        metadata JSON,
        changes_before JSON,
        changes_after JSON,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (actor_id) REFERENCES user(id),
        INDEX idx_actor (actor_id),
        INDEX idx_action (action),
        INDEX idx_date (created_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    # Execute table creation statements separately
    tables_sql = [s.strip() for s in schema_sql.split(';') if s.strip()]
    for i, sql in enumerate(tables_sql, 1):
        try:
            cursor.execute(sql)
            table_name = sql.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
            print(f"[OK] Table {i}/{len(tables_sql)}: {table_name}")
        except Exception as e:
            print(f"[ERROR] Statement {i}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    # Verify
    print("\n[INFO] Verifying tables...")
    conn = mysql.connector.connect(
        host='localhost',
        user='fraud_user',
        password='Sushanth2005@',
        database='fraud_detection_db'
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"[OK] Tables: {', '.join(sorted(tables))}")
    cursor.close()
    conn.close()
    
    print("\n[SUCCESS] Database schema created successfully!")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
