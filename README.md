# Black Belt Organizer

### Description:
This program collects and organizes all information needed to order new Black Belts.

Python, Flask, SQLAlchemy, SQLite, HTML, CSS, Flask-Login and Flask-WTF.

#### Setting up the database
In app.py, the SQLite database is configured, the Flask application object is initialized and the models are defined.
##### Models:
"user" is a table that contains the email, password_hash, role and school id for the instructors who will be using the program.

"student" holds all students past and present.  Columns include name, rank and school.

"school" keeps track of the school locations for each student and instructor

"belt" holds all the information about the belt an instructor would like to order.

"order" keeps track of all orders the administrator makes

"schoolorder"  keeps track of all orders that the instructor makes that have actually been ordered by the administrator

"orderbelt" links the orders to the belts

"archive" holds old student information for those no longer active


#### Using the program
The opening page is a sign in page for instructors and administrators to log in with their email and password.  If they forget their password they can click on "Forget username or password?"  and they will be directed to a page to ask their email address and an email will be sent with a temporary password.

For demonstration purposes, two accounts are available:
    username: instructor  password: instructor
    username: admin  password: admin


#### Program Options
Logging in sends you to the options page.

##### Add a New Student
Instructors and administrators can both enter a new student's name along with their current rank and level.  Administrators must also choose which school this student is from.  (Instructors default to their own school.)

##### Edit or Remove a Student
This page presents all students of the instructor (or all students for administrators).  Clicking on "Edit this Student" sends the user to a page where information can be edited.  Clicking on "Move this Student to the Archives" will take the student out of the student table and into the archive table.  The student will no longer show up in any of the instructor's lists.  I plan to eventually write in the ability for an administrator to access the archive but I left it out at this time since it would only be rarely used.

##### Make or Edit a Belt Order
The top of the page lists all an instructor's students in a drop down list.  If the instructor wants to order a belt for this student they choose the student and click on the add button.

The bottom of the page lists all belts in rank - level order.  They can edit the name, rank, level and size of the belt and then click on the save changes button.  If they haven't yet chosen a belt size, the cell appears in red.  Last size ordered is displayed to help with size errors.

##### View a previous Belt Order
This page lists all orders from this school made by the administrator by date.  Clicking on the date will give a list of belts ordered on this date.

##### Register an Instructor, Edit or Remove an Instructor
These pages are only available to an administrator.

##### Send Current Order
Send Current Order sends the administrator to a page that list all the belts that the instructors from all schools want to order.  It only lists those belts that have a size entered.  (Going to the Make or Edit a Belt Order page will allow the administrator to see any red cells with no size entered and can either notify the instructor to add the size or order without this belt.  The belt will stay in the instructor's list of belts to be ordered.)

Clicking on the make this order button will:
- add a new order to the order table
- adds each belt to the beltorder table
- changes the is_ordered status of the belt to True
- changes each student's current rank to the rank ordered
- make csv files and store them in the orders folder so that the orders can be accessed later in "View a previous Belt Order".




