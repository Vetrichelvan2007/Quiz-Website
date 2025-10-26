from flask import *
import oracledb
from pyngrok import ngrok
from pyngrok import conf
from datetime import datetime

app = Flask(__name__)

app = Flask(__name__)
app.secret_key = "your_secret_key_here" 

# runn this command in cmd to start ngrok
# C:\Users\vetrichelvan\AppData\Local\Microsoft\WindowsApps\ngrok.exe http 5000

def connectdb():
    try:
        return oracledb.connect(
            user="system",
            password="vetri",
            dsn="localhost:1521/XEPDB1"
        )
    except Exception as e:
        print("Error connecting to DB:", e)
        return None

def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        try:
            connection = connectdb()
            if connection is None:
                return "Database connection failed", 500

            cursor = connection.cursor()

            cursor.execute(
                "SELECT * FROM app_user WHERE username=:1 AND password_hash=:2",
                (username, password)
            )
            user = cursor.fetchone()
            print("User fetched:", user)

            if user and user[4].lower() == "teacher":
                cursor.execute("SELECT * FROM teacher WHERE user_id=:1", (user[0],))
                teacher = cursor.fetchone()
                print("Teacher fetched:", teacher)

                if teacher:
                    session["teacher_id"] = teacher[0]
                    session["teacher_name"] = teacher[2]
                    session["user_id"]=user[0]
                    session["username"] = user[1]
                    session["email"] = user[2]
                    session["password"] = user[3]
                    session["role"] = "teacher"

                    return redirect(url_for("teacher_dashboard"))
            elif user and user[4].lower() == "student":
                cursor.execute("SELECT * FROM student WHERE user_id=:1", (user[0],))
                student = cursor.fetchone()

                if student:
                    class_name=cursor.execute("select class_name from class where class_id=:1",(student[3],)).fetchone()[0]
                    dept_name=cursor.execute("select dept_name from department where dept_id=:1",(student[4],)).fetchone()[0]

                    session["student_id"] = student[0]
                    session["student_name"] = student[2]
                    session["user_id"]=user[0]
                    session["username"] = user[1]
                    session["email"] = user[2]
                    session["password"] = user[3]
                    session["class_id"] = student[3]
                    session["dept_id"] = student[4]
                    session["class_name"] = class_name
                    session["dept_name"] = dept_name
                    session["role"] = "student"
                    return redirect(url_for("student_dashboard"))
                
            
            return render_template("login.html", error="Invalid username or password")

        except Exception as e:
            print("Login error:", e)
            return render_template("login.html", error="Something went wrong")

        finally:
            if connection:
                connection.close()

    return render_template("login.html",error="")

@app.route("/signup", methods=["POST","GET"])
def signup():
    if request.method == "POST":
        
        fullname = (request.form.get("fullname") or "").strip()
        email = (request.form.get("email") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = (request.form.get("password") or "").strip()

       
        if not all([fullname, email, username, password]):
            return "All fields are required!"

        try:
            connection = connectdb()
            cursor = connection.cursor()

            cursor.execute("insert into app_user(user_id, username, email, password_hash, role) values (quser_id_seq.NEXTVAL, :1, :2, :3, 'teacher')",(username.strip(),email.strip(),password.strip()))
            cursor.execute("SELECT quser_id_seq.CURRVAL FROM dual")

            user_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO teacher(teacher_id, user_id, name) VALUES (teacher_id_seq.NEXTVAL, :1, :2)",
                (user_id, fullname)
            )
            connection.commit()
            return redirect(url_for("login"))

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template("signup.html")

