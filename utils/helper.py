import os
import uuid

from flask import render_template, url_for
from sendgrid.helpers.mail import Mail
from werkzeug.utils import secure_filename

from app import sendgrid_client


def modify_name(data):
    name = data['email'].split('@')[0]

    for i in name:
        if i.isdigit():
            name = name.replace(i, '')

    data['image_url'] = name


def generate_unique_id():
    unique_id = uuid.uuid4()
    return str(unique_id)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'jfif'}

UPLOAD_FOLDER = os.getcwd() + "/upload_profile_images"
if os.path.exists(UPLOAD_FOLDER):
    print("File exist")
else:
    os.mkdir(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_if_image_is_valid(request):
    if 'image_file' not in request.files and 'image' not in request.files:
        return 'No file part', 400

    file = request.files['image_file']

    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return filename
    else:
        return False


def send_registration_email(recipient):
    sender = 'virtoala0@gmail.com'
    subject = 'Welcome to Our App'
    message = "Welcome to our gym app. We are glad to have you here. "

    content = render_template('welcome_email.html', message=message)

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=content
    )

    try:
        sendgrid_client.send(message)

        return 'Email sent successfully'
    except Exception as e:
        print(str(e))
        return 'Failed to send email'


def send_reset_email(user, token):
    sender = 'virtoala0@gmail.com'
    recipient = user.email
    subject = 'Reset Your Password'

    reset_url = url_for('register.reset_password', token=token, _external=True)

    message = f'''To reset your password, visit the following link: {reset_url}
    If you did not make this request then simply ignore this email and no changes will be made.
    '''

    content = render_template('reset_password_email.html', reset_url=reset_url)

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=content
    )

    try:
        sendgrid_client.send(message)
        return 1
    except Exception as e:
        print(str(e))
        return 0
