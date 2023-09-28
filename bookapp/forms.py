from flask_wtf import FlaskForm
from flask_wtf.file import FileField,FileAllowed,FileRequired
from wtforms import StringField,SubmitField,TextAreaField,PasswordField,SubmitField
from wtforms.validators import Email,DataRequired,EqualTo,Length

class RegForm(FlaskForm):
    fullname= StringField("FirstName",validators=[DataRequired('The Fullname Must Be Set')])   
    email= StringField("Email",validators=[Email('Invalid Email Address'),DataRequired(message='Email Must Be Supplied')])
    pwd= PasswordField("Enter Password",validators=[DataRequired()])
    confpwd= PasswordField("Confirm Password",validators=[EqualTo('pwd',message="Bros, Let The Two Password Match..")])    
    btnsubmit=SubmitField("Register!")


class DpForm(FlaskForm):
    dp= FileField("Upload A Profile Picture",validators=(FileRequired(),FileAllowed(['jpg','png','jpeg'])))
    btnupload=SubmitField("Upload Picture")

class ProfileForm(FlaskForm):
    fullname= StringField("FirstName",validators=[DataRequired('The Fullname Must Be Set')])   
    btnsubmit=SubmitField("Update Profile!")

class ContactForm(FlaskForm):
    email= StringField("Email",validators=[Email('Invalid Email Address'),DataRequired(message='Please Supply Email Address')])
    btnsubmit=SubmitField("Suscribe")