@app.route('/dashboard', methods=["POST", "GET"])
def teacher_dashboard():
    if "teacher_id" not in session:
        return redirect(url_for("login"))

    quizzes = []
    stats = {"total_quizzes": 0, "active_quizzes": 0, "total_students": 0}

    try:
        connection = connectdb()
        cursor = connection.cursor()

        query_all = """
            SELECT name, subject, start_date, end_date, duration_minutes, 
                   no_of_question, total_marks, status, quiz_id, class_id, dept_id, 
                   starttime, endtime
            FROM quiz 
            WHERE created_by = :1
            ORDER BY start_date DESC
        """
        cursor.execute(query_all, (int(session["teacher_id"]),))
        all_rows = cursor.fetchall()

        stats["total_quizzes"] = len(all_rows)
        now = datetime.now()
        count=0
        for row in all_rows:
            count+=1
            quiz_id = row[8]
            start_date, end_date = row[2], row[3]
            start_time_str, end_time_str = row[11], row[12]

            # Parse "07:00 pm" and "08:00 am" safely into time objects
            try:
                start_time = datetime.strptime(start_time_str.strip().lower(), "%I:%M %p").time()
            except Exception:
                start_time = datetime.strptime("12:00 am", "%I:%M %p").time()

            try:
                end_time = datetime.strptime(end_time_str.strip().lower(), "%I:%M %p").time()
            except Exception:
                end_time = datetime.strptime("11:59 pm", "%I:%M %p").time()

            # Combine date + time for accurate comparisons
            quiz_start = datetime.combine(start_date, start_time)
            quiz_end = datetime.combine(end_date, end_time)

            current_status = row[7]

            # ✅ Update logic:
            #  - Before start → upcoming
            #  - Between start & end → active
            #  - After end → inactive
            if now < quiz_start and current_status != 'upcoming':
                cursor.execute("UPDATE quiz SET status='upcoming' WHERE quiz_id=:1", (quiz_id,))
                connection.commit()
                current_status = 'upcoming'

            elif quiz_start <= now <= quiz_end and current_status != 'active':
                cursor.execute("UPDATE quiz SET status='active' WHERE quiz_id=:1", (quiz_id,))
                connection.commit()
                current_status = 'active'

            elif now > quiz_end and current_status != 'inactive':
                cursor.execute("UPDATE quiz SET status='inactive' WHERE quiz_id=:1", (quiz_id,))
                connection.commit()
                current_status = 'inactive'

            # Fetch class and department names
            class_name = cursor.execute("SELECT class_name FROM class WHERE class_id=:1", (row[9],)).fetchone()[0]
            dept_name = cursor.execute("SELECT dept_name FROM department WHERE dept_id=:1", (row[10],)).fetchone()[0]

            quiz_data = {
                "name": row[0],
                "subject": row[1],
                "start_date": row[2].strftime("%Y-%m-%d"),
                "end_date": row[3].strftime("%Y-%m-%d"),
                "duration_minutes": row[4],
                "no_of_question": row[5],
                "total_marks": row[6],
                "status": current_status,
                "quiz_id": row[8],
                "class_name": class_name,
                "dept_name": dept_name,
                "starttime": row[11],
                "endtime": row[12]
            }

            if current_status == 'active':
                stats["active_quizzes"] += 1
                quizzes.append(quiz_data)

        # Total students count
        try:
            stats["total_students"] = cursor.execute("SELECT COUNT(*) FROM student").fetchone()[0]
        except:
            stats["total_students"] = 0

        cursor.close()
        connection.close()

    except Exception as e:
        return f"Error: {str(e)}"

    return render_template('teacherhomepage.html', quizzes=quizzes, stats=stats, total_quizzes=count)

@app.route("/editprofile", methods=["GET", "POST"])
def editprofile():
    if "teacher_id" not in session:
        return redirect(url_for("login"))  
    if request.method == "POST":
        teacher_name = request.form.get("teacherName") or session["name"]
        teacher_username = request.form.get("username") or session["username"]
        teacher_email = request.form.get("email") or session["email"]
        teacher_password = request.form.get("password") or session["password"]

        try:
            connection=connectdb()
            cursor=connection.cursor()

            cursor.execute("UPDATE app_user SET username=:1, email=:2, password_hash=:3 WHERE user_id=:4",(teacher_username.strip(),teacher_email.strip(),teacher_password.strip(),session["user_id"]))
            cursor.execute("UPDATE teacher SET name=:1 WHERE user_id=:2",(teacher_name.strip(),session["user_id"]))

            session["username"] = teacher_username
            session["email"] = teacher_email
            session["password"] = teacher_password
            session["name"] = teacher_name

            connection.commit()

            return redirect(url_for('teacher_dashboard'))

        except Exception as e:
            print(e)
    return render_template("editprofile.html", teacher=session)

@app.route("/changepassword", methods=["POST","GET"])
def changepassword():
    if "role" not in session:
        return redirect(url_for("login"))

    role = {}

    if session["role"] == "teacher":
        if "teacher_id" not in session:
            return redirect(url_for("login"))
        role["id"]=session["teacher_id"]
        role["role"]="Teacher"
        role["password"]=session["password"]
        
    elif session["role"] == "student":
        if "student_id" not in session:
            return redirect(url_for("login"))
        role["id"]=session["student_id"]
        role["role"]="Student"
        role["password"]=session["password"]
    else:
        return redirect(url_for("login"))
        
    if request.method == "POST":
        newPassword=request.form.get("newPassword")
        confirmPassword=request.form.get("confirmPassword")
        try:
            connection=connectdb()
            cursor=connection.cursor()

            cursor.execute("UPDATE app_user SET password_hash=:1 where user_id=:2",(newPassword,session["user_id"]))
            session["password"] = newPassword
            connection.commit()
            print(newPassword,confirmPassword)
            return redirect(url_for('teacher_dashboard'))
        except Exception as e:
            print(e)
    return render_template('changepassword.html',role=role)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/get_classes/<deptname>")
def get_classes(deptname):
    connection = connectdb()
    cursor = connection.cursor()

    cursor.execute("SELECT dept_id FROM department WHERE LOWER(dept_name)=LOWER(:1)", (deptname,))
    dept_row = cursor.fetchone()
    if not dept_row:
        return jsonify([])

    dept_id = dept_row[0]
    cursor.execute("SELECT class_name FROM class WHERE dept_id=:1 ORDER BY class_name", (dept_id,))
    classes = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()
    return jsonify(classes)

