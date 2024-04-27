import math
import os
import pickle
import threading
import time
import pandas as pd
from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_cors import cross_origin
import holidays

app = Flask(__name__)

sql_username = os.getenv('SQL_USERNAME')
sql_password = os.getenv('SQL_PASSWORD')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://{sql_username}:{sql_password}@amusementpark-amusementpark.h.aivencloud.com:15025/amusementpark'

ma = Marshmallow(app)
db = SQLAlchemy(app)

NOT_FOUND = 404
INTERNAL_SERVER_ERROR = 500

day_mapping = {
    "Sunday": 0,
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6
}

ride_capacity = {
    "FantyWheel": 40,
    "GoKarting": 10,
    "ToyTrain": 20,
    "GhostHouse": 10,
    "BumpingCars": 10,
    "SnowWorld": 50,
    "RollerCoaster": 20,
    "Tower": 25,
    "FantasyCups": 20,
    "Carousel": 20,
    "Scrambler": 20,
    "JokerShow": 60,
    "FantasyShip": 30,
    "RabbitStatue": 50
}

queue = {
    "FantyWheel": [],
    "GoKarting": [],
    "ToyTrain": [],
    "GhostHouse": [],
    "BumpingCars": [],
    "SnowWorld": [],
    "RollerCoaster": [],
    "Tower": [],
    "FantasyCups": [],
    "Carousel": [],
    "Scrambler": [],
    "JokerShow": [],
    "FantasyShip": [],
    "RabbitStatue": []
}

lock = threading.Lock()

def get_holiday_details(date):
    # Check if the date is a holiday
    us_holidays = holidays.US()
    if date in us_holidays:
        return 1  # Return 1 to indicate it's a holiday
    else:
        return 0  # Return 0 to indicate it's not a holiday


def reduce_queue():
    global queue, lock
    while True:
        time.sleep(300)  # 300 seconds = 5 minutes
        with lock:
            for ride, q in queue.items():
                for i in range(ride_capacity[ride]):
                    if q:
                        q.pop(0)
                    else:
                        break

reduce_thread = threading.Thread(target=reduce_queue)
reduce_thread.daemon = True
reduce_thread.start()

def predict_wait_time(input_data):
    data = pd.DataFrame(input_data, columns=['Date', 'Time', 'Ride', 'Capacity', 'Crowd Count'])
    day = data['Date'].apply(lambda x: day_mapping[pd.to_datetime(x).strftime("%A")])
    # Convert the second column to datetime
    data_datetime = pd.to_datetime(data['Time'])

    # Extract hour and minute separately
    time_minutes = data_datetime.dt.hour * 60 + data_datetime.dt.minute
    # time_minutes = pd.to_datetime(data.iloc[:,1]).hour * 60 + pd.to_datetime(data.iloc[:,1]).minute

    holiday = []
    for d in day:
        if d == 0 or d == 6:
            holiday.append(1)
        else:
            holiday.append(get_holiday_details(d))

    loaded_model = pickle.load(open('WaitTimeModel.model', 'rb'))
    # Assuming you have your input data stored in a DataFrame or array
    final_data = pd.DataFrame({
        'Day': day,
        'Holiday': holiday,
        'Capacity': data['Capacity'],
        'Crowd Count': data['Crowd Count'],
        'Time_minutes': time_minutes
    })

    # Provide feature names
    final_data.columns = ['Day', 'Holiday', 'Capacity', 'Crowd Count', 'Time_minutes']

    # Now, you can use this input data for prediction
    result = loaded_model.predict(final_data)
    return result


@app.route('/')
def render_index():
    return render_template('index.html')


@app.route('/rides')
def render_rides():
    return render_template('rides.html')


@app.route('/signup')
def render_signup():
    return render_template('signup.html')


@app.route('/map')
def render_map():
    return render_template('map.html')


@app.route('/login')
def render_login():
    return render_template('login.html')


@app.route('/buy')
def render_buy():
    return render_template('buytickets.html')


@app.route('/feedback')
def render_feedback():
    return render_template('feedbackform.html')


@app.route('/customerservices')
def render_services():
    return render_template('customerservices.html')


@app.route('/contactus')
def render_contactus():
    return render_template('contactus.html')


@app.route('/recommendation')
def render_recommendation():
    return render_template('recommendation.html')


@app.route('/virtualq')
def render_virtualq():
    return render_template('virtualq.html')


@app.route('/mytrips')
def render_mytrips():
    return render_template('mytrips.html')

@app.route('/prediction')
def render_prediction():
    return render_template('prediction.html')

