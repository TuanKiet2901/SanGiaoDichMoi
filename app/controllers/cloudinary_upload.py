import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, render_template_string
from flask_login import login_required

cloudinary.config(
  cloud_name = 'dzudbjijz',
  api_key = '594476365858465',
  api_secret = 'xQlA4rq0PGahVp_rpsWyejum-F0'
)

cloudinary_bp = Blueprint('cloudinary', __name__)

UPLOAD_FORM = '''
<!doctype html>
<title>Upload to Cloudinary</title>
<h1>Upload file lên Cloudinary</h1>
<form method=post enctype=multipart/form-data>
  <input type=file name=file>
  <input type=submit value=Upload>
</form>
{% if url %}
  <h2>Ảnh đã upload:</h2>
  <img src="{{ url }}" width="300">
  <p>Link: <a href="{{ url }}">{{ url }}</a></p>
{% endif %}
'''

@cloudinary_bp.route('/cloudinary-upload', methods=['GET', 'POST'])
@login_required
def upload():
    url = None
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400
        result = cloudinary.uploader.upload(file)
        url = result.get('secure_url')
    return render_template_string(UPLOAD_FORM, url=url)
