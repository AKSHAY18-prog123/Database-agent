import mysql.connector

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '24bca7190'
}

DB_NAME = 'school_management'

def seed_database():
    print(f"Connecting to MySQL at {MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}...")
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    # Create database if not exists
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cursor.execute(f"USE {DB_NAME};")
    print(f"Database '{DB_NAME}' created/selected.")

    # Drop existing tables to ensure clean slate
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    tables = ['grades', 'enrollments', 'courses', 'students', 'teachers', 'departments']
    for t in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {t};")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # 1. Departments Table
    cursor.execute("""
    CREATE TABLE departments (
        department_id INT AUTO_INCREMENT PRIMARY KEY,
        department_name VARCHAR(100) NOT NULL UNIQUE,
        building VARCHAR(100) NOT NULL,
        budget DECIMAL(12, 2) NOT NULL,
        head_of_department VARCHAR(100)
    );
    """)

    # 2. Teachers Table
    cursor.execute("""
    CREATE TABLE teachers (
        teacher_id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        hire_date DATE NOT NULL,
        salary DECIMAL(10, 2) NOT NULL,
        department_id INT,
        FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
    );
    """)

    # 3. Students Table
    cursor.execute("""
    CREATE TABLE students (
        student_id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        date_of_birth DATE NOT NULL,
        gender VARCHAR(10),
        gpa DECIMAL(3, 2) DEFAULT 0.00,
        department_id INT,
        enrollment_year INT NOT NULL,
        FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL
    );
    """)

    # 4. Courses Table
    cursor.execute("""
    CREATE TABLE courses (
        course_id INT AUTO_INCREMENT PRIMARY KEY,
        course_code VARCHAR(20) UNIQUE NOT NULL,
        course_name VARCHAR(100) NOT NULL,
        credits INT NOT NULL DEFAULT 3,
        department_id INT,
        teacher_id INT,
        FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL,
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL
    );
    """)

    # 5. Enrollments Table
    cursor.execute("""
    CREATE TABLE enrollments (
        enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
        student_id INT NOT NULL,
        course_id INT NOT NULL,
        semester VARCHAR(20) NOT NULL,
        enrollment_date DATE NOT NULL,
        FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
        UNIQUE KEY unique_enrollment (student_id, course_id, semester)
    );
    """)

    # 6. Grades Table
    cursor.execute("""
    CREATE TABLE grades (
        grade_id INT AUTO_INCREMENT PRIMARY KEY,
        enrollment_id INT NOT NULL UNIQUE,
        grade_letter VARCHAR(2) NOT NULL,
        score DECIMAL(5, 2) NOT NULL,
        remarks VARCHAR(255),
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id) ON DELETE CASCADE
    );
    """)

    print("Tables created successfully.")

    # --- SEED DATA ---
    # Departments (5)
    departments_data = [
        ('Computer Science', 'Turing Hall', 450000.00, 'Dr. Alan Turing'),
        ('Mathematics', 'Euler Block', 320000.00, 'Dr. Katherine Johnson'),
        ('Physics', 'Newton Tower', 380000.00, 'Dr. Richard Feynman'),
        ('Chemistry', 'Curie Lab', 290000.00, 'Dr. Marie Curie'),
        ('Literature & Humanities', 'Shakespeare Annex', 210000.00, 'Dr. Maya Angelou')
    ]
    cursor.executemany("""
        INSERT INTO departments (department_name, building, budget, head_of_department)
        VALUES (%s, %s, %s, %s);
    """, departments_data)

    # Teachers (7)
    teachers_data = [
        ('Aarav', 'Sharma', 'aarav.sharma@school.edu', '2018-08-15', 85000.00, 1),
        ('Priya', 'Patel', 'priya.patel@school.edu', '2019-01-10', 82000.00, 1),
        ('Vikram', 'Rao', 'vikram.rao@school.edu', '2015-06-01', 94000.00, 2),
        ('Ananya', 'Deshmukh', 'ananya.d@school.edu', '2020-09-01', 78000.00, 2),
        ('Rajesh', 'Kumar', 'rajesh.kumar@school.edu', '2016-11-20', 91000.00, 3),
        ('Sunita', 'Verma', 'sunita.verma@school.edu', '2017-03-15', 88000.00, 4),
        ('David', 'Miller', 'david.miller@school.edu', '2021-02-01', 75000.00, 5)
    ]
    cursor.executemany("""
        INSERT INTO teachers (first_name, last_name, email, hire_date, salary, department_id)
        VALUES (%s, %s, %s, %s, %s, %s);
    """, teachers_data)

    # Students (12)
    students_data = [
        ('Rahul', 'Gupta', 'rahul.g@student.edu', '2003-05-14', 'Male', 3.85, 1, 2022),
        ('Neha', 'Singh', 'neha.s@student.edu', '2004-02-22', 'Female', 3.92, 1, 2023),
        ('Rohan', 'Mehta', 'rohan.m@student.edu', '2002-11-08', 'Male', 3.45, 1, 2021),
        ('Sneha', 'Joshi', 'sneha.j@student.edu', '2003-09-30', 'Female', 3.78, 2, 2022),
        ('Amit', 'Verma', 'amit.v@student.edu', '2004-07-19', 'Male', 3.12, 2, 2023),
        ('Kavya', 'Reddy', 'kavya.r@student.edu', '2003-12-05', 'Female', 3.96, 3, 2022),
        ('Arjun', 'Nair', 'arjun.n@student.edu', '2002-04-17', 'Male', 3.60, 3, 2021),
        ('Pooja', 'Iyer', 'pooja.i@student.edu', '2004-01-11', 'Female', 3.88, 4, 2023),
        ('Dev', 'Kapoor', 'dev.k@student.edu', '2003-08-25', 'Male', 3.30, 4, 2022),
        ('Simran', 'Kaur', 'simran.k@student.edu', '2004-06-03', 'Female', 3.75, 5, 2023),
        ('Aditya', 'Chawla', 'aditya.c@student.edu', '2002-10-14', 'Male', 3.55, 5, 2021),
        ('Ishaan', 'Bhat', 'ishaan.b@student.edu', '2003-03-29', 'Male', 3.81, 1, 2022)
    ]
    cursor.executemany("""
        INSERT INTO students (first_name, last_name, email, date_of_birth, gender, gpa, department_id, enrollment_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """, students_data)

    # Courses (8)
    courses_data = [
        ('CS101', 'Introduction to Data Structures & Algorithms', 4, 1, 1),
        ('CS202', 'Database Management Systems & SQL', 4, 1, 2),
        ('CS303', 'Artificial Intelligence & Machine Learning', 4, 1, 1),
        ('MATH101', 'Linear Algebra & Calculus', 3, 2, 3),
        ('MATH202', 'Probability & Statistics', 3, 2, 4),
        ('PHYS101', 'Quantum Physics Fundamentals', 4, 3, 5),
        ('CHEM101', 'Organic & Inorganic Chemistry', 4, 4, 6),
        ('LIT101', 'World Literature & Critical Writing', 3, 5, 7)
    ]
    cursor.executemany("""
        INSERT INTO courses (course_code, course_name, credits, department_id, teacher_id)
        VALUES (%s, %s, %s, %s, %s);
    """, courses_data)

    # Enrollments (12)
    enrollments_data = [
        (1, 1, 'Fall 2023', '2023-08-20'),
        (1, 2, 'Fall 2023', '2023-08-20'),
        (2, 1, 'Fall 2023', '2023-08-21'),
        (2, 3, 'Spring 2024', '2024-01-15'),
        (3, 2, 'Fall 2023', '2023-08-22'),
        (4, 4, 'Fall 2023', '2023-08-20'),
        (5, 5, 'Fall 2023', '2023-08-21'),
        (6, 6, 'Fall 2023', '2023-08-20'),
        (7, 6, 'Spring 2024', '2024-01-16'),
        (8, 7, 'Fall 2023', '2023-08-22'),
        (9, 7, 'Spring 2024', '2024-01-15'),
        (10, 8, 'Fall 2023', '2023-08-20')
    ]
    cursor.executemany("""
        INSERT INTO enrollments (student_id, course_id, semester, enrollment_date)
        VALUES (%s, %s, %s, %s);
    """, enrollments_data)

    # Grades (12)
    grades_data = [
        (1, 'A', 92.50, 'Excellent performance'),
        (2, 'A', 95.00, 'Top scorer in SQL'),
        (3, 'A+', 98.00, 'Outstanding project work'),
        (4, 'A', 94.00, 'Great grasp of AI concepts'),
        (5, 'B+', 87.50, 'Good effort'),
        (6, 'A', 91.00, 'Strong math skills'),
        (7, 'B', 83.00, 'Consistent work'),
        (8, 'A+', 99.00, 'Highest marks in Physics'),
        (9, 'B+', 88.00, 'Solid understanding'),
        (10, 'A', 96.00, 'Flawless lab work'),
        (11, 'B', 84.50, 'Good progress'),
        (12, 'A', 93.00, 'Insightful essays')
    ]
    cursor.executemany("""
        INSERT INTO grades (enrollment_id, grade_letter, score, remarks)
        VALUES (%s, %s, %s, %s);
    """, grades_data)

    conn.commit()
    print("Successfully seeded 35+ records into school_management database!")

    # Display inserted counts
    tables_to_check = ['departments', 'teachers', 'students', 'courses', 'enrollments', 'grades']
    for t in tables_to_check:
        cursor.execute(f"SELECT COUNT(*) FROM {t};")
        count = cursor.fetchone()[0]
        print(f" -> Table '{t}': {count} rows")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    seed_database()
