import csv
import os
import smtplib
import string

from app import app, db, Archive, Belt, Order, Orderbelt, School, Schoolorder, Student, User, login_manager
from collections import defaultdict
from datetime import datetime, timezone
from flask import request, render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from forms import LoginForm, EmailForm, PasswordForm, AddstudentForm, RegistrationForm
from secrets import choice


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


# sign in page

@app.route('/', methods=['GET', 'POST'])
def signin():
    form = LoginForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page or url_for('options'))
        flash("Username or password is incorrect. Please try again.")
        return redirect(url_for('signin'))

    return render_template('signin.html', form=form)


# Both instructor and admin can add a new student to db

@app.route('/addstudent', methods=['GET', 'POST'])
@login_required
def addstudent():
    form = AddstudentForm()
    school_id = current_user.school_id
    if request.method == "POST":
        first_name = form.first_name.data
        last_name = form.last_name.data
        rank = form.rank.data
        level = form.level.data
        if not last_name or not rank or not level:
            flash("Please fill in all fields.")
            return redirect(url_for('addstudent'))
        if rank == 'triple stripe':
            rank = 0
        else:
            rank = int(rank)
        if current_user.role == 'admin':
            school_id = form.school_id.data
            school_id = school_id.strip('(').strip(')')
        student = Student(first_name=first_name, last_name=last_name,
                          rank=rank, level=level, school_id=school_id)
        db.session.add(student)
        db.session.commit()
        flash('You have successfully added the Student.')
        return redirect(url_for('addstudent'))

    return render_template('addstudent.html', form=form)


# add student to instructor belt order

@app.route('/addtoorder', methods=['POST'])
@login_required
def addtoorder():
    studentid = request.form['studentid']
    studentid = studentid.strip(')').strip('(')
    if studentid:
        studentid = int(studentid)
        student = Student.query.filter_by(id=studentid).first()
        rank = student.rank + 1
        if rank == 8:
            rank = 7
        belt = Belt(student_id=studentid, request_date=datetime.now(
            timezone.utc), rank=rank, is_ordered=False)
        db.session.add(belt)
        db.session.commit()

    return redirect(url_for('beltorderinstructor'))


# Put student in archive

@app.route('/archive/<studentid>', methods=['GET', 'POST'])
@login_required
def archive(studentid):
    student = Student.query.filter_by(id=int(studentid)).first()
    archive = Archive(student_id=student.id, first_name=student.first_name, last_name=student.last_name,
                      rank=student.rank, level=student.level, school_id=student.school_id, extra=student.extra)
    belts = Belt.query.filter_by(student_id=student.id).filter_by(is_ordered=False).all()
    for belt in belts:
        db.session.delete(belt)
    db.session.add(archive)
    db.session.delete(student)
    db.session.commit()

    flash('You have successfully moved the Student.')
    return redirect(url_for('choosestudent'))


# make or edit a belt order for instructors - admin can also view and edit

@app.route('/beltorderinstructor', methods=['GET', 'POST'])
@login_required
def beltorderinstructor():
    if current_user.role == 'admin':
        school_location = "All Schools"
        # get a list of all students
        student_list = Student.query.order_by(Student.last_name, Student.first_name).all()
        student_set = {student.id for student in student_list}
        current_belt_orders = Belt.query.filter(Belt.is_ordered == False).all()
    else:
        # get a list of all students for this instructor
        school = School.query.filter_by(id=current_user.school_id).first()
        school_location = school.location
        student_list = school.students
        student_set = {student.id for student in student_list}
        # get a list of belt orders for this school that haven't been ordered yet
        current_belt_orders = Belt.query.filter(Belt.student_id.in_(
            student_set)).filter(Belt.is_ordered == False).all()
    belt_order_list = []
    # find size of belt in latest order if exists then make a list of all info needed and put in belt_order_list
    # remove this student id from student_set so we can't choose to order a second belt at the same time
    for order in current_belt_orders:
        student = Student.query.filter_by(id=order.student_id).first()
        school = School.query.filter_by(id=student.school_id).first()
        belt_order_list.append([student.last_name.upper(), student.first_name.upper(), student.id,
                               student.level, order.id, order.rank, order.size, student.last_size, school.location])
        student_set.discard(student.id)
    # sort belt_order_list by last name, first name
    belt_order_list.sort(key=lambda x: (x[0], x[1]))
    # pair down student_list to only those that don't have a current order
    student_list = [student for student in student_list if student.id in student_set]
    ranks = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh"]

    return render_template("beltorderinstructor.html", belt_order_list=belt_order_list, student_list=student_list, school=school_location, ranks=ranks)


