document.addEventListener('DOMContentLoaded', function() {
    const debugOutput = document.getElementById('debug-output');
    const contentTable = document.getElementById('content-table');
    const paginationContainer = document.getElementById('pagination-container');
    let currentPage = 1;
    const itemsPerPage = 10;

    function logDebug(message) {
        console.log(message);
        if (debugOutput) {
            debugOutput.textContent += message + '\n';
        }
    }

    function fetchContent(page) {
        logDebug(`Fetching content for page ${page}`);
        fetch(`/parsed_content/list?page=${page}&limit=${itemsPerPage}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                renderTable(data.data);
                renderPagination(data.total, page);
            })
            .catch(error => {
                logDebug(`Error fetching content: ${error.message}`);
                console.error('Error:', error);
                alert('An error occurred while fetching content. Please try again later.');
            });
    }

    function renderTable(data) {
        const tbody = contentTable.querySelector('tbody');
        tbody.innerHTML = '';
        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><a href="/parsed_content/item/${item.id}" class="text-blue-500 hover:underline">${item.title}</a></td>
                <td>${item.description ? (item.description.length > 100 ? item.description.substring(0, 100) + '...' : item.description) : ''}</td>
                <td>${item.pub_date}</td>
                <td>
                    <button class="bg-green-500 hover:bg-green-700 text-white font-bold py-1 px-2 rounded text-xs summarize-btn" data-post-id="${item.id}">
                        Summarize
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    function renderPagination(total, currentPage) {
        const totalPages = Math.ceil(total / itemsPerPage);
        paginationContainer.innerHTML = '';
        for (let i = 1; i <= totalPages; i++) {
            const button = document.createElement('button');
            button.textContent = i;
            button.className = `px-3 py-1 mx-1 ${i === currentPage ? 'bg-blue-500 text-white' : 'bg-gray-200'}`;
            button.addEventListener('click', () => fetchContent(i));
            paginationContainer.appendChild(button);
        }
    }

    fetchContent(currentPage);

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
        if (button.disabled) return;

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
                fetchContent(currentPage);
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
    if (clearSummariesBtn) {
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
                    fetchContent(currentPage);
                })
                .catch(error => {
                    console.error('Error:', error);
                    logDebug(`Error clearing summaries: ${error.message}`);
                    alert('An error occurred while processing your request.');
                });
            }
        });
    }
});
