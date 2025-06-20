from flask import Flask, render_template, request
import requests

app = Flask(__name__)

NHTSA_RECALLS_URL = "https://api.nhtsa.gov/recalls/recallsByVehicle"
NHTSA_COMPLAINTS_URL = "https://api.nhtsa.gov/complaints/complaintsByVehicle"
NHTSA_INVESTIGATIONS_URL = "https://api.nhtsa.gov/SafetyIssues"

@app.route('/', methods=['GET'])
def index():
    return render_template('search.html')

@app.route('/search', methods=['POST'])
def search():
    keywords = request.form['keywords']
    year = request.form['year']
    make = request.form['make']
    model = request.form.get('model', '')

    results = search_nhtsa_data(keywords, year, make, model)
    return render_template('search.html', results=results, keywords=keywords)

# --- Search logic helpers ---

def search_nhtsa_data(keywords, year, make, model):
    recalls = search_recalls(year, make, model)
    complaints = search_complaints(year, make, model)
    investigations = search_investigations(year, make, model)
    scored_recalls = match_and_score(recalls, 'Summary', keywords)
    scored_complaints = match_and_score(complaints, 'Summary', keywords)
    scored_investigations = match_and_score(investigations, 'Summary', keywords)
    return {
        'recalls': scored_recalls,
        'complaints': scored_complaints,
        'investigations': scored_investigations
    }


def search_recalls(year, make, model):
    params = {'make': make, 'modelYear': year}
    if model:
        params['model'] = model
    try:
        r = requests.get(NHTSA_RECALLS_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get('results', [])
    except Exception:
        return []


def search_complaints(year, make, model):
    params = {'make': make, 'modelYear': year}
    if model:
        params['model'] = model
    try:
        r = requests.get(NHTSA_COMPLAINTS_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get('results', [])
    except Exception:
        return []


def search_investigations(year, make, model):
    params = {'make': make, 'modelYear': year}
    if model:
        params['model'] = model
    try:
        r = requests.get(NHTSA_INVESTIGATIONS_URL, params=params, timeout=10)
        r.raise_for_status()
        return r.json().get('results', [])
    except Exception:
        return []


def match_and_score(items, field, keywords):
    matches = []
    for item in items:
        text = item.get(field, '')
        score = calculate_relevance_score(text, keywords)
        if score > 0:
            matches.append({
                'score': score,
                'data': item
            })
    matches.sort(key=lambda x: x['score'], reverse=True)
    return matches


def calculate_relevance_score(text, keywords):
    score = 0
    text_lower = text.lower()
    for keyword in keywords.split():
        if keyword.lower() in text_lower:
            score += 1
            if keyword.lower() in ['stall', 'brake', 'airbag', 'fire']:
                score += 2
    return score


if __name__ == '__main__':
    app.run(debug=True)