@app.route("/createquiz", methods=["GET", "POST"])
def createquiz():
    if "teacher_id" not in session:
        return redirect(url_for("login"))

    connection = connectdb()
    cursor = connection.cursor()

    cursor.execute("SELECT dept_name FROM department ORDER BY dept_name")
    departments = [row[0] for row in cursor.fetchall()]

    cursor.close()
    connection.close()

    if request.method == "POST":
        quiz_name = request.form.get("quiz_name").strip()
        subject = request.form.get("subject").strip()
        classname = request.form.get("class").strip()
        deptname = request.form.get("dept").strip()
        no_of_questions = request.form.get("no_of_questions").strip()
        mark_per_question = request.form.get("mark_per_question").strip()
        start_date = request.form.get("start_date")
        start_time = request.form.get("start_time")
        start_ampm = request.form.get("start_ampm")
        end_date = request.form.get("end_date")
        end_time = request.form.get("end_time")
        end_ampm = request.form.get("end_ampm")
        duration = request.form.get("duration_minutes").strip()

        session["quiz_info"] = {
            "quiz_name": quiz_name,
            "subject": subject,
            "class": classname,
            "dept": deptname,
            "no_of_questions": no_of_questions,
            "mark_per_question": mark_per_question,
            "start_date": start_date,
            "start_time": start_time,
            "start_ampm": start_ampm,
            "end_date": end_date,
            "end_time": end_time,
            "end_ampm": end_ampm,
            "duration": duration
        }
        
        return redirect(url_for("add_questions",total_questions=no_of_questions))

    return render_template("createquiz.html", departments=departments)

@app.route("/add_questions/<int:total_questions>", methods=["GET", "POST"])
def add_questions(total_questions):
    
    if "teacher_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        questions = []
        for i in range(1, total_questions + 1):
            question_text = request.form.get(f"question_{i}").strip()
            option1 = request.form.get(f"option1_{i}").strip()
            option2 = request.form.get(f"option2_{i}").strip()
            option3 = request.form.get(f"option3_{i}").strip()
            option4 = request.form.get(f"option4_{i}").strip()
            correct_option = request.form.get(f"correct_option_{i}").strip()

            questions.append({
                "question_text": question_text,
                "options": [option1, option2, option3, option4],
                "correct_option": correct_option
            })
        print(questions)

        try:
            connection = connectdb()
            cursor = connection.cursor()

            quiz_info = session.get("quiz_info", {})

            query="""
                    INSERT INTO quiz (quiz_id, name, subject, class_id, dept_id, no_of_question, mark_per_question,
                    start_date, end_date, duration_minutes, created_by, starttime, endtime)
                    values (quiz_id_seq.NEXTVAL, :1, :2,
                    (SELECT class_id FROM class WHERE class_name=:3),
                    (SELECT dept_id FROM department WHERE dept_name=:4),
                    :5, :6,TO_DATE(:7, 'YYYY-MM-DD'),
                    TO_DATE(:8, 'YYYY-MM-DD'),
                    :9, :10, :11, :12)
            """
            cursor.execute(query,(quiz_info["quiz_name"],quiz_info["subject"],quiz_info["class"],quiz_info["dept"],
                                   int(quiz_info["no_of_questions"]),int(quiz_info["mark_per_question"]),quiz_info["start_date"],quiz_info["end_date"],quiz_info["duration"], session["teacher_id"],f"{quiz_info['start_time']} {quiz_info['start_ampm']}",f"{quiz_info['end_time']} {quiz_info['end_ampm']}"))

            quiz_id = cursor.execute("SELECT quiz_id_seq.CURRVAL FROM dual").fetchone()[0]

            for q in questions:
                cursor.execute("""
                    INSERT INTO quiz_question (question_id, quiz_id, question, op1, op2, op3, op4, correct_answer,mark)
                    VALUES (question_id_seq.NEXTVAL, :1, :2, :3, :4, :5, :6, :7, :8)
                """, (quiz_id, q["question_text"], q["options"][0], q["options"][1], q["options"][2], q["options"][3], q["correct_option"], int(quiz_info["mark_per_question"])))
            connection.commit()
            return redirect(url_for("teacher_dashboard"))
        except Exception as e:
            print(f"Error : {e}")

    return render_template("mcq.html", total_questions=total_questions)

