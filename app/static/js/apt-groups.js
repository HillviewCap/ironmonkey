document.addEventListener('DOMContentLoaded', function() {
    const categoryChart = document.getElementById('category-chart');
    const tlpChart = document.getElementById('tlp-chart');

    // Sample data for charts (you would replace this with real data from your backend)
    const categoryData = {
        labels: ['State-sponsored', 'Cybercrime', 'Hacktivism', 'Other'],
        datasets: [{
            data: [40, 30, 20, 10],
            backgroundColor: ['#4299E1', '#48BB78', '#ED8936', '#A0AEC0']
        }]
    };

    const tlpData = {
        labels: ['RED', 'AMBER', 'GREEN', 'WHITE'],
        datasets: [{
            data: [10, 30, 40, 20],
            backgroundColor: ['#F56565', '#ED8936', '#48BB78', '#A0AEC0']
        }]
    };

    // Create charts
    new Chart(categoryChart, {
        type: 'pie',
        data: categoryData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'APT Groups by Category'
                }
            }
        }
    });

    new Chart(tlpChart, {
        type: 'pie',
        data: tlpData,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'APT Groups by TLP'
                }
            }
        }
    });
});
