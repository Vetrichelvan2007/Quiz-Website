--------------------------------------------------
-- Department Table
--------------------------------------------------
CREATE TABLE department (
    dept_id NUMBER  PRIMARY KEY,
    dept_name VARCHAR2(100) UNIQUE NOT NULL
);
CREATE SEQUENCE dept_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;
--------------------------------------------------
-- Class Table
--------------------------------------------------
CREATE TABLE class (
    class_id NUMBER PRIMARY KEY,
    class_name VARCHAR2(100) NOT NULL,
    dept_id NUMBER NOT NULL,
    CONSTRAINT fk_class_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id)
);
CREATE SEQUENCE class_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;
--------------------------------------------------
-- User Table (common for all logins)
--------------------------------------------------
CREATE TABLE app_user (
    user_id NUMBER PRIMARY KEY,
    username VARCHAR2(50) UNIQUE NOT NULL,
    email VARCHAR2(100) UNIQUE NOT NULL,
    password_hash VARCHAR2(255) NOT NULL,
    role VARCHAR2(20) CHECK (role IN ('student','teacher','admin')) NOT NULL
);
CREATE SEQUENCE quser_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;
--------------------------------------------------
-- Teacher Table (extra teacher info)
--------------------------------------------------
CREATE TABLE teacher (
    teacher_id NUMBER PRIMARY KEY,
    user_id NUMBER NOT NULL UNIQUE,
    name VARCHAR2(100) NOT NULL,
    CONSTRAINT fk_teacher_user FOREIGN KEY (user_id) REFERENCES app_user(user_id)
);
CREATE SEQUENCE teacher_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;
    
--------------------------------------------------
-- Student Table (extra student info)
--------------------------------------------------

CREATE TABLE student (
    student_id NUMBER PRIMARY KEY,
    user_id NUMBER NOT NULL UNIQUE,
    name VARCHAR2(100) NOT NULL,
    class_id NUMBER NOT NULL,
    dept_id NUMBER NOT NULL,
    CONSTRAINT fk_student_user FOREIGN KEY (user_id) REFERENCES app_user(user_id),
    CONSTRAINT fk_student_class FOREIGN KEY (class_id) REFERENCES class(class_id),
    CONSTRAINT fk_student_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id)
);
CREATE SEQUENCE student_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;
--------------------------------------------------
-- Quiz Table
--------------------------------------------------
CREATE TABLE quiz (
    quiz_id NUMBER PRIMARY KEY,
    name VARCHAR2(100) NOT NULL,
    subject VARCHAR2(100) NOT NULL,
    class_id NUMBER NOT NULL,
    dept_id NUMBER NOT NULL,
    no_of_question NUMBER DEFAULT 10 NOT NULL,
    mark_per_question NUMBER DEFAULT 1 NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_minutes NUMBER NOT NULL,
    created_by NUMBER NOT NULL,
    starttime varchar2(10),
    endtime varchar2(10),
    status varchar2(20) default 'active',
    total_marks NUMBER GENERATED ALWAYS AS (no_of_question * mark_per_question) VIRTUAL,
    CONSTRAINT fk_quiz_class FOREIGN KEY (class_id) REFERENCES class(class_id),
    CONSTRAINT fk_quiz_dept FOREIGN KEY (dept_id) REFERENCES department(dept_id),
    CONSTRAINT fk_quiz_teacher FOREIGN KEY (created_by) REFERENCES teacher(teacher_id)
);
CREATE SEQUENCE quiz_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;

--------------------------------------------------
-- Quiz Questions Table
--------------------------------------------------
CREATE TABLE quiz_question (
    question_id NUMBER PRIMARY KEY,
    quiz_id NUMBER NOT NULL,
    question CLOB NOT NULL,
    op1 VARCHAR2(255) NOT NULL,
    op2 VARCHAR2(255) NOT NULL,
    op3 VARCHAR2(255) NOT NULL,
    op4 VARCHAR2(255) NOT NULL,
    correct_answer VARCHAR2(5) CHECK (correct_answer IN ('op1','op2','op3','op4')) NOT NULL,
    mark NUMBER DEFAULT 1 NOT NULL,
    CONSTRAINT fk_question_quiz FOREIGN KEY (quiz_id) REFERENCES quiz(quiz_id)
);
CREATE SEQUENCE question_id_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;