@app.route('/activequizzes')
def activequizzes():
    connection = connectdb()
    cur = connection.cursor()
    
    if session["role"] == "teacher":
        query = """
        SELECT quiz_id, name, subject, class_id, dept_id, no_of_question, 
            mark_per_question, start_date, end_date, duration_minutes, 
            starttime, endtime, status, total_marks
        FROM quiz WHERE created_by = :1
        ORDER BY start_date DESC
        """
        cur.execute(query, (int(session["teacher_id"]),))
    elif session["role"] == "student":
        query = """
            SELECT quiz_id, name, subject, class_id, dept_id, no_of_question, 
                mark_per_question, start_date, end_date, duration_minutes, 
                starttime, endtime, status, total_marks
            FROM quiz WHERE class_id = :1 and status='inactive'
            ORDER BY start_date DESC
        """
        cur.execute(query, (int(session["class_id"]),))
    
    quizzes = []
    for row in cur:
        quizzes.append({
            "quiz_id": row[0],
            "name": row[1],
            "subject": row[2],
            "class_id": row[3],
            "dept_id": row[4],
            "no_of_question": row[5],
            "mark_per_question": row[6],
            "start_date": row[7].strftime("%Y-%m-%d"),
            "end_date": row[8].strftime("%Y-%m-%d"),
            "DURATION_MINUTES": row[9],  # Changed to match template
            "starttime": row[10],
            "endtime": row[11],
            "status": row[12],
            "total_marks": row[13]
        })
    
    cur.close()
    connection.close()
    
    return render_template(
        'activequizzes.html',
        quizzes=quizzes,
        student_id=session.get("student_id"),
        role=session.get("role")
    )   

@app.route("/addstudent", methods=["POST","GET"])
def addstudent():
    if request.method == "POST":
        studentName = request.form.get("studentName").strip()
        studentClass = request.form.get("studentClass").strip()
        studentDept = request.form.get("studentDept").strip()
        email = request.form.get("email").strip()
        password = request.form.get("password").strip()

        try:
            connection = connectdb()
            cursor = connection.cursor()

            cursor.execute("""INSERT INTO app_user(user_id, username, email, password_hash, role) VALUES (quser_id_seq.NEXTVAL, :1||quser_id_seq.CURRVAL, :2, :3, 'student')""", (studentName, email, password))
            cursor.execute("SELECT quser_id_seq.CURRVAL FROM dual")
            user_id = cursor.fetchone()[0] 

            cursor.execute("SELECT class_id, dept_id FROM class WHERE lower(class_name )= :1", (studentClass.lower(),))
            class_row = cursor.fetchone()

            if class_row:
                class_id, dept_id = class_row
            else:
                cursor.execute("SELECT dept_id FROM department WHERE dept_name = :1", (studentDept,))
                dept_row = cursor.fetchone()
                if not dept_row:
                   
                    cursor.execute("INSERT INTO department(dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, :1)", (studentDept,))
                    cursor.execute("SELECT dept_id_seq.CURRVAL FROM dual")
                    dept_id = cursor.fetchone()[0]
                else:
                    dept_id = dept_row[0]

                cursor.execute("INSERT INTO class(class_id, class_name, dept_id) VALUES (class_id_seq.NEXTVAL, :1, :2)", (studentClass, dept_id))
                cursor.execute("SELECT class_id_seq.CURRVAL FROM dual")
                class_id = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO student(student_id, user_id, name, class_id, dept_id)
                VALUES (student_id_seq.NEXTVAL, :1, :2, :3, :4)
            """, (user_id, studentName, class_id, dept_id))

            connection.commit()

        except Exception as e:
            connection.rollback()
            print("Error:", e)
        finally:
            cursor.close()
            connection.close()
    return render_template('addstudent.html')

@app.route('/viewstudents', methods=["GET", "POST"])
def viewstudents():
    students = []
    departments = ["AIDS", "CSC", "ECE", "AIML", "IT", "EEE"]

   
    if request.method == 'POST':
        delete_id = request.form.get('delete_id')
        if delete_id:
            try:
                delete_id = int(delete_id)  
                connection = connectdb()
                cursor = connection.cursor()

                
                cursor.execute("SELECT user_id FROM student WHERE student_id = :1", (delete_id,))
                user_row = cursor.fetchone()

                if user_row:
                    user_id = user_row[0]

                    
                    cursor.execute("DELETE FROM result_for_each_question WHERE student_id = :1", (delete_id,))
                    cursor.execute("DELETE FROM result_for_quiz WHERE student_id = :1", (delete_id,))

                    
                    cursor.execute("DELETE FROM student WHERE student_id = :1", (delete_id,))

                    
                    cursor.execute("DELETE FROM app_user WHERE user_id = :1", (user_id,))

                    connection.commit()
                    flash("Student deleted successfully!", "success")
                else:
                    flash("Student not found!", "warning")

            except Exception as e:
                connection.rollback()
                flash(f"Error deleting student: {e}", "danger")
            finally:
                cursor.close()
                connection.close()

    
    try:
        connection = connectdb()
        cursor = connection.cursor()

        query = """
        SELECT s.student_id, s.name, u.email, u.username, u.password_hash,
               c.class_name, d.dept_name
        FROM student s
        JOIN app_user u ON s.user_id = u.user_id
        JOIN class c ON s.class_id = c.class_id
        JOIN department d ON s.dept_id = d.dept_id
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            students.append({
                "student_id": row[0],
                "name": row[1],
                "email": row[2],
                "username": row[3],
                "password": row[4],
                "class_name": row[5],
                "department": row[6]
            })

        if not students:
            students = [{
                "student_id": 0,
                "name": "N/A",
                "email": "N/A",
                "username": "N/A",
                "password": "N/A",
                "class_name": "N/A",
                "department": "N/A"
            }]

    except Exception as e:
        flash(f"Error fetching students: {e}", "danger")
    finally:
        cursor.close()
        connection.close()

    return render_template('viewstudents.html', students=students, departments=departments)

