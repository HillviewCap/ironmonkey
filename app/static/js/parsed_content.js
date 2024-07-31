document.addEventListener('DOMContentLoaded', function() {
    const grid = new gridjs.Grid({
        columns: [
            { 
                id: 'title', 
                name: 'Title',
                width: '20%',
                resizable: true,
                formatter: (cell, row) => gridjs.html(`<a href="/item/${row.cells[4].data}" class="text-blue-500 hover:underline">${cell}</a>`)
            },
            { 
                id: 'summary', 
                name: 'Summary', 
                width: '40%',
                resizable: true,
                formatter: (cell) => cell && cell.length > 200 ? cell.substring(0, 200) + '...' : cell
            },
            { 
                id: 'url', 
                name: 'URL',
                width: '15%',
                resizable: true,
                formatter: (cell) => {
                    if (!cell) return '';
                    return gridjs.html(`<a href="${cell}" target="_blank" class="text-blue-500 hover:underline" title="${cell}">Source</a>`);
                }
            },
            { 
                id: 'pub_date', 
                name: 'Published Date',
                width: '15%',
                resizable: true,
                formatter: (cell) => gridjs.html(`<span class="text-sm">${cell}</span>`),
                sort: {
                    enabled: true,
                    compare: (a, b) => {
                        const dateA = new Date(a);
                        const dateB = new Date(b);
                        return dateB - dateA;  // Descending order
                    }
                }
            },
            {
                id: 'actions',
                name: 'Actions',
                width: '10%',
                resizable: true,
                formatter: (_, row) => gridjs.html(`
                    <button class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded text-xs summarize-btn" data-post-id="${row.cells[4].data}">
                        Summarize
                    </button>
                `)
            }
        ],
        data: () => {
            return new Promise((resolve, reject) => {
                fetch(parsedContentUrl)
                    .then(response => response.json())
                    .then(data => {
                        if (!data || !data.data || !Array.isArray(data.data)) {
                            console.error('Invalid data structure received:', data);
                            resolve([]);
                            return;
                        }
                        resolve(data.data.map(post => [
                            post.title || '',
                            post.summary || '',
                            post.url || '',
                            post.pub_date || '',
                            post.id || ''
                        ]));
                    })
                    .catch(error => {
                        console.error('Error fetching data:', error);
                        reject(error);
                    });
            });
        },
        search: {
            enabled: true
        },
        sort: true,
        pagination: {
            enabled: true,
            limit: 10
        },
        fixedHeader: true,
        style: {
            table: {
                width: '100%'
            },
            td: {
                'white-space': 'normal',
                'word-wrap': 'break-word'
            }
        },
        language: {
            'search': {
                'placeholder': '🔍 Search...'
            },
            'pagination': {
                'previous': '⬅️',
                'next': '➡️',
                'showing': '👀 Displaying',
                'results': () => 'Records'
            }
        }
    }).render(document.getElementById("parsed-content-table"));

    // Add export button
    const exportBtn = document.createElement('button');
    exportBtn.textContent = 'Export to CSV';
    exportBtn.className = 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mt-4';
    exportBtn.addEventListener('click', () => {
        grid.export('csv', {
            filename: 'parsed_content_export'
        });
    });
    document.getElementById("parsed-content-table").parentNode.insertBefore(exportBtn, document.getElementById("parsed-content-table"));

    document.addEventListener('click', function(event) {
        if (event.target.classList.contains('summarize-btn')) {
            event.stopPropagation();
            const postId = event.target.getAttribute('data-post-id');
            summarizeContent(postId);
        }
    });

    function tagContent(postId) {
        fetch('/tag_content', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ content_id: postId })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            grid.forceRender();
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while tagging the content.');
        });
    }

    function summarizeContent(postId) {
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
                alert('An error occurred while processing your request.');
            });
        }
    });
});
let grid;

function initGrid(data) {
    grid = new gridjs.Grid({
        columns: [
            { id: 'id', name: 'ID', hidden: true },
            { id: 'title', name: 'Title' },
            { id: 'description', name: 'Description' },
            { id: 'pub_date', name: 'Date' },
            {
                name: 'Actions',
                formatter: (_, row) => gridjs.html(`<a href="/parsed_content/item/${row.cells[0].data}" class="btn btn-sm btn-primary">View</a>`)
            }
        ],
        data: data,
        search: true,
        sort: true,
        pagination: {
            limit: 10
        },
        style: {
            table: {
                'font-size': '0.9rem'
            }
        }
    }).render(document.getElementById("blog-posts-grid"));
}

function filterContent(filter) {
    // Implement filtering logic here
    console.log(`Filtering by: ${filter}`);
    // You would typically make an AJAX call here to get filtered data
    // For now, we'll just log the filter
}

document.addEventListener('DOMContentLoaded', function() {
    fetch('/parsed_content/get_parsed_content')
        .then(response => response.json())
        .then(data => {
            initGrid(data.data);
        });

    document.getElementById('search-input').addEventListener('input', function(e) {
        grid.search(e.target.value);
    });

    document.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', function() {
            filterContent(this.dataset.filter);
        });
    });
});
