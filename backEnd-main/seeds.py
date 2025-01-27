from app import create_app, db
from app.models import Student, Grade, Fee, BoardingFee, BusDestination, Term
import pandas as pd
from datetime import datetime

FILE_PATH = "test.xlsx"

def seed_students_from_excel(file_path):
    try:
        # Load the Excel file
        df = pd.read_excel(file_path)

        # Get the current term ID from the Term model
        current_term = Term.get_active_term()  # Fetch the current active term
        if not current_term:
            print("Current term not found. Exiting script.")
            return
        term_id = current_term.id

        # Iterate through each row in the Excel file
        for index, row in df.iterrows():
            print(f"Processing row {index}: {row}")  # Debugging print

            # Validate mandatory fields
            if not row.get("name") or pd.isna(row["name"]):
                print(f"Skipping row {index}: Missing or invalid name")
                continue
            if not row.get("admission_number") or pd.isna(row["admission_number"]):
                print(f"Skipping row {index}: Missing or invalid admission_number")
                continue
            if not row.get("grade") or pd.isna(row["grade"]):
                print(f"Skipping row {index}: Missing or invalid grade")
                continue

            # Get values from the row
            name = row["name"]
            admission_number = row["admission_number"]
            phone = row["phone"]
            grade_name = row["grade"]
            arrears = row.get("arrears", 0)  # Default to 0 if missing
            prepayment = row.get("prepayment", 0)  # Default to 0 if missing
            is_boarding = row.get("is_boarding", False)  # Default to False if missing
            use_bus = row.get("use_bus", False)  # Default to False if missing
            destination_id = row.get("destination_id", None)  # Default to None if missing

            # Convert is_boarding and use_bus to booleans if necessary
            is_boarding = str(is_boarding).strip().lower() in ["true", "1", "yes"]
            use_bus = str(use_bus).strip().lower() in ["true", "1", "yes"]

            # Get grade_id from the database
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                print(f"Grade '{grade_name}' not found in the database. Skipping row {index}...")
                continue

            # Get the fee for the grade based on current term
            fee = Fee.query.filter_by(grade_id=grade.id, term_id=term_id).first()
            if not fee:
                print(f"Fee for grade '{grade_name}' not found for the current term. Skipping row {index}...")
                continue

            # Check if the student already exists
            student = Student.query.filter_by(admission_number=admission_number).first()
            if not student:
                # Add a new student
                student = Student(
                    name=name,
                    admission_number=admission_number,
                    phone=phone,
                    grade_id=grade.id,
                    arrears=arrears,
                    prepayment=prepayment,
                    is_boarding=is_boarding,
                    use_bus=use_bus,
                    destination_id=None,  # Initialize with None; will be set later
                )
                student.set_password(str(admission_number))  # Set password

                # Assign bus destination if applicable
                if use_bus and destination_id:
                    destination = BusDestination.query.get(destination_id)
                    if destination:
                        try:
                            student.assign_bus_destination(destination_id)
                        except ValueError as e:
                            print(f"Error assigning bus destination for student {name}: {e}")
                            continue
                    else:
                        print(f"Destination ID {destination_id} not found for {name}. Skipping bus assignment.")

                # Initialize balance for the student
                student.initialize_balance(term_id)  # Includes fees and optional boarding fee

                # Add the student to the session
                db.session.add(student)
            else:
                # Update the existing student's details
                student.grade_id = grade.id
                student.arrears = arrears
                student.prepayment = prepayment
                student.is_boarding = is_boarding
                student.use_bus = use_bus

                # Assign or update the bus destination if applicable
                if use_bus and destination_id:
                    destination = BusDestination.query.get(destination_id)
                    if destination:
                        try:
                            student.assign_bus_destination(destination_id)
                        except ValueError as e:
                            print(f"Error assigning bus destination for student {name}: {e}")
                            continue
                    else:
                        print(f"Destination ID {destination_id} not found for {name}. Skipping bus assignment.")

                # Recalculate the balance if any fields have changed
                student.initialize_balance(term_id)

        # Commit the transaction
        db.session.commit()
        print("Students added or updated successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()

# Add methods to Student class

def initialize_balance(self, term_id):
    """Calculate initial balance for the term."""
    active_term = Term.get_active_term()
    if not active_term:
        self.balance = 0.0
        return
    fee = Fee.query.filter_by(grade_id=self.grade_id, term_id=active_term.id).first()
    if not fee:
        raise ValueError("Fee structure not set for this grade and term.")

    self.balance = fee.amount if fee.amount is not None else 0.0
    if self.is_boarding:
        boarding_fee = BoardingFee.query.first()
        if boarding_fee:
            self.balance += boarding_fee.extra_fee if boarding_fee.extra_fee is not None else 0.0

    self.balance -= self.prepayment if self.prepayment is not None else 0.0
    self.prepayment = 0.0
    db.session.commit()

def update_payment(self, amount, term_id):
    """Update student balance, prepayment, and arrears for the current active term."""
    active_term = Term.get_active_term()
    if not active_term:
        raise ValueError("No active term found.")
    if self.arrears is None:
        self.arrears = 0.0
    # Handle arrears first
    if self.arrears > 0:
        if amount >= self.arrears:
            amount -= self.arrears
            self.arrears = 0
        else:
            self.arrears -= amount

        db.session.commit()
        return  # Payment fully applied to arrears

    # Apply remaining amount to the current balance
    self.balance -= amount
    if self.balance < 0:
        self.prepayment = -self.balance  # Convert negative balance to prepayment
        self.balance = 0

    if self.prepayment > 0:
        next_term = Term.query.filter(
            Term.start_date > datetime.utcnow()
        ).order_by(Term.start_date).first()

        if next_term:
            self.prepayment_term_id = next_term.id
        else:
            # If no next term, the prepayment stays as a balance
            self.prepayment_term_id = None

    db.session.commit()

# Run the script
if __name__ == "__main__":
    app = create_app()  # Create your Flask app
    with app.app_context():  # Push the application context
        seed_students_from_excel(FILE_PATH)

        