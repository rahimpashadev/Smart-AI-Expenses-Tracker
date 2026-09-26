// Wrap everything inside DOMContentLoaded to ensure the canvas exists
document.addEventListener("DOMContentLoaded", function() {
    // Initial expense data
    const expenseData = {
        Food: [12000, 11000, 13000, 12500, 14000, 13500, 12500],
        Transport: [7000, 8500, 9000, 9500, 8800, 9000, 9000],
        Rent: [30000, 30000, 32000, 35000, 35000, 35000, 35000]
    };

    const ctx = document.getElementById('expenseTrend').getContext('2d');

    // Create Chart.js line chart
    window.expenseTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
            datasets: [
                { label: 'Food', data: [...expenseData.Food], borderColor: 'rgba(34,197,94,1)', backgroundColor: 'rgba(34,197,94,0.2)', tension: 0.4 },
                { label: 'Transport', data: [...expenseData.Transport], borderColor: 'rgba(239,68,68,1)', backgroundColor: 'rgba(239,68,68,0.2)', tension: 0.4 },
                { label: 'Rent', data: [...expenseData.Rent], borderColor: 'rgba(59,130,246,1)', backgroundColor: 'rgba(59,130,246,0.2)', tension: 0.4 }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { position: 'top' }
            },
            scales: { y: { beginAtZero: false } }
        }
    });

    // Function to add expense dynamically
    window.addExpenseToChart = function(category, amount) {
        const lastIndex = expenseData[category].length - 1;
        expenseData[category][lastIndex] += parseInt(amount);
        window.expenseTrend.data.datasets.forEach(ds => {
            if(ds.label === category) ds.data = [...expenseData[category]];
        });
        window.expenseTrend.update();
    }
});
<script src="js_main.js"></script>

