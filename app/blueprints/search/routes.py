from flask import Blueprint, render_template, request, current_app, jsonify, abort
from flask_wtf import FlaskForm
from flask_login import login_required
from app.models import SearchParams
from app.models.relational.parsed_content import ParsedContent

search_bp = Blueprint('search', __name__)
from app.utils.search_utils import get_search_params, perform_search, build_search_query
from app.services.summary_service import SummaryService
import uuid

@search_bp.route("/search", methods=["GET", "POST"])
def search():
    """
    Handle search requests and render search results.

    This function processes both GET and POST requests for searching.
    It initializes search parameters, performs the search, and renders
    the results.

    Returns:
        str: Rendered HTML template with search results or search form.

    Note:
        - For GET requests, it populates search parameters from URL query parameters.
        - For POST requests, it uses form data to set search parameters.
        - Pagination is supported through the 'page' parameter.
    """
    form = FlaskForm()
    search_params = SearchParams(query="")  # Initialize with an empty query

    if request.method == "GET":
        # Populate search_params from GET parameters
        search_params.query = request.args.get("query", "")
        search_params.start_date = request.args.get("start_date")
        search_params.end_date = request.args.get("end_date")
        search_params.source_types = request.args.getlist("source_types")
        search_params.keywords = (
            request.args.get("keywords", "").split(",")
            if request.args.get("keywords")
            else []
        )
    elif form.validate_on_submit():
        search_params = get_search_params(form)

    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit() or request.method == "GET":
        current_app.logger.info(f"Performing search with params: {search_params.__dict__}")
        results, total_results = perform_search(search_params, page, per_page=10, order_by=ParsedContent.pub_date.desc())
        current_app.logger.info(f"Search completed. Total results: {total_results}")
        return render_template(
            "search.html",
            form=form,
            search_params=search_params,
            results=results,
            total_results=total_results,
            page=page
        )

    return render_template("search.html", form=form, search_params=search_params)

@search_bp.route("/view/<uuid:item_id>")
def view_item(item_id):
    """
    Render a view for a specific parsed content item.

    Args:
        item_id (uuid.UUID): The UUID of the parsed content item to view.

    Returns:
        str: Rendered HTML template for the specific item.

    Raises:
        404: If the item with the given ID is not found.
    """
    item = ParsedContent.query.get_or_404(item_id)
    return render_template("view_item.html", item=item)

@search_bp.route("/summarize_content", methods=["POST"])
@login_required
async def summarize_content():
    """
    Generate or enhance a summary for a specific parsed content item.

    This asynchronous function takes a content_id from the JSON request,
    uses the SummaryService to generate or enhance the summary, and returns
    the result.

    Returns:
        flask.Response: JSON response containing the summary or an error message.

    Raises:
        400: If content_id is missing or invalid.
        500: If there's an error during summary generation.

    Note:
        This route requires authentication (login_required).
    """
    content_id = request.json.get("content_id")
    if not content_id:
        current_app.logger.error("content_id is missing in the request")
        return jsonify({"error": "content_id is required"}), 400

    try:
        content_id = uuid.UUID(content_id)
        summary_service = SummaryService()
        success = await summary_service.enhance_summary(str(content_id))
        
        if success:
            document = ParsedContent.query.get(content_id)
            current_app.logger.info(
                f"Summary generated successfully for document id: {content_id}"
            )
            return jsonify({"summary": document.summary}), 200
        else:
            current_app.logger.error(f"Failed to generate summary for document id: {content_id}")
            return jsonify({"error": "Failed to generate summary"}), 500
    except ValueError:
        current_app.logger.error(
            f"Invalid UUID format for content_id: {content_id}"
        )
        return jsonify({"error": "Invalid content_id format"}), 400
    except Exception as e:
        current_app.logger.exception(f"Error summarizing content: {str(e)}")
        return jsonify({"error": f"Error summarizing content: {str(e)}"}), 500

@search_bp.route("/clear_all_summaries", methods=["POST"])
@login_required
def clear_all_summaries():
    """
    Clear all summaries from the ParsedContent table.

    This function sets the summary field to None for all entries in the
    ParsedContent table.

    Returns:
        flask.Response: JSON response indicating success or failure.

    Raises:
        500: If there's an error during the clearing process.

    Note:
        This route requires authentication (login_required).
    """
    try:
        ParsedContent.query.update({ParsedContent.summary: None})
        current_app.db.session.commit()
        return jsonify({"message": "All summaries have been cleared"}), 200
    except Exception as e:
        current_app.db.session.rollback()
        current_app.logger.error(f"Error clearing summaries: {str(e)}")
        return jsonify({"error": "An error occurred while clearing summaries"}), 500