@app.route('/parkmap')
def render_parkmap():
    return render_template('map.html')

@app.route('/admin')
def render_admin():
    return render_template('admin.html')

@app.route('/validate')
def render_validate():
    return render_template('validateticket.html')

@app.route('/viewfeedback')
def render_viewfeedbackform():
    return render_template('viewfeedbackforms.html')

@app.route('/maintenance')
def render_maintenance():
    return render_template('maintenancerequest.html')

@app.route('/viewmaintenance')
def render_viewmaintenace():
    return render_template('viewmaintenance.html')


class Users(db.Model):
    emailid = db.Column(db.String(255), primary_key=True)
    password = db.Column(db.String(255))
    FirstName = db.Column(db.String(255))
    LastName = db.Column(db.String(255))
    DateOfBirth = db.Column(db.Date)

    def __init__(self, emailid, password, FirstName, LastName, DateOfBirth):
        self.emailid = emailid
        self.password = password
        self.FirstName = FirstName
        self.LastName = LastName
        self.DateOfBirth = DateOfBirth

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Ticket(db.Model):
    TicketID = db.Column(db.Integer, primary_key=True)
    emailid = db.Column(db.String(255), nullable=False)
    TransactionID = db.Column(db.String(255), nullable=False)
    Name = db.Column(db.Text, nullable=False)
    AdultCount = db.Column(db.Integer, nullable=False)
    ChildCount = db.Column(db.Integer, nullable=False)
    entryDate = db.Column(db.Date, nullable=False)
    purchaseDate = db.Column(db.Date, default=datetime.date.today, nullable=False)
    AmountPaid = db.Column(db.Float, nullable=False)
    DueAmount = db.Column(db.Float, nullable=False)
    CheckedIn = db.Column(db.Boolean)
    def __init__(self, TicketID, emailid, TransactionID, Name, AdultCount, ChildCount, entryDate, AmountPaid,
                 DueAmount):
        self.TicketID = TicketID
        self.emailid = emailid
        self.TransactionID = TransactionID
        self.Name = Name
        self.AdultCount = AdultCount
        self.ChildCount = ChildCount
        self.entryDate = entryDate
        self.AmountPaid = AmountPaid
        self.DueAmount = DueAmount

class feedbackform(db.Model):
    formid = db.Column(db.Integer, primary_key=True)
    emailid = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    feedback = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, default=datetime.date.today, nullable=False)
    def __init__(self, emailid, name, feedback):
        self.emailid = emailid
        self.name = name
        self.feedback = feedback

class maintenance(db.Model):
    maintenanceID = db.Column(db.Integer, primary_key=True)
    ride = db.Column(db.String(45), nullable=False)
    maintenancetype = db.Column(db.String(45), nullable=False)
    description = db.Column(db.String(45), nullable=False)
    status = db.Column(db.Integer, default=False , nullable=False)
    requestDate = db.Column(db.Date, default=datetime.date.today, nullable=False)
    completionDate = db.Column(db.Date, nullable=False)

    def __init__(self, ride, maintenancetype, description):
        # self.maintenanceID = maintenanceID
        self.ride = ride
        self.maintenancetype = maintenancetype
        self.description = description
        # self.status = status
        # self.requestDate = requestDate
        # self.completionDate = completionDate


