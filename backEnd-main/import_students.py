import pandas as pd
from app import db  # Importing your Flask db instance from the app folder
from app.models import Student, Term, Fee, Payment  # Import the models

def import_students():
    # Load data from the Excel file
    data = pd.read_excel("students_data.xlsx")

    # Example: Assuming 'students_data.xlsx' has the following columns:
    # - 'name', 'admission_number', 'grade_id', 'phone', 'arrears', 'prepayment', 'is_boarding', 'use_bus'

    for index, row in data.iterrows():
        # Get or create grade and term details
        grade = row['grade_id']  # Assuming you have a way to get the grade instance
        term = Term.query.filter_by(is_active=True).first()  # Use the active term (you need to handle how to get the term)

        # Initialize balance based on the grade and add arrears or prepayment
        balance = calculate_balance(grade, row['arrears'], row['prepayment'])

        # Create a new student record
        student = Student(
            name=row['name'],
            admission_number=row['admission_number'],
            grade_id=grade,
            phone=row['phone'],
            balance=balance,
            term_id=term.id,  # Link the student to the active term
            is_boarding=row['is_boarding'],
            use_bus=row['use_bus']
        )

        # Add the student to the database
        db.session.add(student)
        db.session.commit()

    print("Students imported successfully.")

def calculate_balance(grade, arrears, prepayment):
    # Implement your fee calculation logic based on the grade, arrears, and prepayment
    base_fee = grade.fee  # Assume `fee` is a column in your Grade model
    balance = base_fee + arrears - prepayment
    return balance

if __name__ == '__main__':
    import_students()
    