# make a belt order file for individual schools and whole school

@app.route('/beltorderfile', methods=['POST'])
@login_required
def beltorderfile():
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    belts = Belt.query.filter(Belt.is_ordered == False).filter(Belt.size != None).all()
    if not belts:
        flash("No belts to order.")
        return redirect(url_for('options'))
    order = Order(order_date=datetime.now(timezone.utc))
    #order = Order(order_date=datetime(2024, 4, 26))
    db.session.add(order)
    db.session.commit()
    # all school orders will be in orders file named order1.csv etc.  individual school orders will be indiana1.csv
    filename = 'orders/order'+str(order.id)+".csv"
    filenames = ["", 'orders/school1'+str(order.id)+".csv", 'orders/school2'+str(order.id)+".csv", 'orders/school3'+str(order.id)+".csv", 'orders/school4'+str(
        order.id)+".csv", 'orders/school5'+str(order.id)+".csv", 'orders/school6'+str(order.id)+".csv", 'orders/school7'+str(order.id)+".csv"]
    # Write files
    for belt in belts:
        student = Student.query.filter_by(id=belt.student_id).first()
        orderbelt = Orderbelt(order_id=order.id, belt_id=belt.id)
        db.session.add(orderbelt)
        belt.is_ordered = True
        student.rank = belt.rank
        schoolorder = Schoolorder.query.filter_by(
            school_id=student.school_id, order_id=order.id).first()
        if not schoolorder:
            s = Schoolorder(school_id=student.school_id, order_id=order.id)
            db.session.add(s)
        db.session.commit()
        school = School.query.filter_by(id=student.school_id).first()
        with open(filename, 'a', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow([student.first_name.upper(), student.last_name.upper(),
                                belt.size, belt.rank, student.level, school.location])
        with open(filenames[student.school_id], 'a', newline='') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',')
            spamwriter.writerow([student.first_name.upper(),
                                student.last_name.upper(), belt.size, belt.rank, student.level])

    flash("Successfully made orders")
    return redirect(url_for('options'))


# make a belt order to send - Views order to confirm then click button to make order

@app.route('/beltordersend', methods=['GET', 'POST'])
@login_required
def beltordersend():
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))

    # get a list of belt orders that haven't been ordered yet
    current_belt_orders = Belt.query.filter_by(is_ordered=False).all()
    belt_order_list = []

    for belt in current_belt_orders:
        student = Student.query.filter_by(id=belt.student_id).first()
        if belt.size:
            belt_order_list.append([belt.size, student.last_name.upper(),
                                   student.first_name.upper(), belt.rank, student.level])

    # sort belt_order_list by size, last name
    belt_order_list.sort(key=lambda x: (x[0], x[1]))
    ranks = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth', 'Seventh']
    colors = ['Yellow', 'Red', 'Red', 'Red', 'Red', 'Red', 'Red']

    return render_template("beltordersend.html", belt_order_list=belt_order_list, ranks=ranks, colors=colors)


# User changes own password

@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def changepassword():
    form = PasswordForm()
    if form.password.data != form.password2.data:
        flash("New Password and Repeat Password must match.")
        return redirect(url_for('chpassword'))
    if form.validate_on_submit():
        if not current_user.check_password(form.oldpassword.data):
            flash("Password is incorrect. Try again or log out and request a new password sent from the Sign in page.")
            return redirect(url_for('chpassword'))

        current_user.set_password(form.password.data)
        db.session.commit()
        flash("Password was successfully changed.")

        return redirect(url_for('options'))
    return render_template('changepassword.html', form=form)




@app.route('/choosearchive', methods=['GET', 'POST'])
@login_required
def choosearchive():
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))

    studentlist = Archive.query.order_by(Archive.last_name, Archive.first_name).all()

    return render_template('choosearchive.html', studentlist=studentlist)