class ridereview(db.Model):
    maintenanceID = db.Column(db.Integer, primary_key=True)
    ride = db.Column(db.String(45), nullable=False)
    maintenancetype = db.Column(db.String(45), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    requestDate = db.Column(db.Date, default=datetime.date.today, nullable=False)
    completionDate = db.Column(db.Date, nullable=False)

    def __init__(self, maintenanceID, ride, maintenancetype, status, requestDate, completionDate):
        self.maintenanceID = maintenanceID
        self.ride = ride
        self.maintenancetype = maintenancetype
        self.status = status
        self.requestDate = requestDate
        self.completionDate = completionDate

class userSchema(ma.Schema):
    class Meta:
        fields = ('emailid', 'password', 'FirstName', 'LastName', 'DateOfBirth', 'EmailId')


user_schema = userSchema()
users_schema = userSchema(many=True)


class ticketSchema(ma.Schema):
    class Meta:
        fields = (
        'TicketID', 'emailid', 'TransactionID', 'Name', 'AdultCount', 'ChildCount', 'entryDate', 'purchaseDate',
        'AmountPaid', 'DueAmount', 'CheckedIn')


ticket_schema = ticketSchema()
tickets_schema = ticketSchema(many=True)

class feedbackSchema(ma.Schema):
    class Meta:
        fields = ('formID', 'emailid', 'name', 'feedback', 'date')


feedback_schema = feedbackSchema()
feedbacks_schema = feedbackSchema(many=True)

class maintenanceSchema(ma.Schema):
    class Meta:
        fields = ('maintenanceID', 'ride', 'maintenancetype', 'status', 'requestDate', 'completionDate')

maintenance_schema = maintenanceSchema()
maintenances_schema = maintenanceSchema(many=True)


@app.route('/predicttime', methods=['POST'])
def predict_time():
    try:
        data = []
        for req in request.json:
            date = req['Date']
            time = req['Time']
            ride = req['Ride']
            people_count = req['PeopleCount']
            capacity = ride_capacity[ride]
            data.append([date, time, ride, capacity, people_count])

        wait_time = predict_wait_time(data)
        output = [{data[i][2]: math.ceil(wait_time[i])} for i in range(len(data))]

        return jsonify(output)
    except Exception as e:
        return jsonify({"message": "Error evaluation wait time", "error": str(e)}), 500


@app.route('/adduser', methods=['POST'])
@cross_origin()
def adduser():
    try:
        emailid = request.json['emailid']
        password = request.json['password']
        FirstName = request.json['FirstName']
        LastName = request.json['LastName']
        DateOfBirth = request.json['DateOfBirth']

        # Validate input (e.g., check if required fields are present)
        if not (emailid and password and FirstName and LastName and DateOfBirth):
            return jsonify({"message": "All fields are required"}), 400

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create the user object
        user = Users(emailid=emailid, password=hashed_password, FirstName=FirstName, LastName=LastName,
                     DateOfBirth=DateOfBirth)

        # Add to the database
        db.session.add(user)
        db.session.commit()

        # Return the newly created user data
        return jsonify({"message": "User created successfully", "user": user_schema.dump(user)})
    except Exception as e:
        return jsonify({"message": "Error creating user", "error": str(e)}), 500


@app.route('/getusers', methods=['GET'])
@cross_origin()
def getusers():
    try:
        users = Users.query.all()
        users_data = []

        for user in users:
            user_data = {
                'emailid': user.emailid,
                'FirstName': user.FirstName,
                'LastName': user.LastName,
                'DateOfBirth': user.DateOfBirth
            }
            users_data.append(user_data)

        return jsonify({"users": users_data})
    except Exception as e:
        return jsonify({"message": "Error fetching users", "error": str(e)}), 500


@app.route('/getuser/<emailid>/', methods=['GET'])
@cross_origin()
def getuser(emailid):
    try:
        user = Users.query.get(emailid)
        if not user:
            return jsonify({"message": "User not found"}), 404

        user_data = {
            'emailid': user.emailid,
            'FirstName': user.FirstName,
            'LastName': user.LastName,
            'DateOfBirth': user.DateOfBirth,
            'EmailId': user.EmailId
        }

        return jsonify(user_data)
    except Exception as e:
        return jsonify({"message": "Error fetching user", "error": str(e)}), 500


@app.route('/updateuser/<emailid>/', methods=['PUT'])
@cross_origin()
def updateuser(emailid):
    # Get the existing user from the database
    user = Users.query.get(emailid)

    if not user:
        return jsonify({"message": "User not found"}), NOT_FOUND

    # Extract the fields from the request (assuming JSON input)
    request_data = request.json
    updated_fields = {
        'FirstName': request_data.get('FirstName', user.FirstName),
        'LastName': request_data.get('LastName', user.LastName),
        'DateOfBirth': request_data.get('DateOfBirth', user.DateOfBirth),
        'EmailId': request_data.get('EmailId', user.EmailId)
    }

    # Update the user object
    for field, value in updated_fields.items():
        setattr(user, field, value)

    # Commit changes to the database
    db.session.commit()

    return user_schema.jsonify(user)


@app.route('/update_password/<emailid>/', methods=['POST'])
@cross_origin()
def update_password(emailid):
    user = Users.query.get(emailid)
    if not user:
        return jsonify({"message": "User not found"}), 404

    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')

    if not user or not (user.password == old_password):
        return jsonify({"message": "Incorrect old password"}), 400

    # Hash the new password
    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"})


@app.route('/validate_credentials', methods=['POST'])
@cross_origin()
def validate_credentials():
    try:
        provided_emailid = request.json.get('emailid')
        provided_password = request.json.get('password')

        user = Users.query.filter_by(emailid=provided_emailid).first()
        if (not user):
            return jsonify({"message": "No user found"}), 404
        else:
            if not (check_password_hash(user.password, provided_password)):
                return jsonify({"message": "Invalid credentials"}), 401

        return user_schema.jsonify(user), 200
    except Exception as e:
        return jsonify({"message": "Error validating credentials", "error": str(e)}), 500


def convertDate(date):
    return datetime.datetime.strptime(date, '%B %d, %Y').date()


@app.route('/buytickets', methods=['POST'])
@cross_origin()
def buytickets():
    try:
        emailid = request.json.get('emailid')
        adult_count = int(request.json.get('AdultCount'))
        child_count = int(request.json.get('ChildCount'))
        entry_date = convertDate(request.json.get('entryDate'))
        transaction_id = request.json.get('TransactionID')  # New parameter for transaction ID
        amount_paid = float(request.json.get('AmountPaid'))  # New parameter for amount paid
        due_amount = float(request.json.get('DueAmount'))  # New parameter for due amount
        name = request.json.get('Name')  # New parameter for name

        # if not emailid or not Users.query.get(emailid):
        #     return jsonify({"message": "User not found"}), 404

        ticket_id = f'{entry_date.strftime("%Y%m%d")}{Ticket.query.filter_by(entryDate=entry_date).count() + 1}'
        new_ticket = Ticket(TicketID=ticket_id, emailid=emailid, AdultCount=adult_count, ChildCount=child_count,
                            entryDate=entry_date, TransactionID=transaction_id, AmountPaid=amount_paid,
                            DueAmount=due_amount, Name=name)  # Update Ticket object creation

        db.session.add(new_ticket)
        db.session.commit()

        return jsonify({"TicketID": ticket_id, "message": "Ticket purchased successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Error purchasing ticket", "error": str(e)}), 500


@app.route('/getticketdetails', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_ticket_details():
    try:
        emailid = request.json.get('emailid')
        if not emailid:
            return jsonify({"message": "Please provide the Email Id"}), 404

        user_tickets = Ticket.query.filter_by(emailid=emailid).all()

        ticket_details = []
        for ticket in user_tickets:
            ticket_details.append({
                "emailid": ticket.emailid,
                "Name": ticket.Name,
                "TicketID": ticket.TicketID,
                "AdultCount": ticket.AdultCount,
                "ChildCount": ticket.ChildCount,
                "EntryDate": ticket.entryDate.strftime("%Y-%m-%d"),
                "PurchaseDate": ticket.purchaseDate.strftime("%Y-%m-%d"),
            })
        if ticket_details:
            return jsonify({"UserTickets": ticket_details}), 200
        else:
            return jsonify({"message": "No tickets found"}), 500
    except Exception as e:
        return jsonify({"message": "Error retrieving ticket details", "error": str(e)}), 500


@app.route('/validateticket', methods=['POST'])
@cross_origin()
def validate_ticket():
    try:
        ticket_id = request.json.get('TicketID')

        if not ticket_id:
            return jsonify({"message": "Ticket ID is missing"}), 400
        ticket_details = Ticket.query.get(ticket_id)
        if ticket_details.CheckedIn:
            return jsonify({"message": "Ticket is already checked"}), 400
        if not ticket_details:
            return jsonify({"message": "Ticket not found"}), 404

        # if not ticket_details.UserID == user_id:
        #     return jsonify({"message": "Ticket is not assigned to the correct user"}), 400

        if not ticket_details.entryDate == datetime.date.today():
            return jsonify({"message": "Ticket is booked for different date"}), 400

        ticket_details.CheckedIn = 1
        db.session.commit()

        return jsonify({"message": "Ticket is valid and Checked-In successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Error validating ticket", "error": str(e)}), 500


@app.route('/joinqueue', methods=['POST'])
def join_queue():
    try:
        ticket_id = request.json.get('TicketID')
        ride = request.json.get('Ride')

        if not ride:
            return jsonify({"message": "Missing ride name"}), 400

        if not ride in queue:
            return jsonify({"message": "No ride found"}), 400

        if not ticket_id:
            return jsonify({"message": "Ticket ID is missing"}), 400

        ticket_details = Ticket.query.get(ticket_id)

        if not ticket_details:
            return jsonify({"message": "Ticket not found"}), 404


        if not ticket_details.entryDate == datetime.date.today():
            return jsonify({"message": "Ticket is booked for different date"}), 400

        if not ticket_details:
            return jsonify({"message": "Ticket is not Checked-In"}), 400

        currentposition = len(queue[ride])
        if not ticket_id in queue[ride]:
            if ticket_details:
                with lock:
                    for i in range(ticket_details.AdultCount):
                        queue[ride].append(ticket_id)

                    for i in range(ticket_details.ChildCount):
                        queue[ride].append(ticket_id)
        else:
            currentposition = queue[ride].index(ticket_id)

        return jsonify({"currentPosition": currentposition, "currentLength": len(queue[ride])}), 200
    except Exception as e:
        return jsonify({"message": "Error joining in Queue", "error": str(e)}), 500

@app.route('/queuestatus', methods=['POST'])
def queuestatus():
    ticket_id = request.json.get('TicketID')
    ride = request.json.get('Ride')
    if ticket_id in queue[ride]:
        currentposition = queue[ride].index(ticket_id)
    else:
        currentposition = 'NA'

    return jsonify({"position": currentposition, "currentLength": len(queue[ride])})

@app.route('/queuedetails', methods=['POST'])
def queuedetails():
    ticket_id = request.json.get('TicketID')
    result = []
    for ride, q in queue.items():
        if ticket_id in q:
            result.append({"Ride": ride, "position": q.index(ticket_id), "currentLength": len(q)})

    return jsonify(result)

@app.route('/submitfeedback', methods=['POST'])
@cross_origin()
def submitfeedback():
    try:
        email = request.json.get('email')
        name = request.json.get('name')
        feedback_msg = request.json.get('feedback')

        new_feedback = feedbackform(emailid=email, name=name, feedback=feedback_msg)

        db.session.add(new_feedback)
        db.session.commit()

        return jsonify({"message": "Feedback submitted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Error submitting the feedback", "error": str(e)}), 500


@app.route('/getfeedback', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_feedback_details():
    try:
        fromdate = request.json.get('fromdate')
        todate = request.json.get('todate')

        if fromdate and todate:
            feedback_forms = feedbackform.query.filter(feedbackform.date.between(convertDate(fromdate), convertDate(todate))).all()
        elif fromdate:
            feedback_forms = feedbackform.query.filter(feedbackform.date.between(convertDate(fromdate), convertDate(fromdate))).all()
        else:
            feedback_forms = feedbackform.query.all()

        feedback_details = []
        for feedback_form in feedback_forms:
            feedback_details.append({
                "email": feedback_form.emailid,
                "name": feedback_form.name,
                "feedback": feedback_form.feedback,
                "date": feedback_form.date
            })
        if feedback_details:
            return jsonify({"feedbackforms": feedback_details}), 200
        else:
            return jsonify({"message": "No feedbacks found", "error": "No feedbacks found"}), 500
    except Exception as e:
        return jsonify({"message": "Error retrieving feedback details", "error": str(e)}), 500

@app.route('/submitmaintenance', methods=['POST'])
@cross_origin()
def submitmaintenance():
    try:
        ride = request.json.get('ride')
        maintenancetype = request.json.get('maintenanceType')
        description = request.json.get('description')

        new_maintenance = maintenance(ride=ride, maintenancetype=maintenancetype, description=description)

        db.session.add(new_maintenance)
        db.session.commit()

        return jsonify({"message": "Feedback submitted successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Error submitting the feedback", "error": str(e)}), 500

@app.route('/getmaintenance', methods=['POST'])
@cross_origin(supports_credentials=True)
def get_maintenance_details():
    try:
        fromdate = request.json.get('fromdate')
        todate = request.json.get('todate')

        if fromdate and todate:
            maintenance_datas = maintenance.query.filter(feedbackform.date.between(convertDate(fromdate), convertDate(todate))).all()
        elif fromdate:
            maintenance_datas = maintenance.query.filter(feedbackform.date.between(convertDate(fromdate), convertDate(fromdate))).all()
        else:
            maintenance_datas = maintenance.query.all()

        maintenance_details = []
        for maintenance_data in maintenance_datas:
            if maintenance_data.status:
                status = 'Completeted'
            else:
                status = 'Not Completeted'

            maintenance_details.append({
                "maintenanceID": maintenance_data.maintenanceID,
                "ride": maintenance_data.ride,
                "maintenancetype": maintenance_data.maintenancetype,
                "description": maintenance_data.description,
                "status": status,
                "requestdate": maintenance_data.requestDate,
                "compeltiondate": maintenance_data.completionDate,
            })

        if maintenance_details:
            return jsonify({"maintenance_details": maintenance_details}), 200
        else:
            return jsonify({"message": "No maintenance tickets found", "error": "No maintenance tickets found"}), 500
    except Exception as e:
        return jsonify({"message": "Error retrieving details", "error": str(e)}), 500


if __name__ == '__main__':
    app.run()