--------------------------------------------------
-- Result for Each Question Table
--------------------------------------------------
CREATE TABLE result_for_each_question (
    result_for_each_question_id NUMBER PRIMARY KEY,
    quiz_id NUMBER NOT NULL,
    question_id NUMBER NOT NULL,
    student_id NUMBER NOT NULL,
    question VARCHAR2(500) NOT NULL,
    op1 VARCHAR2(100) NOT NULL,
    op2 VARCHAR2(100) NOT NULL,
    op3 VARCHAR2(100) NOT NULL,
    op4 VARCHAR2(100) NOT NULL,
    crt_ans VARCHAR2(5) CHECK (crt_ans IN ('op1','op2','op3','op4')) NOT NULL,
    student_ans VARCHAR2(5) DEFAULT NULL
        CHECK (student_ans IN ('op1','op2','op3','op4') OR student_ans IS NULL),
    CONSTRAINT fk_rfeq_quiz FOREIGN KEY (quiz_id) REFERENCES quiz(quiz_id),
    CONSTRAINT fk_rfeq_question FOREIGN KEY (question_id) REFERENCES quiz_question(question_id),
    CONSTRAINT fk_rfeq_student FOREIGN KEY (student_id) REFERENCES student(student_id)
);

CREATE SEQUENCE result_for_each_question_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;

--------------------------------------------------
-- Result for Quiz Table
--------------------------------------------------
CREATE TABLE result_for_quiz (
    result_id NUMBER PRIMARY KEY,
    quiz_id NUMBER NOT NULL,
    student_id NUMBER NOT NULL,
    total_mark NUMBER DEFAULT 0,
    CONSTRAINT fk_rfq_quiz FOREIGN KEY (quiz_id) REFERENCES quiz(quiz_id),
    CONSTRAINT fk_rfq_student FOREIGN KEY (student_id) REFERENCES student(student_id)
);

CREATE SEQUENCE result_for_quiz_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE;


SELECT * FROM department;
SELECT * FROM class;
SELECT * FROM app_user;
SELECT * FROM teacher;
SELECT * FROM student;
SELECT * FROM quiz;
SELECT * FROM quiz_question;
SELECT * FROM result_for_each_question;
SELECT * FROM result_for_quiz;

TRUNCATE TABLE result_for_quiz;
TRUNCATE TABLE result_for_each_question;
TRUNCATE TABLE quiz_question;
TRUNCATE TABLE quiz;
TRUNCATE TABLE student;
TRUNCATE TABLE teacher;
TRUNCATE TABLE app_user;
TRUNCATE TABLE class;
TRUNCATE TABLE department;


DROP SEQUENCE dept_id_seq;
DROP SEQUENCE class_id_seq;
DROP SEQUENCE quser_id_seq;
DROP SEQUENCE teacher_id_seq;
DROP SEQUENCE student_id_seq;
DROP SEQUENCE quiz_id_seq;
DROP SEQUENCE question_id_seq;
DROP SEQUENCE result_for_each_question_seq;
DROP SEQUENCE result_for_quiz_seq;

-- Drop child tables first
DROP TABLE result_for_quiz CASCADE CONSTRAINTS;
DROP TABLE result_for_each_question CASCADE CONSTRAINTS;
DROP TABLE quiz_question CASCADE CONSTRAINTS;
DROP TABLE quiz CASCADE CONSTRAINTS;
DROP TABLE student CASCADE CONSTRAINTS;
DROP TABLE teacher CASCADE CONSTRAINTS;
DROP TABLE app_user CASCADE CONSTRAINTS;
DROP TABLE class CASCADE CONSTRAINTS;
DROP TABLE department CASCADE CONSTRAINTS;
------------------------------------------------------------
-- SAMPLE DATA INSERT SCRIPT
------------------------------------------------------------
--------------------------------------------------
-- Departments
--------------------------------------------------
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'AIDS');
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'AIML');
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'IT');
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'CSC');
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'ECE');
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'EEE');
INSERT INTO department (dept_id, dept_name) VALUES (dept_id_seq.NEXTVAL, 'MECH');

--------------------------------------------------
-- Classes
--------------------------------------------------
INSERT INTO class (class_id, class_name, dept_id) VALUES (class_id_seq.NEXTVAL, 'AIDS 1', 1);
INSERT INTO class (class_id, class_name, dept_id) VALUES (class_id_seq.NEXTVAL, 'AIML 1', 2);

--------------------------------------------------
-- App Users
--------------------------------------------------
INSERT INTO app_user (user_id, username, email, password_hash, role) 
VALUES (quser_id_seq.NEXTVAL, 'teacher1', 'teacher1@example.com', 'hashedpwd1', 'teacher');
INSERT INTO app_user (user_id, username, email, password_hash, role) 
VALUES (quser_id_seq.NEXTVAL, 'student1', 'student1@example.com', 'hashedpwd2', 'student');
INSERT INTO app_user (user_id, username, email, password_hash, role) 
VALUES (quser_id_seq.NEXTVAL, 'student2', 'student2@example.com', 'hashedpwd3', 'student');

--------------------------------------------------
-- Teachers
--------------------------------------------------
INSERT INTO teacher (teacher_id, user_id, name) VALUES (teacher_id_seq.NEXTVAL, 1, 'Alice Johnson');

