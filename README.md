# Hamid Ali Awan — Portfolio

## Setup

1. Install Python 3.8+ and pip
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the app:
   ```
   python app.py
   ```
4. Open http://localhost:5000

## Customization

- **Social links**: Edit `templates/index.html` — search for `your-profile` and replace with your actual URLs
- **Contact info**: Edit email, phone, location in `templates/index.html` — search for `EDIT:`
- **CV download**: Place your CV as `static/cv/Hamid_Ali_Awan_CV.pdf`
- **Profile photo**: Add photo to `static/img/photo.jpg` and uncomment the `<img>` tag in the hero section
- **Projects**: Edit the project cards in the Projects section

## Structure

```
├── app.py                  # Flask backend
├── requirements.txt
├── templates/
│   └── index.html          # Main page
└── static/
    ├── css/style.css       # Styles
    ├── js/main.js          # Animations & interactions
    ├── cv/                 # Place CV here
    └── img/                # Place images here
```
