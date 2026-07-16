from flask import Flask, render_template, request, jsonify, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-cv')
def download_cv():
    # Place your CV file as 'static/cv/Hamid_Ali_Awan_CV.pdf'
    return send_from_directory('static/cv', 'Hamid_Ali_Awan_CV.pdf', as_attachment=True)

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name', '')
    email = data.get('email', '')
    subject = data.get('subject', '')
    message = data.get('message', '')
    # TODO: Save to database or send email
    print(f"Contact from {name} ({email}): {subject} - {message}")
    return jsonify({'status': 'success', 'message': 'Message received! I will get back to you soon.'})

if __name__ == '__main__':
    os.makedirs('static/cv', exist_ok=True)
    app.run(debug=True, port=5000)