# choose instructor to edit or delete

@app.route('/chooseinstructor', methods=['GET', 'POST'])
@login_required
def chooseinstructor():
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    instructorlist = User.query.filter(User.id != 1).all()
    return render_template('chooseinstructor.html', instructorlist=instructorlist)


# Choose which order to print out of a list of all orders admin

@app.route('/chooseorderadmin', methods=['GET'])
@login_required
def chooseorderadmin():
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    orders = Order.query.all()
    order_list = []
    for order in orders:
        date = str(order.order_date.month)+"-" + \
            str(order.order_date.day)+'-'+str(order.order_date.year)
        order_list.append((order.id, date))
    return render_template('chooseorderadmin.html', order_list=order_list)


# Choose which order to print out of a list of all orders

@app.route('/chooseorderinstructor', methods=['GET'])
@login_required
def chooseorderinstructor():
    schoolorders = Schoolorder.query.filter_by(school_id=current_user.school_id).all()
    order_set = {order.order_id for order in schoolorders}
    orders = Order.query.filter(Order.id.in_(order_set)).all()
    order_list = []
    for order in orders:
        date = str(order.order_date.month)+"-" + \
            str(order.order_date.day)+'-'+str(order.order_date.year)
        order_list.append((order.id, date))
    return render_template('chooseorderinstructor.html', order_list=order_list)


# choose student to edit or archive

@app.route('/choosestudent', methods=['GET', 'POST'])
@login_required
def choosestudent():
    if current_user.role == 'admin':
        studentlist = Student.query.order_by(Student.last_name, Student.first_name).all()
    else:
        studentlist = Student.query.filter_by(school_id=current_user.school_id).order_by(
            Student.last_name, Student.first_name).all()
    return render_template('choosestudent.html', studentlist=studentlist)


# Delete Instructor

@app.route('/delete/<userid>', methods=['GET', 'POST'])
@login_required
def delete(userid):
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    user = User.query.filter_by(id=int(userid)).first()

    db.session.delete(user)
    db.session.commit()

    flash('You have successfully deleted the User.')
    return redirect(url_for('chooseinstructor'))


# Delete student from archive

@app.route('/deletestudent/<archiveid>', methods=['GET', 'POST'])
@login_required
def deletestudent(archiveid):
    if current_user.role != 'admin':
        flash("No access to this page")
        return redirect(url_for('options'))
    this_student = Archive.query.filter_by(id = archiveid).first()
    db.session.delete(this_student)
    db.session.commit()
    flash('You have successfully deleted the Student.')
    return redirect(url_for('choosearchive'))


# edit the chosen instructor

@app.route('/editinstructor/<userid>', methods=['GET', 'POST'])
@login_required
def editinstructor(userid):
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    user = User.query.filter_by(id=int(userid)).first()
    form = RegistrationForm()

    if request.method == "POST":
        email = form.email.data
        role = form.role.data
        school_id = form.school_id.data

        if not email or not role or not school_id:
            flash("Please fill in all fields.")
            return redirect(url_for('editinstructor', userid=user.id))
        school_id = school_id.strip('(').strip(')')

        user.email = email
        user.role = role
        user.school_id = school_id

        db.session.commit()
        flash('You have successfully edited the User.')
        return redirect(url_for('chooseinstructor'))

    form.email.data = user.email
    form.role.data = user.role
    form.school_id.data = str(user.school_id)

    return render_template('editinstructor.html', form=form, user=user)


# edit instructor belt order

@app.route('/editorderinstructor', methods=['POST'])
@login_required
def editorderinstructor():
    last_names = request.form.getlist('last_name')
    first_names = request.form.getlist('first_name')
    studentids = request.form.getlist('studentid')
    levels = request.form.getlist('level')
    beltids = request.form.getlist('beltid')
    ranks = request.form.getlist('rank')
    sizes = request.form.getlist('size')
    removes = request.form.getlist('remove')
    info_array = zip(last_names, first_names, studentids, levels, beltids, ranks, sizes)
    for info in info_array:
        student = Student.query.filter_by(id=int(info[2])).first()
        if student.last_name != info[0]:
            student.last_name = info[0]
        if student.first_name != info[1]:
            student.first_name = info[1]
        if student.level != info[3]:
            student.level = info[3]
        belt = Belt.query.filter_by(id=int(info[4])).first()
        if info[5] and belt.rank != int(info[5]):
            belt.rank = int(info[5])
            belt.request_date = datetime.now(timezone.utc)
        if info[6] and belt.size != int(info[6]):
            belt.size = int(info[6])
            belt.request_date = datetime.now(timezone.utc)
    for beltid in removes:
        belt = Belt.query.filter_by(id=int(beltid)).first()
        db.session.delete(belt)
    db.session.commit()
    return redirect(url_for('beltorderinstructor'))


