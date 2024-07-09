document.addEventListener('DOMContentLoaded', function() {
    const table = document.getElementById('parsedContentTable');
    const headers = table.querySelectorAll('th.sortable');
    
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            const order = header.classList.contains('asc') ? 'desc' : 'asc';
            
            // Remove sorting classes from all headers
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            
            // Add sorting class to clicked header
            header.classList.add(order);
            
            const rows = Array.from(table.querySelectorAll('tbody tr'));
            const sortedRows = rows.sort((a, b) => {
                const aValue = a.querySelector(`td:nth-child(${Array.from(headers).indexOf(header) + 1})`).textContent.trim();
                const bValue = b.querySelector(`td:nth-child(${Array.from(headers).indexOf(header) + 1})`).textContent.trim();
                
                if (column === 'date') {
                    return order === 'asc' ? new Date(aValue) - new Date(bValue) : new Date(bValue) - new Date(aValue);
                } else {
                    return order === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
                }
            });
            
            // Clear the table body
            table.querySelector('tbody').innerHTML = '';
            
            // Append sorted rows
            sortedRows.forEach(row => table.querySelector('tbody').appendChild(row));
        });
    });
});
