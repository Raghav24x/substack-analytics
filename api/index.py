from vercel_wsgi import make_lambda_handler
from main import app  # Adjust if your Flask app object is in a different file

handler = make_lambda_handler(app)
