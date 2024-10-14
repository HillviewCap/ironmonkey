document.addEventListener('DOMContentLoaded', function() {
    const debugOutput = document.getElementById('debug-output');
    const contentTable = document.getElementById('content-table');
    const paginationContainer = document.getElementById('pagination-container');
    let currentPage = 1;
    const itemsPerPage = 10;

    const dateForm = document.getElementById('date-form');
    const dateInput = document.getElementById('date');
    const selectedDateSpan = document.getElementById('selected-date');
    const contentGrid = document.getElementById('content-grid');
    const noContentMessage = document.getElementById('no-content-message');
    const articlesToday = document.getElementById('articles-today');
    const topSitesList = document.getElementById('top-sites-list');
    const topAuthorsList = document.getElementById('top-authors-list');
    const actorOccurrencesList = document.getElementById('actor-occurrences-list');

    // Function definitions moved outside of conditionals
    function fetchContent(date) {
        const encodedDate = encodeURIComponent(date);
        fetch(`/parsed_content/list?date=${encodedDate}`)
            .then(response => response.json())
            .then(data => {
                updateContent(data.content);
                updateStats(data.stats);
                if (selectedDateSpan) {
                    selectedDateSpan.textContent = date;
                }
            })
            .catch(error => console.error('Error:', error));
    }

    function updateContent(content) {
        if (!contentGrid) return;
        contentGrid.innerHTML = '';
        if (content.length > 0) {
            if (noContentMessage) {
                noContentMessage.style.display = 'none';
            }
            content.forEach(item => {
                const articleElement = document.createElement('a');
                articleElement.href = `/parsed_content/item/${item.id}`;
                articleElement.className = 'block bg-white rounded-lg shadow-md p-6 hover:bg-gray-100';
                articleElement.innerHTML = `
                    <h2 class="text-xl font-semibold mb-2 text-blue-600 hover:underline">
                        ${item.title}
                    </h2>
                    <p class="text-gray-600 mb-4">${item.description ? item.description.substring(0, 150) + '...' : ''}</p>
                    <div class="text-sm text-gray-500 flex justify-between items-center">
                        <span>${new Date(item.pub_date).toLocaleString()}</span>
                        <span class="text-blue-500">${item.rss_feed_title}</span>
                    </div>
                `;
                contentGrid.appendChild(articleElement);
            });
        } else {
            if (noContentMessage) {
                noContentMessage.style.display = 'block';
            }
        }
    }

    function updateStats(stats) {
        if (articlesToday) {
            articlesToday.textContent = stats.articles_today;
        }
        if (topSitesList) {
            topSitesList.innerHTML = stats.top_sites.map(site => `<li>${site[0]}: ${site[1]} articles</li>`).join('');
        }
        if (topAuthorsList) {
            topAuthorsList.innerHTML = stats.top_authors.map(author => `<li>${author[0]}: ${author[1]} articles</li>`).join('');
        }
        if (actorOccurrencesList) {
            if (stats.actor_occurrences.length > 0) {
                actorOccurrencesList.innerHTML = stats.actor_occurrences
                    .map(actor => `<li>${actor.entity_name}: ${actor.occurrence_count} occurrences</li>`)
                    .join('');
            } else {
                actorOccurrencesList.innerHTML = '<li>No APT occurrences for this date.</li>';
            }
        }
    }

    function logDebug(message) {
        console.log(message);
        if (debugOutput) {
            debugOutput.textContent += message + '\n';
        }
    }

    // Event listener for date form submission
    if (dateForm && dateInput) {
        dateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            fetchContent(dateInput.value);
        });
    }

    // Fetch content for the initial date if dateInput exists
    if (dateInput) {
        fetchContent(dateInput.value);
    }

    function updateContent(content) {
        if (contentGrid) {
            contentGrid.innerHTML = '';
            if (content.length > 0) {
                noContentMessage.style.display = 'none';
                content.forEach(item => {
                    const articleElement = document.createElement('a');
                    articleElement.href = `/parsed_content/item/${item.id}`;
                    articleElement.className = 'block bg-white rounded-lg shadow-md p-6 hover:bg-gray-100';
                    articleElement.innerHTML = `
                        <h2 class="text-xl font-semibold mb-2 text-blue-600 hover:underline">
                            ${item.title}
                        </h2>
                        <p class="text-gray-600 mb-4">${item.description ? item.description.substring(0, 150) + '...' : ''}</p>
                        <div class="text-sm text-gray-500 flex justify-between items-center">
                            <span>${new Date(item.pub_date).toLocaleString()}</span>
                            <span class="text-blue-500">${item.rss_feed_title}</span>
                        </div>
                    `;
                    contentGrid.appendChild(articleElement);
                });
            } else {
                noContentMessage.style.display = 'block';
            }
        }
    }

    function updateStats(stats) {
        if (articlesToday) {
            articlesToday.textContent = stats.articles_today;
        }
        if (topSitesList) {
            topSitesList.innerHTML = stats.top_sites.map(site => `<li>${site[0]}: ${site[1]} articles</li>`).join('');
        }
        if (topAuthorsList) {
            topAuthorsList.innerHTML = stats.top_authors.map(author => `<li>${author[0]}: ${author[1]} articles</li>`).join('');
        }
    }

    function logDebug(message) {
        console.log(message);
        if (debugOutput) {
            debugOutput.textContent += message + '\n';
        }
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

        // Add event listener for tagged entities
        document.querySelectorAll('.tagged-entity').forEach(entity => {
            entity.addEventListener('click', (e) => {
                e.preventDefault();
                const entityType = e.target.dataset.entityType;
                const entityId = e.target.dataset.entityId;
                // Here you can add logic to show more information about the entity
                console.log(`Clicked entity: ${entityType} with ID: ${entityId}`);
            });
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

    // Fetch content for the initial date
    fetchContent(dateInput.value);

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
                fetchContent(dateInput.value);
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
                    if (dateInput) {
                        fetchContent(dateInput.value);
                    }
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