--------------------------------------------------
-- Students
--------------------------------------------------
INSERT INTO student (student_id, user_id, name, class_id, dept_id) 
VALUES (student_id_seq.NEXTVAL, 2, 'Bob Smith', 1, 1);
INSERT INTO student (student_id, user_id, name, class_id, dept_id) 
VALUES (student_id_seq.NEXTVAL, 3, 'Carol Lee', 1, 1);

--------------------------------------------------
-- Quiz 1
--------------------------------------------------
INSERT INTO quiz (quiz_id, name, subject, class_id, dept_id, no_of_question, mark_per_question, start_date, end_date, duration_minutes, created_by, starttime, endtime) 
VALUES (quiz_id_seq.NEXTVAL, 'Python Basics', 'Python', 1, 1, 5, 1, 
TO_DATE('2025-10-25','YYYY-MM-DD'), TO_DATE('2025-10-25','YYYY-MM-DD'), 30, 1, '08:00 am', '08:30 am');

--------------------------------------------------
-- Quiz 1 Questions
--------------------------------------------------
INSERT INTO quiz_question (question_id, quiz_id, question, op1, op2, op3, op4, correct_answer, mark) 
VALUES (question_id_seq.NEXTVAL, 1, 'What is Python?', 'A snake', 'A programming language', 'A movie', 'A game', 'op2', 1);

INSERT INTO quiz_question (question_id, quiz_id, question, op1, op2, op3, op4, correct_answer, mark) 
VALUES (question_id_seq.NEXTVAL, 1, 'Which keyword defines a function?', 'fun', 'define', 'def', 'function', 'op3', 1);

INSERT INTO quiz_question (question_id, quiz_id, question, op1, op2, op3, op4, correct_answer, mark) 
VALUES (question_id_seq.NEXTVAL, 1, 'Which data type is immutable?', 'List', 'Dictionary', 'Tuple', 'Set', 'op3', 1);

INSERT INTO quiz_question (question_id, quiz_id, question, op1, op2, op3, op4, correct_answer, mark) 
VALUES (question_id_seq.NEXTVAL, 1, 'What does len() function do?', 'Adds elements', 'Returns length', 'Deletes element', 'None', 'op2', 1);

INSERT INTO quiz_question (question_id, quiz_id, question, op1, op2, op3, op4, correct_answer, mark) 
VALUES (question_id_seq.NEXTVAL, 1, 'Which operator is for exponent?', '+', '-', '**', '%', 'op3', 1);

--------------------------------------------------
-- Results for Each Question (Student 1)
--------------------------------------------------
INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 1, 1, 'What is Python?', 'A snake', 'A programming language', 'A movie', 'A game', 'op2', 'op2');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 2, 1, 'Which keyword defines a function?', 'fun', 'define', 'def', 'function', 'op3', 'op3');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 3, 1, 'Which data type is immutable?', 'List', 'Dictionary', 'Tuple', 'Set', 'op3', 'op3');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 4, 1, 'What does len() function do?', 'Adds elements', 'Returns length', 'Deletes element', 'None', 'op2', 'op2');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 5, 1, 'Which operator is for exponent?', '+', '-', '**', '%', 'op3', 'op3');

--------------------------------------------------
-- Results for Each Question (Student 2)
--------------------------------------------------
INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 1, 2, 'What is Python?', 'A snake', 'A programming language', 'A movie', 'A game', 'op2', 'op1');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 2, 2, 'Which keyword defines a function?', 'fun', 'define', 'def', 'function', 'op3', 'op3');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 3, 2, 'Which data type is immutable?', 'List', 'Dictionary', 'Tuple', 'Set', 'op3', 'op3');

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 4, 2, 'What does len() function do?', 'Adds elements', 'Returns length', 'Deletes element', 'None', 'op2', NULL); -- student skipped

INSERT INTO result_for_each_question (result_for_each_question_id, quiz_id, question_id, student_id, question, op1, op2, op3, op4, crt_ans, student_ans) 
VALUES (result_for_each_question_seq.NEXTVAL, 1, 5, 2, 'Which operator is for exponent?', '+', '-', '**', '%', 'op3', 'op3');

--------------------------------------------------
-- Result for Quiz Table
--------------------------------------------------
INSERT INTO result_for_quiz (result_id, quiz_id, student_id, total_mark) VALUES (result_for_quiz_seq.NEXTVAL, 1, 1, 5);
INSERT INTO result_for_quiz (result_id, quiz_id, student_id, total_mark) VALUES (result_for_quiz_seq.NEXTVAL, 1, 2, 3);

commit;

SELECT 
    s.name AS student_name,
    r.quiz_id,
    r.total_mark,
    s.student_id,
    q.total_marks AS quiz_total_marks
FROM result_for_quiz r
JOIN student s ON r.student_id = s.student_id
JOIN quiz q ON r.quiz_id = q.quiz_id
WHERE r.quiz_id = 1
ORDER BY s.name;