# edit the chosen student

@app.route('/editstudent/<studentid>', methods=['GET', 'POST'])
@login_required
def editstudent(studentid):
    student = Student.query.filter_by(id=int(studentid)).first()
    form = AddstudentForm()

    if request.method == "POST":
        first_name = form.first_name.data
        last_name = form.last_name.data
        rank = form.rank.data
        level = form.level.data
        if not last_name or not rank or not level:
            flash("Please fill in all fields.")
            return redirect(url_for('editstudent', studentid=studentid))
        if rank == 'triple stripe':
            rank = 0
        else:
            rank = int(rank)
        if current_user.role == 'admin':
            school_id = form.school_id.data
            school_id = school_id.strip('(').strip(')')
            student.school_id = school_id
        student.first_name = first_name
        student.last_name = last_name
        student.rank = rank
        student.level = level

        db.session.commit()
        flash('You have successfully edited the Student.')
        return redirect(url_for('choosestudent'))

    form.first_name.data = student.first_name
    form.last_name.data = student.last_name
    form.rank.data = str(student.rank)
    form.level.data = student.level
    form.school_id.data = str(student.school_id)

    return render_template('editstudent.html', form=form, student=student)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('signin'))


# gets to all pages

@app.route('/options')
@login_required
def options():
    return render_template('options.html')


# view past order for company - sort by size - no heading

