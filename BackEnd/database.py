import psycopg2
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Database connection - JUST CHANGE PASSWORD!
DB_CONFIG = {
    "host": "localhost",
    "database": "answer_eval_db",
    "user": "postgres",
    "password": "your_password_here",  # CHANGE THIS!
    "port": "5432"
}


def create_database():
    """CREATE DATABASE TABLES - RUN THIS ONCE"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # CREATE ALL TABLES
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            class_id SERIAL PRIMARY KEY,
            class_name VARCHAR(100) NOT NULL,
            teacher_id INTEGER REFERENCES teachers(teacher_id),
            academic_year VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            roll_number VARCHAR(50) UNIQUE NOT NULL,
            class_id INTEGER REFERENCES classes(class_id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS exams (
            exam_id SERIAL PRIMARY KEY,
            exam_name VARCHAR(200) NOT NULL,
            class_id INTEGER REFERENCES classes(class_id),
            subject VARCHAR(100) NOT NULL,
            exam_date DATE NOT NULL,
            total_marks INTEGER NOT NULL,
            answer_key_json JSONB,
            marking_scheme_json JSONB,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS answer_scripts (
            script_id SERIAL PRIMARY KEY,
            student_id INTEGER REFERENCES students(student_id),
            exam_id INTEGER REFERENCES exams(exam_id),
            pdf_path VARCHAR(500) NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_obtained_marks DECIMAL(5,2),
            evaluated_at TIMESTAMP,
            status VARCHAR(50) DEFAULT 'uploaded'
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS evaluated_answers (
            eval_id SERIAL PRIMARY KEY,
            script_id INTEGER REFERENCES answer_scripts(script_id),
            question_number INTEGER NOT NULL,
            question_type VARCHAR(50) NOT NULL,
            extracted_text TEXT,
            marks_obtained DECIMAL(5,2),
            max_marks DECIMAL(5,2),
            confidence_score DECIMAL(3,2),
            needs_review BOOLEAN DEFAULT FALSE,
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS anomaly_flags (
            flag_id SERIAL PRIMARY KEY,
            script_id INTEGER REFERENCES answer_scripts(script_id),
            question_number INTEGER NOT NULL,
            similarity_score DECIMAL(3,2),
            similar_script_id INTEGER,
            flag_reason VARCHAR(200),
            resolved BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        print("✅ ALL TABLES CREATED SUCCESSFULLY!")
        conn.commit()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if conn:
            cursor.close()
            conn.close()


# DATABASE OPERATIONS - YOUR TEAM WILL USE THESE!

def add_teacher(name, email, password_hash):
    """Add a new teacher"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teachers (name, email, password_hash) VALUES (%s, %s, %s) RETURNING teacher_id",
        (name, email, password_hash)
    )
    teacher_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return teacher_id


def add_exam(exam_name, class_id, subject, exam_date, total_marks):
    """Add a new exam"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO exams (exam_name, class_id, subject, exam_date, total_marks) 
        VALUES (%s, %s, %s, %s, %s) RETURNING exam_id""",
        (exam_name, class_id, subject, exam_date, total_marks)
    )
    exam_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return exam_id


def store_evaluation_results(script_id, evaluations):
    """Store evaluated answers - YOUR TEAM WILL CALL THIS"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for eval_data in evaluations:
        cursor.execute(
            """INSERT INTO evaluated_answers 
            (script_id, question_number, question_type, extracted_text, 
             marks_obtained, max_marks, confidence_score, needs_review, feedback) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (script_id, eval_data['question_number'], eval_data['question_type'],
             eval_data['extracted_text'], eval_data['marks_obtained'],
             eval_data['max_marks'], eval_data['confidence_score'],
             eval_data['needs_review'], eval_data['feedback'])
        )

    conn.commit()
    conn.close()
    print(f"✅ Stored {len(evaluations)} evaluations for script {script_id}")


def get_exam_results(exam_id):
    """Get all results for an exam - FOR DASHBOARD"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.name, s.roll_number, asp.total_obtained_marks
        FROM students s
        JOIN answer_scripts asp ON s.student_id = asp.student_id
        WHERE asp.exam_id = %s
    """, (exam_id,))

    results = cursor.fetchall()
    conn.close()
    return results


# RUN THIS TO SETUP DATABASE
if __name__ == "__main__":
    create_database()
    print("🎉 DATABASE READY FOR YOUR TEAM!")