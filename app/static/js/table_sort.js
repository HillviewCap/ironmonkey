function initTableSort(tableId) {
    const table = document.getElementById(tableId);
    if (!table) {
        console.error(`Table with id "${tableId}" not found`);
        return;
    }

    const headers = table.querySelectorAll('th.sortable');
    
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            const order = header.classList.contains('asc') ? 'desc' : 'asc';
            
            // Remove sorting classes from all headers
            headers.forEach(h => h.classList.remove('asc', 'desc'));
            
            // Add sorting class to clicked header
            header.classList.add(order);
            
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
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
            tbody.innerHTML = '';
            
            // Append sorted rows
            sortedRows.forEach(row => tbody.appendChild(row));
        });
    });
}
