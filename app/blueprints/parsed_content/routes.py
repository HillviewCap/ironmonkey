from flask import Blueprint, render_template, abort, request, redirect, url_for, jsonify, Response
import csv
from app.models.relational.parsed_content import ParsedContent
from app.services.parsed_content_service import ParsedContentService
from app.services.summary_service import SummaryService
from uuid import UUID

parsed_content_bp = Blueprint('parsed_content', __name__)
summary_service = SummaryService()

@parsed_content_bp.route('/', methods=['GET'])
def parsed_content_list():
    # Fetch the most recent blog posts
    recent_posts, _ = ParsedContentService.get_contents(page=0, limit=10, search_query='')
    return render_template('parsed_content.html', recent_posts=recent_posts)

@parsed_content_bp.route('/item/<uuid:content_id>', methods=['GET'])
def view_content(content_id):
    content = ParsedContentService.get_content_by_id(content_id)
    if not content:
        abort(404)
    return render_template('view_item.html', item=content)

@parsed_content_bp.route('/list', methods=['GET'])
def list_content():
    page = request.args.get('page', 1, type=int) - 1  # Grid.js uses 1-based indexing
    limit = request.args.get('limit', 10, type=int)
    search_query = request.args.get('search', '')
    feed_id = request.args.get('feed_id')
    
    contents, total = ParsedContentService.get_contents(page=page, limit=limit, search_query=search_query, feed_id=feed_id)
    
    return jsonify({
        'data': [content.to_dict() for content in contents],
        'total': total,
        'page': page + 1,  # Return 1-based page number
        'limit': limit
    })

@parsed_content_bp.route('/export_csv', methods=['GET'])
def export_csv():
    search = request.args.get('search', '')
    feed_id = request.args.get('feed_id')
    
    # Convert feed_id to UUID if it's provided
    if feed_id:
        try:
            feed_id = UUID(feed_id)
        except ValueError:
            return jsonify({'error': 'Invalid feed_id'}), 400

    # Fetch data from your database
    items, _ = ParsedContentService.get_contents(
        page=0,  # Fetch all items
        limit=0,  # No limit
        search_query=search,
        feed_id=feed_id
    )

    # Create a CSV response
    def generate():
        data = [content.to_dict() for content in items]
        fieldnames = data[0].keys() if data else []
        writer = csv.DictWriter(Response(), fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
        yield writer

    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=parsed_content.csv"})

@parsed_content_bp.route('/get_parsed_content')
def get_parsed_content():
    search = request.args.get('search', '')
    feed_id = request.args.get('feed_id')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    # Convert feed_id to UUID if it's provided
    if feed_id:
        try:
            feed_id = UUID(feed_id)
        except ValueError:
            return jsonify({'error': 'Invalid feed_id'}), 400

    # Fetch data from your database
    items, total = ParsedContentService.get_contents(
        page=page,  # Keep as 1-based index
        limit=limit,
        search_query=search,
        feed_id=feed_id
    )

    # Format the data for Grid.js
    formatted_data = [
        [
            str(item.id),
            item.title,
            item.description[:100] + '...' if len(item.description) > 100 else item.description,
            item.pub_date.split(' ')[0] if item.pub_date else ''
        ]
        for item in items
    ]

    return jsonify({
        'data': formatted_data,
        'total': total
    })

@parsed_content_bp.route('/summarize_content', methods=['POST'])
def summarize_content():
    content_id = request.json.get('content_id')
    if not content_id:
        return jsonify({'error': 'No content_id provided'}), 400

    try:
        summary = summary_service.generate_summary(content_id)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parsed_content_bp.route('/clear_all_summaries', methods=['POST'])
def clear_all_summaries():
    try:
        ParsedContentService.clear_all_summaries()
        return jsonify({'message': 'All summaries cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
