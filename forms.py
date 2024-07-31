from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, RadioField
from wtforms.validators import DataRequired, EqualTo


class AddstudentForm(FlaskForm):
    first_name = StringField('First Name: ')
    last_name = StringField('Last Name: ', validators=[DataRequired()])
    rank = SelectField('Current Rank: ', choices=[
                       'triple stripe', '1', '2', '3', '4', '5', '6', '7', '8'], validators=[DataRequired()])
    level = RadioField('Current Level: ', choices=[
                       ('Junior', 'Junior'), ('Adult', 'Adult')], validators=[DataRequired()])
    school_id = SelectField('School: ', choices=[('1', 'School 1'), ('2', 'School 2'), (
        '3', 'School 3'), ('4', 'School 4'), ('5', 'School 5'), ('6', 'School 6'), ('7', 'School 7')])
    submit = SubmitField('Save')


class EmailForm(FlaskForm):
    email = StringField('Email: ')
    submit = SubmitField('Request username and temporary password.')


class LoginForm(FlaskForm):
    username = StringField('Email Address:  ', validators=[DataRequired()])
    password = PasswordField('Password:  ')
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign in')


class PasswordForm(FlaskForm):
    oldpassword = PasswordField('Old Password: ', validators=[DataRequired()])
    password = PasswordField('New Password: ', validators=[DataRequired()])
    password2 = PasswordField('Repeat New Password: ', validators=[DataRequired(), EqualTo(
        'password', message="New Password and Repeat Password must match.")])
    submit = SubmitField('Change Password')


class RegistrationForm(FlaskForm):
    email = StringField('Email: ')
    role = SelectField('Role:', choices=['instructor', 'admin'], validators=[DataRequired()])
    school_id = SelectField('School: ', choices=[('1', 'School 1'), ('2', 'School 2'), (
        '3', 'School 3'), ('4', 'School 4'), ('5', 'School 5'), ('6', 'School 6'), ('7', 'School 7')])
    submit = SubmitField('Submit')
