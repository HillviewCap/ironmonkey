from flask import render_template, jsonify, request
from . import dashboard_bp
from app.utils.mongodb_connection import get_mongo_client
from flask import current_app

@dashboard_bp.route('/')
def dashboard():
    # Render the dashboard template
    return render_template('dashboard.html')

@dashboard_bp.route('/api/entity-frequency')
def entity_frequency():
    mongo_client = None
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
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error in entity_frequency: {str(e)}")
        return jsonify({'error': 'An error occurred while fetching data'}), 500
    finally:
        if mongo_client:
            mongo_client.close()