@app.route('/editstudent/<int:student_id>', methods=["GET", "POST"])
def editstudent(student_id):
    student = None
    try:
        connection = connectdb()
        cursor = connection.cursor()

        # Fetch current student info with JOIN
        query = """
        SELECT s.student_id, s.name, u.email, u.username, u.password_hash,
               c.class_name, d.dept_name
        FROM student s
        JOIN app_user u ON s.user_id = u.user_id
        JOIN class c ON s.class_id = c.class_id
        JOIN department d ON s.dept_id = d.dept_id
        WHERE s.student_id = :1
        """
        cursor.execute(query, (student_id,))
        row = cursor.fetchone()

        if row:
            student = {
                "student_id": row[0],
                "name": row[1],
                "email": row[2],
                "username": row[3],
                "password": row[4],
                "class_name": row[5],
                "department": row[6]
            }
        else:
            return "Student not found", 404

    except Exception as e:
        print("Error fetching student:", e)
        return "Internal Server Error", 500
    finally:
        if connection:
            cursor.close()
            connection.close()

    # Handle POST
    if request.method == "POST":
        student_id = int(request.form.get("student_id"))
        studentName = request.form.get("name")
        studentClass = request.form.get("class_name")
        studentDept = request.form.get("department")
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            connection = connectdb()
            cursor = connection.cursor()

            # 1. Update user info
            cursor.execute("""
                UPDATE app_user 
                SET email = :1, password_hash = :2 
                WHERE user_id = (SELECT user_id FROM student WHERE student_id = :3)
            """, (email, password, student_id))

            # 2. Update student name
            cursor.execute("""
                UPDATE student SET name = :1 WHERE student_id = :2
            """, (studentName, student_id))

            # 3. Check if department exists
            cursor.execute("SELECT dept_id FROM department WHERE dept_name = :1", (studentDept,))
            deptdetails = cursor.fetchone()

            if not deptdetails:
                cursor.execute(
                    "INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, :1)",
                    (studentDept,)
                )
                cursor.execute("SELECT dept_id FROM department WHERE dept_name = :1", (studentDept,))
                deptdetails = cursor.fetchone()

            dept_id = deptdetails[0]

            # 4. Check if class exists
            cursor.execute("SELECT class_id FROM class WHERE class_name = :1", (studentClass,))
            classdetails = cursor.fetchone()

            if not classdetails:
                cursor.execute("""
                    INSERT INTO class (class_id, class_name, dept_id) 
                    VALUES (class_id_seq.NEXTVAL, :1, :2)
                """, (studentClass, dept_id))
                cursor.execute("SELECT class_id FROM class WHERE class_name = :1", (studentClass,))
                classdetails = cursor.fetchone()

            class_id = classdetails[0]

            cursor.execute("""
                UPDATE student
                SET class_id = :1,
                    dept_id = :2
                WHERE student_id = :3
            """, (class_id, dept_id, student_id))

            connection.commit()
            return redirect(url_for('viewstudents'))

        except Exception as e:
            if connection:
                connection.rollback()
            print("Error updating student:", e)
        finally:
            if connection:
                cursor.close()
                connection.close()

    return render_template('editstudent.html', student=student)

