from flask import request, jsonify, Blueprint
from .models import db, Staff,  Student, Payment, Fee, BusPayment, BusDestination, Term, Gallery, Notification, Grade, BoardingFee, Class
from flask import current_app as app
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.jobs import process_term_rollover, promote_students

logging.basicConfig(level=logging.DEBUG)
routes = Blueprint('routes', __name__)

@routes.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        identifier = data.get('identifier')  # admission_number or name
        password = data.get('password')

        if not identifier or not password:
            return jsonify({"error": "Missing identifier or password"}), 400

        # Check if it's a student login
        student = Student.query.filter_by(admission_number=identifier).first()
        if student and student.check_password(password):
            return jsonify({"message": "Student login successful", "role": "student"}), 200

        # Check for staff login
        staff = Staff.query.filter_by(name=identifier).first()
        if staff and staff.check_password(password):
            return jsonify({"message": "Staff login successful", "role": staff.role}), 200

        # If no match is found
        return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        app.logger.error(f"Error during login: {e}")
        return jsonify({"error": "Internal server error"}), 500
    # return jsonify({"message": "Invalid credentials"}), 401
# Add/Register Student
@routes.route('/students', methods=['POST'])
def add_student():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["name", "admission_number", "grade_id", "phone", "is_boarding", "use_bus"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required."}), 400

        # Check if admission_number is unique
        existing_student = Student.query.filter_by(admission_number=data["admission_number"]).first()
        if existing_student:
            return jsonify({"error": "Admission number already exists."}), 400

        # Fetch grade and validate
        grade = Grade.query.get(data["grade_id"])
        if not grade:
            return jsonify({"error": "Grade not found."}), 400

        # Create a new student (without password, balance-related fields will be set later)
        student = Student(
            name=data["name"],
            admission_number=data["admission_number"],
            grade_id=data["grade_id"],
            phone=data["phone"],
            arrears=data ["arrears"],
            prepayment=data["prepayment"],
            is_boarding=data.get("is_boarding", False),
            use_bus=data.get("use_bus", False),
            bus_balance=data.get("bus_balance", 0.0),
            destination_id=data.get("destination_id")
        )
        student.set_password()
        if student.use_bus:
            destination_id = data.get("destination_id")
            if not destination_id:
                return jsonify({"error": "destination_id is required when use_bus is True."}), 400

            destination = BusDestination.query.get(destination_id)
            if not destination:
                return jsonify({"error": "Invalid bus destination ID."}), 400

            student.destination_id = destination.id
            student.bus_balance = destination.charge
        # Assign bus destination if 'use_bus' is True
            # Fetch and assign

        # Fetch the active term
        active_term = Term.get_active_term()
        if not active_term:
            return jsonify({"error": "No active term found."}), 400

        # Initialize balance based on the current active term's fee
        try:
            student.initialize_balance(term_id=active_term.id)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        # Commit student to the database
        db.session.add(student)
        db.session.commit()

        return jsonify({"message": "Student added successfully", "student": student.id}), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding student: {e}")
        return jsonify({"error": str(e)}), 500
        


@routes.route('/students', methods=['GET'])
def get_students():
    students = Student.query.all()
    # Serialize student data including necessary fields
    student_data = [
        {
            "id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "grade": student.grade.name if student.grade else "N/A",
            "balance": student.balance,
            "arrears":student.arrears,
            "bus_balance": student.bus_balance,
            "prepayment": student.prepayment,
            "last_payment_term_id":student.last_payment_term_id 
        }
        for student in students
    ]
    return jsonify(student_data)
    

# Update Student
@routes.route('/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    data = request.get_json()

    # Update fields
    if 'name' in data:
        student.name = data['name']
    if 'phone' in data:
        student.phone = data['phone']
    if 'use_bus' in data:
        student.use_bus = data['use_bus']
    if 'is_boarding' in data:
        student.is_boarding = data['is_boarding']

    # Reinitialize balance if necessary
    if 'is_boarding' in data or 'arrears' in data:
        student.arrears = data.get('arrears', student.arrears)
        student.initialize_balance()

    # Commit changes
    db.session.commit()
    return jsonify({"message": "Student updated successfully"}), 200


# Delete Student
@routes.route('/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted successfully"}), 200


# Update Balance After Payment

    
@routes.route('/register_staff', methods=['POST'])
def register_staff():
    data = request.get_json()
    name = data['name']
    phone = data['phone']
    role = data['role']
    password = data.get('password', 'defaultpassword')  # Set default password if not provided
    
    staff = Staff(
        name=name,
        phone=phone,
        role=role,
    )
    staff.set_password(password)  # Set password using bcrypt
    db.session.add(staff)
    db.session.commit()
    
    return jsonify({"message": "Staff registered successfully"}), 201

@routes.route('/staff', methods=['GET'])
def get_staff():
    staff_members = Staff.query.all()
    return jsonify([{
        'id': staff.id,
        'name': staff.name,
        'phone': staff.phone,
        'role': staff.role,
        'password':staff.password
    } for staff in staff_members])

@routes.route('/delete_staff/<int:id>', methods=['DELETE'])
def delete_staff(id):
    staff = Staff.query.get_or_404(id)
    db.session.delete(staff)
    db.session.commit()
    
    return jsonify({"message": "Staff deleted successfully"}), 200

@routes.route('/students/<int:id>', methods=['GET'])
def get_student(id):
    student = Student.query.get(id)
    if student:
        return jsonify({
            'id': student.id,
            'name': student.name,
            'grade': student.grade,
            'balance': student.balance,
            'bus_balance': student.bus_balance,
            'is_boarding': student.is_boarding
        })
    return jsonify({"error": "Student not found"}), 404


# Add Payment
@routes.route('/payments', methods=['POST'])
def add_payment():
    data = request.get_json()

    try:
        student_id = data.get('student_id')
        amount = data.get('amount')
        method = data.get('method')
        term_id = data.get('term_id')
        description = data.get('description')

        # Check if all required fields are provided
        if not all([student_id, amount, method, term_id]):
            return jsonify({"error": "Missing required fields"}), 400

        # Create and record the payment
        payment = Payment(
            student_id=student_id,
            amount=amount,
            method=method,
            term_id=term_id,
            description=description
        )

        # Commit the session to save the payment
        db.session.add(payment)
        db.session.commit()

        return jsonify({"message": "Payment added successfully!"}), 201

    except Exception as e:
        # Handle any exceptions that may arise during the process
        db.session.rollback()  # Rollback in case of an error
        return jsonify({"error": str(e)}), 500

# Fetch all payments
@routes.route('/payments', methods=['GET'])
def get_all_payments():
    try:
        payments = Payment.query.all()  # Fetch all payments from the database
        if not payments:
            return jsonify({'message': 'No payments found'}), 404
        return jsonify([payment.to_dict() for payment in payments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
# Edit Payment
@routes.route('/payments/<int:payment_id>', methods=['PUT'])
def edit_payment(payment_id):
    data = request.get_json()
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404

        payment.amount = data.get('amount', payment.amount)
        payment.method = data.get('method', payment.method)
        payment.term_id = data.get('term_id', payment.term_id)
        payment.description = data.get('description', payment.description)

        db.session.commit()
        return jsonify({"message": "Payment updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An error occurred while updating payment", "details": str(e)}), 500


# Delete Payment
@routes.route('/payments/<int:payment_id>', methods=['DELETE'])
def delete_payment(payment_id):
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404

        db.session.delete(payment)
        db.session.commit()
        return jsonify({"message": "Payment deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": "An error occurred while deleting payment", "details": str(e)}), 500

@routes.route('/payments/student/<int:student_id>', methods=['GET'])
def get_payments(student_id):
    payments = Payment.query.filter_by(student_id=student_id).all()
    return jsonify([payment.to_dict() for payment in payments])

# Get Payment by ID
@routes.route('/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    try:
        payment = Payment.query.get(payment_id)
        if not payment:
            return jsonify({"error": "Payment not found"}), 404

        return jsonify({
            "id": payment.id,
            "amount": payment.amount,
            "date": payment.date,
            "method": payment.method,
            "term_id": payment.term_id,
            "balance_after_payment": payment.balance_after_payment,
            "description": payment.description,
        }), 200

    except Exception as e:
        return jsonify({"error": "An error occurred while fetching payment", "details": str(e)}), 500

@routes.route('/destinations', methods=['GET'])
def get_destinations():
    try:
        # Fetch all bus destinations
        destinations = BusDestination.query.all()

        # Check if there are any destinations
        if not destinations:
            return jsonify({"message": "No bus destinations found."}), 404

        # Return the bus destinations as a list
        return jsonify([destination.to_dict() for destination in destinations]), 200

    except Exception as e:
        app.logger.error(f"Error fetching bus destinations: {e}")
        return jsonify({"error": str(e)}), 500

@routes.route('/students/<int:student_id>/assign_bus', methods=['POST'])
def assign_bus_to_student(student_id):
    student = Student.query.get_or_404(student_id)
    destination_id = request.json.get("destination_id")

    try:
        # Call the model method to assign destination, update balance, and set use_bus to True
        student.assign_bus_destination(destination_id)
        return jsonify({"message": "Bus destination, balance updated, and use_bus set to True."}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
        
@routes.route('/students/<int:student_id>/payments/term/<int:term_id>', methods=['GET'])
def get_student_payments_by_term(student_id, term_id):
    payments = Payment.query.filter_by(student_id=student_id).join(Fee).filter(Fee.term_id == term_id).all()
    return jsonify([
        {
            'id': payment.id,
            'amount': payment.amount,
            'date': payment.date,
            'method': payment.method
        }
        for payment in payments
    ])

@routes.route('/get_student_bus_destinations/<int:student_id>', methods=['GET'])
def get_student_bus_destinations(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    bus_destinations = student.bus_destinations  # Use the relationship to get bus destinations
    result = [{
        'bus_destination': destination.name,
        'charge': destination.charge
    } for destination in bus_destinations]

    return jsonify(result), 200

@routes.route('/term', methods=['POST'])
def create_term():
    data = request.get_json()
    if not all(key in data for key in ['name', 'start_date', 'end_date']):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format, use YYYY-MM-DD"}), 400

    if start_date >= end_date:
        return jsonify({"error": "Start date must be before end date"}), 400

    term = Term(name=data['name'], start_date=start_date, end_date=end_date)
    db.session.add(term)
    db.session.commit()

    return jsonify({"message": "Term created successfully", "term": term.to_dict()})


@routes.route('/terms', methods=['GET'])
def get_terms():
    terms = Term.query.all()
    active_term = Term.get_active_term()
    return jsonify([{
        'id': term.id,
        'name': term.name,
        'start_date': term.start_date,
        'end_date': term.end_date,
        'is_active': term.id == active_term.id if active_term else False
    } for term in terms])

@routes.route('/bus-payments', methods=['POST'])
def create_bus_payment():
    data = request.get_json()
    student_id = data['student_id']
    amount = data['amount']
    term_id = data['term_id']
    destination_id = data.get('destination_id', None)

    bus_payment = BusPayment(
        student_id=student_id,
        term_id=term_id,
        amount=amount,
        destination_id=destination_id
    )
    db.session.add(bus_payment)
    db.session.commit()

    # Update the student's bus balance
    bus_payment.update_student_bus_balance()

    return jsonify({
        'message': 'Bus payment created successfully',
        'bus_payment': {
            'student_id': student_id,
            'amount': amount,
            'payment_date': bus_payment.payment_date
        }
    })

@routes.route('/assign-student-to-bus', methods=['POST'])
def assign_student_to_bus():
    data = request.get_json()

    # Extract student ID and destination ID from the request
    student_id = data.get('student_id')
    destination_id = data.get('destination_id')

    # Validate student and destination existence
    student = Student.query.get(student_id)
    destination = BusDestination.query.get(destination_id)

    if not student:
        return jsonify({"error": "Student not found"}), 404

    if not destination:
        return jsonify({"error": "Bus destination not found"}), 404

    # Assign the bus destination to the student
    student.bus_destination_id = destination.id
    db.session.commit()

    return jsonify({
        "message": f"Student '{student.name}' assigned to destination '{destination.name}' successfully.",
        "student_id": student.id,
        "destination_id": destination.id
    })

@routes.route('/students-with-destinations', methods=['GET'])
def get_students_with_destinations():
    # Query all students
    students = Student.query.all()

    # Prepare a list of students with their destinations
    result = []
    for student in students:
        result.append({
            "student_id": student.id,
            "name": student.name,
            "admission_number": student.admission_number,
            "grade": student.grade.name if student.grade else None,
            "destination": {
                "id": student.bus_destination.id if student.bus_destination else None,
                "name": student.bus_destination.name if student.bus_destination else "No destination assigned",
                "charge": student.bus_destination.charge if student.bus_destination else None
            }
        })

    return jsonify(result)

@routes.route('/students-in-destination/<int:destination_id>', methods=['GET'])
def get_students_in_destination(destination_id):
    destination = BusDestination.query.get(destination_id)

    if not destination:
        return jsonify({"error": "Bus Destination not found"}), 404

    students = [
        {
            'id': student.id,
            'name': student.name,
            'admission_number': student.admission_number
        }
        for student in destination.students
    ]

    return jsonify({
        'destination': {
            'id': destination.id,
            'name': destination.name,
            'charge': destination.charge
        },
        'students': students
    })

@routes.route('/gallery', methods=['POST'])
def add_gallery_item():
    data = request.get_json()
    image_url = data['image_url']
    description = data.get('description', None)

    gallery_item = Gallery(image_url=image_url, description=description)
    db.session.add(gallery_item)
    db.session.commit()

    return jsonify({
        'message': 'Gallery item added successfully',
        'gallery_item': {
            'image_url': image_url,
            'description': description
        }
    })

@routes.route('/notifications', methods=['GET'])
def get_notifications():
    notifications = Notification.query.all()
    return jsonify([{
        'id': notification.id,
        'message': notification.message,
        'date': notification.date
    } for notification in notifications])

@routes.route('/notifications', methods=['POST'])
def add_notification():
    data = request.get_json()
    message = data['message']

    notification = Notification(message=message)
    db.session.add(notification)
    db.session.commit()

    return jsonify({
        'message': 'Notification added successfully',
        'notification': {
            'message': message,
            'date': notification.date
        }
    })

@routes.route('/process-rollover', methods=['POST'])
def process_rollover():
    success = process_term_rollover()  # Call the rollover function
    if success:
        return jsonify({"message": "Term rollover processed successfully"}), 200
    else:
        return jsonify({"message": "No term found to process rollover"}), 400

@routes.route('/promote-students', methods=['POST'])

def promote_students_route():
    promote_students()  # Call the function for student promotion
    return jsonify({"message": "students rollover was successfulll. congratulations 🎉"}),200

# Route to add a grade
@routes.route('/grades', methods=['POST'])
def add_grade():
    try:
        data = request.get_json()
        name = data.get('name')

        if not name:
            return jsonify({"error": "Grade name is required."}), 400

        # Check if the grade already exists
        existing_grade = Grade.query.filter_by(name=name).first()
        if existing_grade:
            return jsonify({"error": "Grade already exists."}), 400

        # Add new grade
        grade = Grade(name=name)
        db.session.add(grade)
        db.session.commit()

        return jsonify({"message": f"Grade '{name}' added successfully."}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# Route to get all grades
@routes.route('/grades', methods=['GET'])
def get_grades():
    try:
        grades = Grade.query.all()
        grades_data = [{"id": grade.id, "grade": grade.name} for grade in grades]
        return jsonify(grades_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@routes.route('/fees/<int:term_id>/<int:grade_id>', methods=['GET'])
def get_fees_for_grade_in_term(term_id, grade_id):
    try:
        # Query the Fee for the specific term and grade
        fees = Fee.query.filter_by(term_id=term_id, grade_id=grade_id).all()

        if not fees:
            return jsonify({'message': f'No fees found for term {term_id} and grade {grade_id}'}), 404

        # Return the fee data
        return jsonify({'fees': [fee.to_dict() for fee in fees]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@routes.route('/fee-structure/<int:term_id>', methods=['GET'])
def generate_fee_structure_for_term(term_id):
    try:
        # Query all grades for the specific term and their associated fees
        fee_structure = db.session.query(Grade.name, db.func.sum(Fee.amount).label('total_fee')) \
            .join(Fee, Grade.id == Fee.grade_id) \
            .filter(Fee.term_id == term_id) \
            .group_by(Grade.name) \
            .all()

        if not fee_structure:
            return jsonify({'message': f'No fee structure found for term {term_id}'}), 404

        # Return the fee structure
        return jsonify({'fee_structure': [{'grade_name': grade_name, 'total_fee': total_fee} for grade_name, total_fee in fee_structure]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to fetch all fees or fees for a specific term and grade
@routes.route('/fees', methods=['GET'])
def get_fees():
    term_id = request.args.get('term_id', type=int)
    grade_id = request.args.get('grade_id', type=int)

    try:
        query = Fee.query

        if term_id:
            query = query.filter_by(term_id=term_id)

        if grade_id:
            query = query.filter_by(grade_id=grade_id)

        fees = query.all()
        return jsonify([fee.to_dict() for fee in fees]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to fetch fee structure for a specific year
@routes.route('/fee-structure/<int:year>', methods=['GET'])
def get_fee_structure(year):
    try:
        terms = Term.query.filter(Term.start_date.between(f"{year}-01-01", f"{year}-12-31")).all()

        if not terms:
            return jsonify({"message": "No terms found for the specified year."}), 404

        fee_structure = {}
        for term in terms:
            fees = Fee.query.filter_by(term_id=term.id).all()
            fee_structure[term.name] = [fee.to_dict() for fee in fees]

        return jsonify(fee_structure), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to add a new fee
@routes.route('/fees', methods=['POST'])
def add_fee():
    try:
        data = request.get_json()
        term_id = data.get('term_id')
        grade_id = data.get('grade_id')
        amount = data.get('amount')

        if not all([term_id, grade_id, amount]):
            return jsonify({"message": "term_id, grade_id, and amount are required."}), 400

        # Check if the fee already exists
        existing_fee = Fee.query.filter_by(term_id=term_id, grade_id=grade_id).first()
        if existing_fee:
            return jsonify({"message": "Fee for this term and grade already exists."}), 409

        new_fee = Fee(term_id=term_id, grade_id=grade_id, amount=amount)
        db.session.add(new_fee)
        db.session.commit()

        return jsonify(new_fee.to_dict()), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to update an existing fee
@routes.route('/fees/<int:fee_id>', methods=['PUT'])
def update_fee(fee_id):
    try:
        data = request.get_json()
        amount = data.get('amount')

        if not amount:
            return jsonify({"message": "Amount is required."}), 400

        fee = Fee.query.get(fee_id)

        if not fee:
            return jsonify({"message": "Fee not found."}), 404

        fee.amount = amount
        db.session.commit()

        return jsonify(fee.to_dict()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Route to delete a fee
@routes.route('/fees/<int:fee_id>', methods=['DELETE'])
def delete_fee(fee_id):
    try:
        fee = Fee.query.get(fee_id)

        if not fee:
            return jsonify({"message": "Fee not found."}), 404

        db.session.delete(fee)
        db.session.commit()

        return jsonify({"message": "Fee deleted successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route('/boarding_fee', methods=['GET'])
def get_boarding_fee():
    boarding_fee = BoardingFee.query.first()

    if boarding_fee:
        return jsonify({
            "id": boarding_fee.id,
            "extra_fee": boarding_fee.extra_fee
        })
    else:
        return jsonify({"error": "Boarding fee not found"}), 404

@routes.route('/boarding_fee', methods=['PUT'])
def update_boarding_fee():
    try:
        data = request.get_json()

        boarding_fee = BoardingFee.query.first()

        if not boarding_fee:
            return jsonify({"error": "Boarding fee not found"}), 404

        # Update extra_fee if provided
        if "extra_fee" in data:
            boarding_fee.extra_fee = data["extra_fee"]

        db.session.commit()

        return jsonify({"message": "Boarding fee updated successfully", "extra_fee": boarding_fee.extra_fee}), 200
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error updating boarding fee: {e}")
        return jsonify({"error": str(e)}), 500

@routes.route('/bus_payments', methods=['POST'])
def add_bus_payment():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["student_id", "amount"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"{field} is required."}), 400

        student_id = data["student_id"]
        amount = data["amount"]

        # Validate student existence
        student = Student.query.get(student_id)
        if not student:
            return jsonify({"error": "Student not found."}), 404

        # Check if the student uses the bus
        if not student.use_bus or not student.destination_id:
            return jsonify({"error": "Student does not use the bus or has no assigned destination."}), 400

        # Fetch the current active term
        current_term = Term.get_active_term()
        if not current_term:
            return jsonify({"error": "No active term found."}), 400

        # Create the bus payment
        bus_payment = BusPayment(
            student_id=student_id,
            term_id=current_term.id,
            destination_id=student.destination_id,
            amount=amount
        )
        db.session.add(bus_payment)

        # Update the student's bus balance
        if student.bus_balance >= amount:
            student.bus_balance -= amount
        else:
            return jsonify({"error": "Payment amount exceeds the student's current bus balance."}), 400

        db.session.commit()

        return jsonify({
            "message": "Bus payment added successfully.",
            "bus_payment": bus_payment.to_dict(),
            "updated_bus_balance": student.bus_balance
        }), 201

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error adding bus payment: {e}")
        return jsonify({"error": str(e)}), 500

@routes.route('/terms/active', methods=['GET'])
def get_active_term():
    # Determine the active term based on the current date
    active_term = Term.query.filter(Term.start_date <= datetime.utcnow().date(), Term.end_date >= datetime.utcnow().date()).first()

    if not active_term:
        return jsonify({"error": "No active term found"}), 404

    return jsonify(active_term.to_dict())

@routes.route('/assign-class', methods=['POST'])
def assign_class():
    data = request.json
    staff_id = data.get('staff_id')
    class_id = data.get('class_id')

    if not staff_id or not class_id:
        return jsonify({"error": "Staff ID and Class ID are required"}), 400

    # Fetch class and staff safely
    cls = Class.query.filter_by(id=class_id).first()
    staff = Staff.query.filter_by(id=staff_id).first()

    if not cls:
        return jsonify({"error": "Class not found"}), 404
    if not staff:
        return jsonify({"error": "Staff not found"}), 404

    try:
        cls.staff_id = staff.id  # Assign staff to the class
        db.session.commit()
        return jsonify({"message": "Staff assigned to class successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@routes.route('/classes', methods=['GET'])
def get_classes():
    try:
        classes = Class.query.all()
        return jsonify([cls.to_dict() for cls in classes]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@routes.route('/delete-class/<int:class_id>', methods=['DELETE'])
def delete_class(class_id):
    cls = Class.query.filter_by(id=class_id).first()

    if not cls:
        return jsonify({"error": "Class not found"}), 404

    try:
        db.session.delete(cls)
        db.session.commit()
        return jsonify({"message": "Class deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@routes.route('/api/stats', methods=['GET'])
def get_stats():
    from sqlalchemy import func

    # Total fee expected (school-wide)
    total_expected_fee = db.session.query(func.sum(Fee.amount)).scalar() or 0

    # Total fee collected (school-wide)
    total_fee_paid = db.session.query(func.sum(Payment.amount)).scalar() or 0

    # Expenses (Example: Expenses table in your database)
    total_expenses = db.session.query(func.sum(Expense.amount)).scalar() or 0

    # Revenue
    current_revenue = total_fee_paid - total_expenses

    # Per-class stats
    class_stats = []
    classes = Class.query.all()
    for c in classes:
        total_class_fee = db.session.query(func.sum(Fee.amount)).filter(Fee.class_id == c.id).scalar() or 0
        total_class_paid = db.session.query(func.sum(Payment.amount)).filter(Payment.class_id == c.id).scalar() or 0
        class_stats.append({
            "class_name": c.name,
            "total_expected_fee": total_class_fee,
            "total_fee_paid": total_class_paid,
            "percentage_paid": round((total_class_paid / total_class_fee) * 100, 2) if total_class_fee > 0 else 0
        })

    stats = {
        "total_expected_fee": total_expected_fee,
        "total_fee_paid": total_fee_paid,
        "percentage_paid": round((total_fee_paid / total_expected_fee) * 100, 2) if total_expected_fee > 0 else 0,
        "total_expenses": total_expenses,
        "current_revenue": current_revenue,
        "class_stats": class_stats
    }

    return jsonify(stats)

@routes.route('/api/prediction', methods=['POST'])
def predict_days():
    data = request.get_json()
    daily_expenses = data.get("daily_expenses", 0)  # Average daily expenses
    in_kind_payments = data.get("in_kind_payments", 0)  # Value of in-kind payments

    # Total revenue (fees collected + in-kind payments)
    total_revenue = db.session.query(db.func.sum(Payment.amount)).scalar() or 0
    total_revenue += in_kind_payments

    # Calculate operational days
    operational_days = 0
    if daily_expenses > 0:
        operational_days = total_revenue / daily_expenses

    # Return prediction result
    return jsonify({
        "total_revenue": total_revenue,
        "daily_expenses": daily_expenses,
        "operational_days": round(operational_days, 2)
    })
    