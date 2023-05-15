import uuid


def modify_name(data):
    name = data['email'].split('@')[0]

    for i in name:
        if i.isdigit():
            name = name.replace(i, '')

    data['image_url'] = name


def generate_unique_id():
    unique_id = uuid.uuid4()
    return str(unique_id)

