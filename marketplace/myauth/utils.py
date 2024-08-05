from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


def resize_image(img: Image.Image) -> Image:
    """
    A function to reduce the size of the uploaded image.
    :param img: The image to be resized.
    :return: The resized image.
    """

    image = Image.open(img)

    max_height = 400
    max_width = 350
    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    output = BytesIO()
    image.save(output, format=image.format)
    output.seek(0)

    resized_image = InMemoryUploadedFile(
        output,
        'ImageField',
        img.name,
        img.content_type,
        output.tell,
        None
    )
    return resized_image