@app.route("/student_dashboard")
def student_dashboard():
    student_id = session.get("student_id")
    class_id = session.get("class_id")
    if not student_id:
        return redirect(url_for("login"))

    quizzes = []

    try:
        connection = connectdb()
        cursor = connection.cursor()

        now = datetime.now()

        query = """
            SELECT quiz_id, name, subject, start_date, end_date, duration_minutes, no_of_question, mark_per_question, starttime, endtime, status
            FROM quiz
            WHERE class_id = :1
            ORDER BY start_date ASC
        """
        cursor.execute(query, (class_id,))

        for row in cursor.fetchall():
            quiz_id, name, subject, start_date, end_date, duration_minutes, no_of_question, mark_per_question, starttime_str, endtime_str, status = row

            # Parse start and end times
            try:
                start_time = datetime.strptime(starttime_str.strip().lower(), "%I:%M %p").time()
            except:
                start_time = datetime.strptime("12:00 AM", "%I:%M %p").time()

            try:
                end_time = datetime.strptime(endtime_str.strip().lower(), "%I:%M %p").time()
            except:
                end_time = datetime.strptime("11:59 PM", "%I:%M %p").time()

            # Combine with dates
            quiz_start = datetime.combine(start_date, start_time)
            quiz_end = datetime.combine(end_date, end_time)

            # Update status based on current datetime
            if now < quiz_start and status != 'upcoming':
                cursor.execute("UPDATE quiz SET status='upcoming' WHERE quiz_id=:1", (quiz_id,))
                connection.commit()
                status = 'upcoming'
            elif quiz_start <= now <= quiz_end and status != 'active':
                cursor.execute("UPDATE quiz SET status='active' WHERE quiz_id=:1", (quiz_id,))
                connection.commit()
                status = 'active'
            elif now > quiz_end and status != 'inactive':
                cursor.execute("UPDATE quiz SET status='inactive' WHERE quiz_id=:1", (quiz_id,))
                connection.commit()
                status = 'inactive'

            # Only show active quizzes
            if status == 'active':
                quizzes.append({
                    'quiz_id': quiz_id,
                    'name': name,
                    'subject': subject,
                    'start_date': start_date.strftime("%Y-%m-%d"),
                    'end_date': end_date.strftime("%Y-%m-%d"),
                    'duration_minutes': duration_minutes,
                    'no_of_question': no_of_question,
                    'mark_per_question': mark_per_question,
                    'starttime': starttime_str,
                    'endtime': endtime_str,
                    'status': status
                })

    except Exception as e:
        print(f"Error: {e}")

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template("studenthomepage.html", quizzes=quizzes)

@app.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def quiz(quiz_id):
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for('login'))

    conn = None
    cursor = None

    try:
        conn = connectdb()
        cursor = conn.cursor()

        # Check if student already attempted
        cursor.execute("""
            SELECT COUNT(*) FROM result_for_quiz
            WHERE quiz_id = :quiz_id AND student_id = :student_id
        """, {"quiz_id": quiz_id, "student_id": student_id})
        if cursor.fetchone()[0] > 0:
            return redirect(url_for('show_result', student_id=student_id, quiz_id=quiz_id))

        # ✅ FETCH start_date and starttime to validate access
        cursor.execute("""
            SELECT start_date, starttime, duration_minutes
            FROM quiz
            WHERE quiz_id = :1
        """, (quiz_id,))
        quiz_row = cursor.fetchone()

        if not quiz_row:
            return "<h3>❌ Quiz not found.</h3>"

        start_date, start_time_str, duration_minutes = quiz_row

        # Combine date and time
        try:
            # Convert "08:00 AM" to time object
            start_time_obj = datetime.strptime(start_time_str.strip(), "%I:%M %p").time()
        except ValueError:
            return "<h3>⚠️ Invalid start time format in DB. Use format like '08:00 AM'.</h3>"

        quiz_start_datetime = datetime.combine(start_date, start_time_obj)
        current_datetime = datetime.now()

        if current_datetime < quiz_start_datetime:
            return f"<h3>⏳ The quiz hasn't started yet. It will be available at {start_time_str} on {start_date.strftime('%Y-%m-%d')}.</h3>"

        # ✅ Quiz has started, continue...

        if request.method == 'POST':
            answers = {}
            for key, val in request.form.items():
                if key.startswith('q'):
                    qid = int(key[1:])
                    answers[qid] = val if val else None

            cursor.execute("""
                INSERT INTO result_for_quiz (result_id, quiz_id, student_id, total_mark)
                VALUES (result_for_quiz_seq.NEXTVAL, :quiz_id, :student_id, 0)
            """, {"quiz_id": quiz_id, "student_id": student_id})

            cursor.execute("SELECT result_for_quiz_seq.CURRVAL FROM dual")
            result_id = cursor.fetchone()[0]

            total_marks = 0

            for question_id, student_ans in answers.items():
                cursor.execute("""
                    SELECT question, op1, op2, op3, op4, correct_answer, mark
                    FROM quiz_question
                    WHERE question_id = :qid
                """, {"qid": question_id})
                row = cursor.fetchone()

                if not row:
                    continue

                question_text, op1, op2, op3, op4, correct_answer, mark_per_question = row

                if hasattr(question_text, "read"):
                    question_text = question_text.read()

                obtained_mark = mark_per_question if student_ans == correct_answer else 0
                total_marks += obtained_mark

                cursor.execute("""
                    INSERT INTO result_for_each_question (
                        result_for_each_question_id,
                        quiz_id,
                        question_id,
                        student_id,
                        question,
                        op1, op2, op3, op4,
                        crt_ans,
                        student_ans
                    )
                    VALUES (
                        result_for_each_question_seq.NEXTVAL,
                        :quiz_id,
                        :question_id,
                        :student_id,
                        :question,
                        :op1, :op2, :op3, :op4,
                        :crt_ans,
                        :student_ans
                    )
                """, {
                    "quiz_id": quiz_id,
                    "question_id": question_id,
                    "student_id": student_id,
                    "question": str(question_text),
                    "op1": str(op1),
                    "op2": str(op2),
                    "op3": str(op3),
                    "op4": str(op4),
                    "crt_ans": correct_answer,
                    "student_ans": student_ans
                })

            cursor.execute("""
                UPDATE result_for_quiz
                SET total_mark = :total
                WHERE result_id = :rid
            """, {"total": total_marks, "rid": result_id})

            conn.commit()
            return redirect(url_for('student_dashboard'))
            # return redirect(url_for('show_result', student_id=student_id, quiz_id=quiz_id))


        # ✅ If GET method, fetch quiz questions
        cursor.execute("""
            SELECT question_id, question, op1, op2, op3, op4
            FROM quiz_question
            WHERE quiz_id = :quiz_id
        """, {"quiz_id": quiz_id})

        rows = cursor.fetchall()

        quiz_data = []
        for r in rows:
            question_text = r[1]
            if hasattr(question_text, "read"):
                question_text = question_text.read()

            quiz_data.append({
                "question_id": r[0],
                "question": str(question_text),
                "option1": str(r[2]),
                "option2": str(r[3]),
                "option3": str(r[4]),
                "option4": str(r[5])
            })

        if not quiz_data:
            return "<h3>⚠️ No questions found for this quiz.</h3>"

        duration = duration_minutes * 60  # seconds

        return render_template("attendquiz.html", quiz_data=quiz_data, duration=duration)

    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        return f"<h3>❌ An error occurred: {str(e)}</h3>"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
         