@app.route('/printorderc/<orderid>', methods=['GET', 'POST'])
@login_required
def printorderc(orderid):
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    order = Order.query.filter_by(id=orderid).first()
    junior = defaultdict(list)
    adult = defaultdict(list)
    with open('orders/order' + orderid + '.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row in spamreader:
            # reminder size and rank are strings here
            if row[4] == 'Junior':
                junior[int(row[3])].append((row[0], row[1], row[2], row[5]))
            else:
                adult[int(row[3])].append((row[0], row[1], row[2], row[5]))
    # sort by size, last_name
    for belt in junior.values():
        belt = belt.sort(key=lambda x: (x[2], x[1]))
    for belt in adult.values():
        belt = belt.sort(key=lambda x: (x[2], x[1]))
    ranks = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh"]
    date = str(order.order_date.month)+"-"+str(order.order_date.day)+'-'+str(order.order_date.year)

    return render_template('printordercompany.html', junior=junior, adult=adult, date=date, ranks=ranks)


# view past order for admin as an instructor - includes school

@app.route('/printorderi/<orderid>', methods=['GET', 'POST'])
@login_required
def printorderi(orderid):
    if current_user.role != 'admin':
        flash("You do not have access to this page")
        return redirect(url_for('/options'))
    order = Order.query.filter_by(id=orderid).first()
    junior = defaultdict(list)
    adult = defaultdict(list)
    with open('orders/order' + orderid + '.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row in spamreader:
            # reminder size and rank are strings here
            if row[4] == 'Junior':
                junior[int(row[3])].append((row[0], row[1], row[2], row[5]))
            else:
                adult[int(row[3])].append((row[0], row[1], row[2], row[5]))
    # sort by last_name, first_name
    for belt in junior.values():
        belt = belt.sort(key=lambda x: (x[1], x[0]))
    for belt in adult.values():
        belt = belt.sort(key=lambda x: (x[1], x[0]))
    ranks = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh"]
    date = str(order.order_date.month)+"-"+str(order.order_date.day)+'-'+str(order.order_date.year)

    return render_template('printorderinstructor.html', junior=junior, adult=adult, date=date, ranks=ranks, school="Young Brothers")


# view past order for instructors

@app.route('/printorderinstructor/<orderid>', methods=['GET', 'POST'])
@login_required
def printorderinstructor(orderid):
    school = School.query.filter_by(id=current_user.school_id).first()
    order = Order.query.filter_by(id=orderid).first()
    junior = defaultdict(list)
    adult = defaultdict(list)
    with open('orders/'+school.location.lower()+orderid+'.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        for row in spamreader:
            # reminder size and rank are strings here
            if row[4] == 'Junior':
                junior[int(row[3])].append((row[0], row[1], row[2]))
            else:
                adult[int(row[3])].append((row[0], row[1], row[2]))
    # sort by last_name, first_name
    for belt in junior.values():
        belt = belt.sort(key=lambda x: (x[1], x[0]))
    for belt in adult.values():
        belt = belt.sort(key=lambda x: (x[1], x[0]))
    ranks = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh"]
    date = str(order.order_date.month)+"-"+str(order.order_date.day)+'-'+str(order.order_date.year)

    return render_template('printorderinstructor.html', junior=junior, adult=adult, date=date, school=school.location, ranks=ranks)


@app.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if current_user.role != 'admin':
        flash("No access to this page")
        return redirect(url_for('options'))
    form = RegistrationForm()

    if request.method == "POST":

        email = form.email.data
        role = form.role.data
        school_id = form.school_id.data

        if not email or not role or not school_id:
            flash("Please fill in all fields.")
            return redirect(url_for('register'))

        school_id = school_id.strip(')').strip('(')
        user = User(email=email, role=role, school_id=school_id)
        db.session.add(user)
        db.session.commit()
        temp = ''.join([choice(string.ascii_lowercase + string.digits) for _ in range(8)])
        user.set_password(temp)
        db.session.commit()

# ##Be sure to add real website
        sender = '@yahoo.com'
        recipient = user.email
        content = f"From the Belt Order Site at http***********.com\n\nYour temporary password is: {temp}\n\nPlease log in and change your password."
        header = 'To:' + recipient+'\nFrom:'+sender+'\nsubject: Belt Order Site\n\n'
        content = header + content
        mail = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        mail.ehlo()
        mail.starttls()
        mail.login(sender, os.environ.get('API_KEY'))
        mail.sendmail(sender, recipient, content)
        mail.close()

        flash('Successfully Registered User')
        return redirect(url_for('register'))

    return render_template('register.html', form=form)


# Reinstate student from archive

@app.route('/returnstudent/<archiveid>', methods=['GET', 'POST'])
@login_required
def returnstudent(archiveid):
    if current_user.role != 'admin':
        flash("No access to this page")
        return redirect(url_for('options'))
    this_student = Archive.query.filter_by(id = archiveid).first()

    student = Student(first_name=this_student.first_name, last_name=this_student.last_name,
                        rank=this_student.rank, level=this_student.level, school_id=this_student.school_id)
    db.session.add(student)
    db.session.delete(this_student)
    db.session.commit()
    flash('You have successfully added the Student.')
    return redirect(url_for('choosearchive'))



# user requests password reset

@app.route('/resetpassword', methods=['GET', 'POST'])
def resetpassword():
    form = EmailForm()
    if form.validate_on_submit():
        uemail = form.email.data
        user = User.query.filter_by(email=uemail).first()
        if not user:
            flash("This is not a valid email address.")
            return redirect('/resetpassword')
        temp = ''.join([choice(string.ascii_lowercase + string.digits) for _ in range(8)])
        user.set_password(temp)
        db.session.commit()

# ##Be sure to add real website
        sender = '@yahoo.com'
        recipient = user.email

        content = f"From the Belt Order Site at   https://**************.com\n\nYour temporary password is: {temp}\n\nPlease log in and change your password."
        header = 'To:'+recipient+'\nFrom:'+sender+'\nsubject: Belt Order Site\n\n'
        content = header + content
        mail = smtplib.SMTP('smtp.mail.yahoo.com', 587)
        mail.ehlo()
        mail.starttls()
        mail.login(sender, os.environ.get('API_KEY'))
        mail.sendmail(sender, recipient, content)
        mail.close()

        flash('Check your email and come back to log in and change your password.')
        return redirect(url_for('signin'))

    return render_template('resetpassword.html', form=form)
