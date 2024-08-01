document.addEventListener('DOMContentLoaded', function() {
    const debugOutput =  document.getElementById('debug-output');

    function logDebug(message) {
        console.log(message);
        if (debugOutput) {
            debugOutput.textContent += message + '\n';
        }
    }

    logDebug('DOMContentLoaded event fired');
    logDebug('Initializing Grid.js');

    const grid = new gridjs.Grid({
        columns: [
            { 
                id: 'id',
                name: 'ID',
                hidden: true
            },
            { 
                id: 'title', 
                name: 'Title',
                sort: true,
                formatter: (cell, row) => gridjs.html(`<a href="/parsed_content/item/${row.cells[0].data}" class="text-blue-500 hover:underline">${cell}</a>`)
            },
            { 
                id: 'description', 
                name: 'Description', 
                formatter: (cell) => cell && cell.length > 100 ? cell.substring(0, 100) + '...' : cell
            },
            { id: 'pub_date', name: 'Published Date', sort: true },
            {
                id: 'actions',
                name: 'Actions',
                formatter: (_, row) => gridjs.html(`
                    <button class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded text-xs summarize-btn" data-post-id="${row.cells[0].data}">
                        Summarize
                    </button>
                `)
            }
        ],
        server: {
            url: '/parsed_content/list',
            then: data => {
                logDebug(`Received data: ${JSON.stringify(data)}`);
                return data.data;
            },
            total: data => data.total,
            handle: (res) => {
                if (!res.ok) {
                    logDebug(`Error fetching data: ${res.status} ${res.statusText}`);
                    throw Error(res.statusText);
                }
                return res.json();
            },
        },
        pagination: {
            limit: 10,
            server: {
                url: (prev, page, limit) => `${prev}?page=${page}&limit=${limit}`
            }
                    throw Error(res.statusText);
                }
                return res.json();
            }
        },
        search: true,
        sort: true,
        pagination: {
            limit: 10,
            server: {
                url: (prev, page, limit) => `${prev}${prev.includes('?') ? '&' : '?'}page=${page}&limit=${limit}`
            }
        },
        style: {
            table: {
                'font-size': '0.9rem'
            }
        }
    });

    grid.on('load', () => {
        logDebug('Grid loaded');
    });

    grid.on('error', (err) => {
        logDebug(`Grid error: ${err.message}`);
    });

    logDebug('Rendering grid');
    grid.render(document.getElementById("blog-posts-grid"));

    // Add export button
    const exportBtn = document.createElement('button');
    exportBtn.textContent = 'Export to CSV';
    exportBtn.className = 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4';
    exportBtn.addEventListener('click', () => {
        grid.export('csv', {
            filename: 'parsed_content_export'
        });
    });
    document.getElementById("blog-posts-grid").parentNode.insertBefore(exportBtn, document.getElementById("blog-posts-grid").nextSibling);

    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('summarize-btn')) {
            event.preventDefault();
            const postId = event.target.getAttribute('data-post-id');
            summarizeContent(postId);
        }
    });

    function summarizeContent(postId) {
        logDebug(`Summarizing post: ${postId}`);
        const button = document.querySelector(`button[data-post-id="${postId}"]`);
        if (button.disabled) return; // Prevent multiple clicks

        const originalText = button.textContent;
        button.textContent = 'Summarizing...';
        button.disabled = true;

        fetch(summarizeContentUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ content_id: postId })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(err => { throw err; });
            }
            return response.json();
        })
        .then(data => {
            if (data.summary) {
                alert('Content summarized successfully!');
                grid.forceRender();
            } else {
                throw new Error(data.error || 'Failed to summarize content');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            logDebug(`Error summarizing content: ${error.message}`);
            alert('An error occurred while summarizing the content: ' + (error.error || error.message));
        })
        .finally(() => {
            button.textContent = originalText;
            button.disabled = false;
        });
    }

    const clearSummariesBtn = document.getElementById('clear-summaries-btn');
    clearSummariesBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to clear all summaries? This action cannot be undone.')) {
            fetch(clearAllSummariesUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                grid.forceRender();
            })
            .catch(error => {
                console.error('Error:', error);
                logDebug(`Error clearing summaries: ${error.message}`);
                alert('An error occurred while processing your request.');
            });
        }
    });

    function filterContent(filter) {
        logDebug(`Filtering by: ${filter}`);
        // Implement filtering logic here
    }

    document.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', function() {
            filterContent(this.dataset.filter);
        });
    });
});
