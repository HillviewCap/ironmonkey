# RSS Feed Management Plan

## New Routes to Create

1. `/rss/feeds` (GET): List all RSS feeds
2. `/rss/feed/<uuid:feed_id>` (GET): Get details of a specific RSS feed
3. `/rss/feed` (POST): Create a new RSS feed
4. `/rss/feed/<uuid:feed_id>` (PUT): Update an existing RSS feed
5. `/rss/feed/<uuid:feed_id>` (DELETE): Delete an RSS feed
6. `/rss/parse/<uuid:feed_id>` (POST): Manually trigger parsing for a specific feed

## New Services to Create

1. `RSSFeedService`:
   - `get_all_feeds()`
   - `get_feed_by_id(feed_id: uuid.UUID)`
   - `create_feed(feed_data: dict)`
   - `update_feed(feed_id: uuid.UUID, feed_data: dict)`
   - `delete_feed(feed_id: uuid.UUID)`
   - `parse_feed(feed_id: uuid.UUID)`

2. `ParsedContentService`:
   - `get_parsed_content(filters: dict, page: int, per_page: int)`
   - `get_content_by_id(content_id: uuid.UUID)`
   - `create_parsed_content(content_data: dict)`
   - `update_parsed_content(content_id: uuid.UUID, content_data: dict)`
   - `delete_parsed_content(content_id: uuid.UUID)`

## New Utils to Create

1. `rss_validator.py`:
   - `validate_rss_url(url: str) -> bool`
   - `extract_feed_info(url: str) -> dict`

2. `content_sanitizer.py`:
   - `sanitize_html_content(html: str) -> str`

## Changes to Existing Code

1. Refactor the existing route handlers in rss_manager.py to use the new services.
2. Move the feed parsing logic from rss_manager.py to the RSSFeedService.
3. Update the ParsedContent model to include any missing fields that might be useful.
4. Implement proper error handling and logging in all new and refactored code.
5. Ensure all new code follows the project's conventions and uses type hints.

## Next Steps

1. Implement the new services in separate files under the `app/services/` directory.
2. Create the new utility functions in separate files under the `app/utils/` directory.
3. Update the rss_manager.py file to use the new services and implement the new routes.
4. Write unit tests for all new services and utility functions.
5. Update existing tests to accommodate the refactored code.
6. Document all new functions, methods, and routes using docstrings.
