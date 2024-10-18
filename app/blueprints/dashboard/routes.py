from flask import render_template, jsonify, request
from . import dashboard_bp
from app.utils.mongodb_connection import get_mongo_client
from flask import current_app

@dashboard_bp.route('/dashboard')
def dashboard():
    # Render the dashboard template
    return render_template('dashboard.html')

@dashboard_bp.route('/dashboard/api/entity-frequency')
def entity_frequency():
    try:
        # Get the 'label' query parameter if provided
        label = request.args.get('label')

        mongo_client = get_mongo_client()
        db = mongo_client[current_app.config['MONGO_DB_NAME']]
        pipeline = [
            {'$unwind': '$content_tags'},
        ]

        # Filter by label if provided
        if label:
            pipeline.append({'$match': {'content_tags.label': label}})

        pipeline.extend([
            {
                '$group': {
                    '_id': '$content_tags.text',
                    'label': {'$first': '$content_tags.label'},
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ])

        results = db['parsed_content'].aggregate(pipeline)
        data = [{'text': doc['_id'], 'label': doc['label'], 'count': doc['count']} for doc in results]
        mongo_client.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
