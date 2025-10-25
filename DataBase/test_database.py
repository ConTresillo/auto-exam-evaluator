# testdb.py - OOP / Agile version
from database import DatabaseManager

# --- CONFIGURATION ---
db_file = "testdb.db"  # parameterized DB file
db = DatabaseManager(db_file=db_file)

# --- STEP 1: CREATE TABLES ---
db.create_tables()

print("🧪 TESTING DATABASE...")

# --- STEP 2: ADD TEACHER ---
teacher_id = db.insert("teachers", {
    "name": "Dr. Smith",
    "email": "smith@college.edu",
    "password_hash": "hashed_password123"
})
print(f"✅ Teacher ID: {teacher_id}")

# --- STEP 3: ADD CLASS ---
class_id = db.insert("classes", {
    "class_name": "Computer Science 101",
    "teacher_id": teacher_id,
    "academic_year": "2024"
})
print(f"✅ Class ID: {class_id}")

# --- STEP 4: ADD STUDENT ---
student_id = db.insert("students", {
    "name": "John Doe",
    "roll_number": "CS2024001",
    "class_id": class_id
})
print(f"✅ Student ID: {student_id}")

# --- STEP 5: ADD EXAM ---
exam_id = db.insert("exams", {
    "exam_name": "Midterm Exam",
    "class_id": class_id,
    "subject": "Mathematics",
    "exam_date": "2024-01-15",
    "total_marks": 100
})
print(f"✅ Exam ID: {exam_id}")

# --- STEP 6: ADD ANSWER SCRIPT ---
script_id = db.insert("answer_scripts", {
    "student_id": student_id,
    "exam_id": exam_id,
    "pdf_path": "uploads/student1.pdf"
})
print(f"✅ Script ID: {script_id}")

# --- STEP 7: STORE EVALUATIONS ---
sample_evaluations = [
    {
        "script_id": script_id,
        "question_number": 1,
        "question_type": "short_answer",
        "extracted_text": "The capital of France is Paris",
        "marks_obtained": 8.0,
        "max_marks": 10.0,
        "confidence_score": 0.85,
        "needs_review": False,
        "feedback": "Good answer but missing details"
    },
    {
        "script_id": script_id,
        "question_number": 2,
        "question_type": "long_answer",
        "extracted_text": "Student handwriting unclear here",
        "marks_obtained": 5.0,
        "max_marks": 15.0,
        "confidence_score": 0.45,
        "needs_review": True,
        "feedback": "Low confidence - needs manual review"
    }
]

for eval_data in sample_evaluations:
    db.insert("evaluated_answers", eval_data)

# Update script status after evaluation
db.update_script_status(script_id)

print("🎯 DATABASE TEST COMPLETE! SHOW YOUR TEAM THIS OUTPUT!")

# --- STEP 8: VIEW DATABASE CONTENTS ---
print("\n🎯 VIEWING DATABASE CONTENTS...")
for table in db.tables.keys():
    print(f"\n--- TABLE: {table} ---")
    rows = db.fetch_all(table)
    for row in rows:
        print(row)