@app.route('/result/<int:student_id>/<int:quiz_id>')
def show_result(student_id, quiz_id):
    conn = None
    cursor = None
    try:
        conn = connectdb()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT total_mark 
            FROM result_for_quiz 
            WHERE quiz_id = :1 AND student_id = :2
        """, (quiz_id, student_id))
        row = cursor.fetchone()
        if not row:
            return "<h3>Result not found!</h3>"
        total_mark = row[0]

        cursor.execute("""
            SELECT question, op1, op2, op3, op4, crt_ans, student_ans
            FROM result_for_each_question
            WHERE quiz_id = :1 AND student_id = :2
            ORDER BY result_for_each_question_id
        """, (quiz_id, student_id))

        questions = []
        for q in cursor.fetchall():
            question_text, op1, op2, op3, op4, crt_ans, student_ans = q
            options = [op1, op2, op3, op4]
            correct = student_ans == crt_ans

            student_text = options[int(student_ans[-1]) - 1] if student_ans else ""
            crt_text = options[int(crt_ans[-1]) - 1]

            questions.append({
                "question": question_text,
                "options": options,
                "crt_ans": crt_ans,
                "student_ans": student_ans,
                "correct": correct,
                "student_text": student_text,
                "crt_text": crt_text
            })
        cursor.execute("select total_marks from quiz where quiz_id=:1",(quiz_id,))
        total_marks=cursor.fetchone()[0]    
        return render_template("show_result.html",
                               total_mark=total_mark,
                               questions=questions,total_marks=total_marks)

    except Exception as e:
        if conn:
            conn.rollback()
        return f"Error: {str(e)}"

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/overallresults/<int:quiz_id>',methods=["GET","POST"])
def overallresults(quiz_id):
    if 'teacher_id' not in session:
        return redirect(url_for("login"))

    
    try:
        connection=connectdb()
        cursor=connection.cursor()

        cursor.execute("select trunc(start_date) from quiz where quiz_id=:1",(quiz_id,))

        start_date=cursor.fetchone()[0]
        cur_date=datetime.now().date()

        if isinstance(start_date, datetime):
            start_date = start_date.date()  

        cur_date = datetime.now().date()

        if cur_date < start_date:
            return "<h3>Overall results will be available after the quiz date.</h3>"
        else:
            print("Quiz is active.")

            
        query="""SELECT 
                    s.name AS student_name,
                    r.quiz_id,
                    r.total_mark,
                    s.student_id,
                    q.total_marks AS quiz_total_marks
                FROM result_for_quiz r
                JOIN student s ON r.student_id = s.student_id
                JOIN quiz q ON r.quiz_id = q.quiz_id
                WHERE r.quiz_id = :1
                ORDER BY s.name ASC
            """
        cursor.execute(query,(quiz_id,))
        results =cursor.fetchall()

        students = []
        for result in results:
            students.append({
                "name": result[0],
                "quiz_id": result[1],
                "marks": result[2],
                "student_id": result[3],
                "total_marks": result[4]
            })
    except Exception as e:
        print(f"Error fetching overall results: {e}")
        students = []

    return render_template("overallresults.html",students=students,quiz_id=quiz_id)

@app.route('/studentprofile')
def studentprofile():
    if "student_id" not in session:
        return redirect(url_for("login"))  
    return render_template("studentprofile.html", student=session)

@app.route("/editstudentprofile", methods=["GET", "POST"])
def editstudentprofile():
    if "student_id" not in session:
        return redirect(url_for("login"))  
    return render_template("editstudentprofile.html", student=session)

@app.route("/edit_quiz/<int:quiz_id>", methods=["GET", "POST"])
def edit_quiz(quiz_id):
    if "teacher_id" not in session:
        return redirect(url_for("login"))

    connection = connectdb()
    cursor = connection.cursor()

    try:
        if request.method == "POST":
            # Get form data
            quiz_name = request.form.get("quiz_name").strip()
            subject = request.form.get("subject").strip()
            classname = request.form.get("classname").strip()
            deptname = request.form.get("deptname").strip()
            duration = int(request.form.get("duration") or 0)
            start_date = request.form.get("start_date")
            start_time = request.form.get("start_time")
            start_ampm = request.form.get("start_ampm")
            end_date = request.form.get("end_date")
            end_time = request.form.get("end_time")
            end_ampm = request.form.get("end_ampm")

            # 1️⃣ Basic validations
            if not quiz_name:
                flash("Quiz name cannot be empty!", "error")
                return redirect(url_for("edit_quiz", quiz_id=quiz_id))
            if not subject:
                flash("Subject cannot be empty!", "error")
                return redirect(url_for("edit_quiz", quiz_id=quiz_id))
            if duration <= 0:
                flash("Duration must be greater than 0!", "error")
                return redirect(url_for("edit_quiz", quiz_id=quiz_id))

            # 2️⃣ Validate class exists
            cursor.execute("SELECT class_id FROM class WHERE class_name=:1", (classname,))
            class_row = cursor.fetchone()
            if not class_row:
                flash(f"Class '{classname}' does not exist!", "error")
                return redirect(url_for("edit_quiz", quiz_id=quiz_id))
            class_id = class_row[0]

            # 3️⃣ Validate department exists
            cursor.execute("SELECT dept_id FROM department WHERE dept_name=:1", (deptname,))
            dept_row = cursor.fetchone()
            if not dept_row:
                flash(f"Department '{deptname}' does not exist!", "error")
                return redirect(url_for("edit_quiz", quiz_id=quiz_id))
            dept_id = dept_row[0]

            # 4️⃣ Validate start < end datetime
            start_dt = datetime.strptime(f"{start_date} {start_time} {start_ampm}", "%Y-%m-%d %I:%M %p")
            end_dt = datetime.strptime(f"{end_date} {end_time} {end_ampm}", "%Y-%m-%d %I:%M %p")
            if start_dt >= end_dt:
                flash("Start date/time must be before end date/time!", "error")
                return redirect(url_for("edit_quiz", quiz_id=quiz_id))

            # 5️⃣ Determine status
            status = "active" if end_dt > datetime.now() else "inactive"

            # 6️⃣ Update quiz including status
            cursor.execute("""
                UPDATE quiz SET 
                    name=:1, 
                    subject=:2, 
                    class_id=:3, 
                    dept_id=:4, 
                    duration_minutes=:5, 
                    start_date=TO_DATE(:6, 'YYYY-MM-DD'), 
                    starttime=:7, 
                    end_date=TO_DATE(:8, 'YYYY-MM-DD'), 
                    endtime=:9,
                    status=:10
                WHERE quiz_id=:11
            """, (
                quiz_name, subject, class_id, dept_id, duration,
                start_date, f"{start_time} {start_ampm}",
                end_date, f"{end_time} {end_ampm}", status, quiz_id
            ))
            connection.commit()
            flash("Quiz updated successfully!", "success")
            return redirect(url_for("activequizzes"))

        # GET request: fetch quiz info
        cursor.execute("SELECT * FROM quiz WHERE quiz_id=:1", (quiz_id,))
        quiz_row = cursor.fetchone()

        cursor.execute("SELECT class_name FROM class WHERE class_id=:1", (quiz_row[3],))
        class_name = cursor.fetchone()[0]

        cursor.execute("SELECT dept_name FROM department WHERE dept_id=:1", (quiz_row[4],))
        dept_name = cursor.fetchone()[0]

        quiz = {
            'quiz_id': quiz_id,
            'quiz_name': quiz_row[1],
            'subject': quiz_row[2],
            'classname': class_name,
            'deptname': dept_name,
            'duration': quiz_row[9],
            'start_date': quiz_row[7].strftime("%Y-%m-%d"),
            'start_time': quiz_row[11].split()[0],
            'start_ampm': quiz_row[11].split()[1],
            'end_date': quiz_row[8].strftime("%Y-%m-%d"),
            'end_time': quiz_row[12].split()[0],
            'end_ampm': quiz_row[12].split()[1]
        }

    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}", "danger")
        return redirect(url_for("activequizzes"))

    finally:
        cursor.close()
        connection.close()

    return render_template("edit_quiz.html", quiz=quiz)

if __name__ == "__main__":
  
    app.run( debug=True, port=5000) 