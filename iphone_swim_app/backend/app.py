from flask import Flask, render_template, request, jsonify
from db import init_db, add_swimmer, get_swimmers, add_result, get_results_for_swimmer, get_all_results, update_pb_cache
from scraper import fetch_results_from_url

app = Flask(__name__)
init_db()

@app.route('/')
def index():
    swimmers = get_swimmers()
    results = get_all_results()
    return render_template('index.html', swimmers=swimmers, results=results)

@app.route('/api/swimmers', methods=['GET', 'POST'])
def swimmers_api():
    if request.method == 'POST':
        data = request.get_json(force=True)
        swimmer_id = add_swimmer(
            name=data.get('name', '').strip(),
            gender=data.get('gender', '').strip(),
            birth_year=data.get('birth_year')
        )
        return jsonify({'ok': True, 'swimmer_id': swimmer_id})
    return jsonify(get_swimmers())

@app.route('/api/results', methods=['POST'])
def results_api():
    data = request.get_json(force=True)
    add_result(
        swimmer_id=data['swimmer_id'],
        meet_name=data.get('meet_name', '').strip(),
        event_name=data.get('event_name', '').strip(),
        course=data.get('course', '').strip(),
        time_text=data.get('time_text', '').strip(),
        rank_text=data.get('rank_text', '').strip(),
        meet_date=data.get('meet_date', '').strip(),
        source_url=data.get('source_url', '').strip(),
    )
    update_pb_cache(data['swimmer_id'])
    return jsonify({'ok': True})

@app.route('/api/swimmers/<int:swimmer_id>/results')
def swimmer_results(swimmer_id):
    return jsonify(get_results_for_swimmer(swimmer_id))

@app.route('/api/import-url', methods=['POST'])
def import_url():
    data = request.get_json(force=True)
    swimmer_id = data['swimmer_id']
    url = data['url']
    imported = fetch_results_from_url(url)
    count = 0
    for item in imported:
        add_result(
            swimmer_id=swimmer_id,
            meet_name=item.get('meet_name', ''),
            event_name=item.get('event_name', ''),
            course=item.get('course', ''),
            time_text=item.get('time_text', ''),
            rank_text=item.get('rank_text', ''),
            meet_date=item.get('meet_date', ''),
            source_url=url,
        )
        count += 1
    update_pb_cache(swimmer_id)
    return jsonify({'ok': True, 'imported_count': count, 'rows': imported})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
