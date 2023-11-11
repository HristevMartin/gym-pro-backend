import os
import uuid

from flask import render_template, url_for
from sendgrid.helpers.mail import Mail

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
    from werkzeug.utils import secure_filename
    from google.cloud import storage

    bucket_name = 'gym-image-bucket'

    def generate_public_url(blob_name):
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

    if 'image_file' not in request.files and 'image' not in request.files:
        return 'No file part', 400

    file = request.files['image_file']

    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        service_account_info = os.environ.get('GCP_SERVICE_ACCOUNT')
        import json
        if os.getenv('project') == "local":
            storage_client = storage.Client.from_service_account_json(
                r'C:\Users\hrist\OneDrive\Desktop\gcp training\gym-website-393216-dc707085ff77.json')

        # For production, decode the base64 string
        else:
            # service_account_info = json.loads(base64.b64decode(os.environ.get("GCP_SERVICE_ACCOUNT")).decode("utf-8"))
            # storage_client = storage.Client.from_service_account_info(service_account_info)
            service_account_info = json.loads(os.environ.get("GCP_SERVICE_ACCOUNT"))
            storage_client = storage.Client.from_service_account_info(service_account_info)

        bucket = storage_client.get_bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_file(file)

        # return the public url
        return generate_public_url(filename)
    else:
        return False


def send_registration_email(recipient):
    sender = 'virtoala0@gmail.com'
    subject = 'Welcome to Our App'
    message = "Welcome to our gym hub marketplace. We are glad to have you here. "

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
    project = os.getenv('project')

    if project == 'production':
        reset_url = f"https://pro-gym-4285b.web.app{url_for('register.reset_password', token=token)}"
    else:
        reset_url = url_for('register.reset_password', token=token, _external=True)

    sender = 'virtoala0@gmail.com'
    recipient = user.email
    subject = 'Reset Your Password'

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
