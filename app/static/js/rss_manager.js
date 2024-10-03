let grid;

async function addFeed(event) {
    event.preventDefault();
    const form = document.getElementById('add-single-feed-form');
    const submitButton = form.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.textContent;
    
    submitButton.disabled = true;
    submitButton.textContent = 'Processing...';
    
    const formData = new FormData(form);
    const gridElement = document.getElementById("awesome-blogs-grid");
    const createFeedUrl = gridElement.getAttribute('data-create-feed-url');

    const addToRssFeedsUrl = gridElement.getAttribute('data-add-to-rss-feeds-url');
    try {
        const response = await fetch('/rss_manager/create_rss_feed', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('input[name="csrf_token"]').value
            },
            body: JSON.stringify(Object.fromEntries(formData))
        });
        const result = await response.json();
        if (response.ok) {
            showNotification('Feed added successfully', 'success');
            form.reset();
            refreshExistingFeedsTable();
            if (grid) {
                grid.forceRender();
            }
        } else {
            showNotification('Error adding feed: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('An error occurred while adding the feed', 'error');
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
    }
}

function refreshExistingFeedsTable() {
    const getRssFeedsUrl = gridElement.getAttribute('data-get-rss-feeds-url');
    fetch(getRssFeedsUrl)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newTable = doc.querySelector('.min-w-full');
            const oldTable = document.querySelector('.min-w-full');
            oldTable.parentNode.replaceChild(newTable, oldTable);
        })
        .catch(error => console.error('Error refreshing feeds table:', error));
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.className = `fixed top-4 right-4 p-4 rounded-md ${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white`;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function initializeAwesomeBlogsGrid() {
    const gridElement = document.getElementById("awesome-blogs-grid");
    const getBlogsUrl = gridElement.getAttribute('data-get-blogs-url');

    grid = new gridjs.Grid({
        columns: [
            { id: 'blog', name: 'Blog' },
            { id: 'blog_category', name: 'Category' },
            { id: 'type', name: 'Type' },
            { 
                id: 'blog_link', 
                name: 'Blog Link',
                formatter: (cell) => gridjs.html(`<a href="${cell}" target="_blank" rel="noopener" class="text-blue-500 hover:text-blue-700">Blog Link</a>`)
            },
            { 
                id: 'feed_link', 
                name: 'Feed Link',
                formatter: (cell) => cell ? gridjs.html(`<a href="${cell}" target="_blank" rel="noopener" class="text-blue-500 hover:text-blue-700">Feed Link</a>`) : 'No RSS feed available'
            },
            {
                id: 'actions',
                name: 'Actions',
                formatter: (_, row) => {
                    const isInRssFeeds = row.cells[5].data;
                    if (isInRssFeeds) {
                        return gridjs.html('<p class="text-sm text-green-500 font-bold">Already in RSS Feeds</p>');
                    } else {
                        return gridjs.html(`<button onclick="addToRssFeeds('${row.cells[0].data}')" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-1 px-2 rounded text-sm">Add to RSS Feeds</button>`);
                    }
                }
            }
        ],
        server: {
            url: getBlogsUrl,
            then: response => response.map(blog => [
                blog.blog,
                blog.blog_category,
                blog.type,
                blog.blog_link,
                blog.feed_link,
                blog.is_in_rss_feeds
            ])
        },
        search: true,
        sort: true,
        pagination: true,
        className: {
            table: 'min-w-full bg-white'
        }
    }).render(document.getElementById("awesome-blogs-grid"));
}

async function addToRssFeeds(blogName) {
    const gridElement = document.getElementById("awesome-blogs-grid");
    const addToRssFeedsUrl = gridElement.getAttribute('data-add-to-rss-feeds-url');

    try {
        const response = await fetch(addToRssFeedsUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.getElementById('csrf_token').value
            },
            body: JSON.stringify({ blog: blogName })
        });
        const result = await response.json();
        if (response.ok) {
            showNotification('Blog added to RSS feeds successfully', 'success');
            grid.forceRender();
            refreshExistingFeedsTable();
        } else {
            showNotification('Error adding blog to RSS feeds: ' + result.error, 'error');
        }
    } catch (error) {
        console.error('Error in addToRssFeeds:', error);
        showNotification('An error occurred while adding the blog to RSS feeds', 'error');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    initializeAwesomeBlogsGrid();
});
