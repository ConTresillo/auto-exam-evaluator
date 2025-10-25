from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import DatabaseManager  # Your existing class!

app = FastAPI(title="Answer Evaluator API", version="1.0.0")
db = DatabaseManager()

@app.on_event("startup")
def startup():
    try:
        db.create_tables()
        print("🚀 API Started with Database Ready!")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")


# --- Pydantic Models ---
class TeacherCreate(BaseModel):
    name: str
    email: str
    password_hash: str

class ClassCreate(BaseModel):
    class_name: str
    teacher_id: int
    academic_year: str

class StudentCreate(BaseModel):
    name: str
    roll_number: str
    class_id: int

class ExamCreate(BaseModel):
    exam_name: str
    class_id: int
    subject: str
    exam_date: str
    total_marks: int
    answer_key_json: Optional[str] = None
    marking_scheme_json: Optional[str] = None

class AnswerScriptCreate(BaseModel):
    student_id: int
    exam_id: int
    pdf_path: str

class EvaluationData(BaseModel):
    question_number: int
    question_type: str
    extracted_text: str
    marks_obtained: float
    max_marks: float
    confidence_score: float
    needs_review: bool
    feedback: str

class BatchEvaluation(BaseModel):
    script_id: int
    evaluations: List[EvaluationData]


# --- Helper function ---
def safe_insert(table: str, data: dict):
    try:
        record_id = db.insert(table, data)
        if record_id is None:
            raise HTTPException(status_code=400, detail=f"Failed to insert into {table}")
        return record_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


def safe_fetch(table: str, where_clause: str = "", params=()):
    try:
        return db.fetch_all(table, where_clause, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


# --- API Endpoints with exception handling ---
@app.get("/")
def root():
    return {"message": "Answer Evaluator API is running! 🚀"}

@app.post("/teachers/")
def create_teacher(teacher: TeacherCreate):
    teacher_id = safe_insert("teachers", teacher.dict())
    return {"teacher_id": teacher_id, "message": "Teacher created"}

@app.get("/teachers/")
def get_all_teachers():
    teachers = safe_fetch("teachers")
    return {"teachers": teachers}

@app.post("/classes/")
def create_class(class_data: ClassCreate):
    class_id = safe_insert("classes", class_data.dict())
    return {"class_id": class_id, "message": "Class created"}

@app.get("/classes/")
def get_all_classes():
    classes = safe_fetch("classes")
    return {"classes": classes}

@app.post("/students/")
def create_student(student: StudentCreate):
    student_id = safe_insert("students", student.dict())
    return {"student_id": student_id, "message": "Student created"}

@app.get("/students/")
def get_all_students():
    students = safe_fetch("students")
    return {"students": students}

@app.post("/exams/")
def create_exam(exam: ExamCreate):
    exam_id = safe_insert("exams", exam.dict())
    return {"exam_id": exam_id, "message": "Exam created"}

@app.get("/exams/")
def get_all_exams():
    exams = safe_fetch("exams")
    return {"exams": exams}

@app.post("/answer-scripts/")
def create_answer_script(script: AnswerScriptCreate):
    script_id = safe_insert("answer_scripts", script.dict())
    return {"script_id": script_id, "message": "Answer script registered"}

@app.post("/evaluations/batch")
def store_batch_evaluation(batch: BatchEvaluation):
    try:
        db.store_evaluation_batch(batch.script_id, [eval.dict() for eval in batch.evaluations])
        return {"message": f"Stored {len(batch.evaluations)} evaluations for script {batch.script_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store evaluations: {e}")

@app.get("/evaluations/script/{script_id}")
def get_script_evaluations(script_id: int):
    evaluations = safe_fetch("evaluated_answers", "script_id = ?", [script_id])
    return {"script_id": script_id, "evaluations": evaluations}

@app.get("/exams/{exam_id}/results")
def get_exam_results(exam_id: int):
    scripts = safe_fetch("answer_scripts", "exam_id = ?", [exam_id])
    results = []
    for script in scripts:
        script_id = script[0]
        evaluations = safe_fetch("evaluated_answers", "script_id = ?", [script_id])
        results.append({"script_id": script_id, "script_data": script, "evaluations": evaluations})
    return {"exam_id": exam_id, "results": results}

@app.get("/flagged-answers/")
def get_flagged_answers():
    flagged = safe_fetch("evaluated_answers", "needs_review = TRUE")
    return {"flagged_answers": flagged}

@app.get("/status/")
def get_system_status():
    stats = {
        "total_teachers": len(safe_fetch("teachers")),
        "total_classes": len(safe_fetch("classes")),
        "total_students": len(safe_fetch("students")),
        "total_exams": len(safe_fetch("exams")),
        "total_scripts": len(safe_fetch("answer_scripts")),
        "pending_evaluation": len(safe_fetch("answer_scripts", "status = 'uploaded'")),
        "flagged_reviews": len(safe_fetch("evaluated_answers", "needs_review = TRUE"))
    }
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
