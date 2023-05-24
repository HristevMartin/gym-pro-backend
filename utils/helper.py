import os
import uuid

from werkzeug.utils import secure_filename


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

    file = request.files['image_file'] or request.files['image']

    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(path)
        return filename
    else:
        return False
