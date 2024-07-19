from flask import render_template, request, current_app
from flask_wtf import FlaskForm
from app.models import SearchParams, ParsedContent
from app.blueprints.search import bp
from app.utils.search_utils import get_search_params, perform_search

@bp.route("/search", methods=["GET", "POST"])
def search():
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
        results, total_results = perform_search(search_params, page)
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

@bp.route("/view/<uuid:item_id>")
def view_item(item_id):
    item = ParsedContent.query.get_or_404(item_id)
    return render_template("view_item.html", item=item)
