import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    def __init__(
        self,
        db_file=None,
        default_script_status="uploaded",
        evaluated_status="evaluated",
        tables=None
    ):
        self.db_file = db_file or os.getenv("DB_FILE", "answer_evaluator.db")
        self.default_script_status = default_script_status
        self.evaluated_status = evaluated_status

        # Default table schema
        self.tables = tables or {
            "teachers": """
                CREATE TABLE IF NOT EXISTS teachers (
                    teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
            "classes": """
                CREATE TABLE IF NOT EXISTS classes (
                    class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_name TEXT NOT NULL,
                    teacher_id INTEGER,
                    academic_year TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
                );
            """,
            "students": """
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    roll_number TEXT UNIQUE NOT NULL,
                    class_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(class_id)
                );
            """,
            "exams": """
                CREATE TABLE IF NOT EXISTS exams (
                    exam_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_name TEXT NOT NULL,
                    class_id INTEGER,
                    subject TEXT NOT NULL,
                    exam_date TEXT NOT NULL,
                    total_marks INTEGER NOT NULL,
                    answer_key_json TEXT,
                    marking_scheme_json TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (class_id) REFERENCES classes(class_id)
                );
            """,
            "answer_scripts": f"""
                CREATE TABLE IF NOT EXISTS answer_scripts (
                    script_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER,
                    exam_id INTEGER,
                    pdf_path TEXT NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_obtained_marks REAL,
                    evaluated_at TIMESTAMP,
                    status TEXT DEFAULT '{self.default_script_status}',
                    FOREIGN KEY (student_id) REFERENCES students(student_id),
                    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
                );
            """,
            "evaluated_answers": """
                CREATE TABLE IF NOT EXISTS evaluated_answers (
                    eval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id INTEGER,
                    question_number INTEGER NOT NULL,
                    question_type TEXT NOT NULL,
                    extracted_text TEXT,
                    marks_obtained REAL,
                    max_marks REAL,
                    confidence_score REAL,
                    needs_review BOOLEAN DEFAULT FALSE,
                    feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (script_id) REFERENCES answer_scripts(script_id)
                );
            """,
            "anomaly_flags": """
                CREATE TABLE IF NOT EXISTS anomaly_flags (
                    flag_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    script_id INTEGER,
                    question_number INTEGER NOT NULL,
                    similarity_score REAL,
                    similar_script_id INTEGER,
                    flag_reason TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (script_id) REFERENCES answer_scripts(script_id)
                );
            """
        }

    # --- Core methods ---
    def connect(self):
        try:
            conn = sqlite3.connect(self.db_file)
            return conn
        except sqlite3.Error as e:
            print(f"❌ Error connecting to DB: {e}")
            raise

    def create_tables(self):
        try:
            conn = self.connect()
            cursor = conn.cursor()
            for table_name, ddl in self.tables.items():
                cursor.execute(ddl)
            conn.commit()
            print(f"✅ All tables created in {self.db_file}")
        except sqlite3.Error as e:
            print(f"❌ Error creating tables: {e}")
            raise
        finally:
            conn.close()

    # --- Generic CRUD operation ---
    def insert(self, table, data: dict):
        try:
            keys = ", ".join(data.keys())
            question_marks = ", ".join(["?"] * len(data))
            values = tuple(data.values())
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(f"INSERT INTO {table} ({keys}) VALUES ({question_marks})", values)
            conn.commit()
            last_id = cursor.lastrowid
            return last_id
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Integrity error inserting into {table}: {e}")
            return None
        except sqlite3.Error as e:
            print(f"❌ Database error inserting into {table}: {e}")
            return None
        finally:
            conn.close()

    def fetch_all(self, table, where_clause="", params=()):
        try:
            conn = self.connect()
            cursor = conn.cursor()
            query = f"SELECT * FROM {table}"
            if where_clause:
                query += f" WHERE {where_clause}"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error as e:
            print(f"❌ Error fetching from {table}: {e}")
            return []
        finally:
            conn.close()

    def update_script_status(self, script_id, status=None):
        status = status or self.evaluated_status
        try:
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE answer_scripts SET status = ?, evaluated_at = CURRENT_TIMESTAMP WHERE script_id = ?",
                (status, script_id)
            )
            conn.commit()
        except sqlite3.Error as e:
            print(f"❌ Error updating script status: {e}")
        finally:
            conn.close()

    def store_evaluation_batch(self, script_id, evaluations):
        """Batch insert evaluations with exception handling"""
        for eval_data in evaluations:
            try:
                self.insert("evaluated_answers", {
                    "script_id": script_id,
                    "question_number": eval_data['question_number'],
                    "question_type": eval_data['question_type'],
                    "extracted_text": eval_data['extracted_text'],
                    "marks_obtained": eval_data['marks_obtained'],
                    "max_marks": eval_data['max_marks'],
                    "confidence_score": eval_data['confidence_score'],
                    "needs_review": eval_data['needs_review'],
                    "feedback": eval_data['feedback']
                })
            except Exception as e:
                print(f"⚠️ Failed to insert evaluation: {e}")

        self.update_script_status(script_id)
        print(f"✅ Stored {len(evaluations)} evaluations safely")
