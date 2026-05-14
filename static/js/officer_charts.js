// Store chart instances for later updates
let yieldChart = null;
let healthChart = null;

// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', function() {
    createYieldChart('all');
    createHealthChart();
});

// Create/Update Yield Chart
function createYieldChart(cropFilter = 'all') {
    let filteredCropNames = cropNames;
    let filteredCropYields = cropYields;
    
    // Filter data if specific crop selected
    if (cropFilter !== 'all') {
        const index = cropNames.indexOf(cropFilter);
        if (index !== -1) {
            filteredCropNames = [cropNames[index]];
            filteredCropYields = [cropYields[index]];
        }
    }
    
    const trace = {
        x: filteredCropNames,
        y: filteredCropYields,
        type: "bar",
        marker: {
            color: '#4CAF50',
            line: {
                color: 'white',
                width: 1
            }
        },
        text: filteredCropYields.map(y => y + ' kg'),
        textposition: 'outside',
        hoverinfo: 'x+y'
    };
    
    const layout = {
        title: cropFilter === 'all' ? "Total Yield per Crop" : `Yield: ${cropFilter}`,
        xaxis: { 
            title: "Crop",
            tickangle: -45
        },
        yaxis: { 
            title: "Yield (kg)",
            gridcolor: '#e9ecef'
        },
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { b: 80, t: 50, r: 20, l: 50 },
        showlegend: false,
        font: { family: 'Arial, sans-serif', size: 12 }
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    // Destroy old chart if exists
    if (yieldChart) {
        Plotly.purge('yieldChart');
    }
    
    // Create new chart
    yieldChart = Plotly.newPlot('yieldChart', [trace], layout, config);
}

// Create Health Pie Chart
function createHealthChart() {
    // Check if data exists
    if (!healthLabels || !healthCounts || healthLabels.length === 0) {
        document.getElementById('healthChart').innerHTML = '<p class="no-data">No health data available</p>';
        return;
    }
    
    const colors = {
        'Healthy': '#28a745',
        'Fair': '#ffc107',
        'Poor': '#dc3545'
    };
    
    const trace = {
        labels: healthLabels,
        values: healthCounts,
        type: "pie",
        marker: {
            colors: healthLabels.map(label => colors[label] || '#6c757d')
        },
        textinfo: 'label+percent',
        hoverinfo: 'label+value+percent',
        textposition: 'inside',
        insidetextorientation: 'radial'
    };
    
    const layout = {
        title: "Crop Health Status",
        showlegend: false,
        plot_bgcolor: 'white',
        paper_bgcolor: 'white',
        margin: { t: 50, b: 20, l: 20, r: 20 },
        font: { family: 'Arial, sans-serif', size: 12 }
    };
    
    const config = {
        responsive: true,
        displayModeBar: false
    };
    
    Plotly.newPlot('healthChart', [trace], layout, config);
}

// Function to filter yield data by crop (called from dropdown)
function filterYieldData(cropName) {
    createYieldChart(cropName);
    
    // Also filter the table if it exists
    const rows = document.querySelectorAll('.crop-row');
    let visibleCount = 0;
    
    rows.forEach(row => {
        if (cropName === 'all' || row.dataset.crop === cropName) {
            row.style.display = '';
            visibleCount++;
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update count display if element exists
    const cropCountEl = document.getElementById('cropCount');
    if (cropCountEl) {
        cropCountEl.textContent = visibleCount + ' crop' + (visibleCount !== 1 ? 's' : '');
    }
}

// Export table to CSV
function exportToCSV() {
    const table = document.getElementById('yieldTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const csv = [];
    
    // Get headers
    const headers = [];
    table.querySelectorAll('thead th').forEach(th => {
        headers.push(th.textContent);
    });
    csv.push(headers.join(','));
    
    // Get data rows (only visible ones)
    document.querySelectorAll('.crop-row:not([style*="display: none"])').forEach(row => {
        const rowData = [];
        row.querySelectorAll('td').forEach(td => {
            // Clean up the text (remove emojis, extra spaces)
            let text = td.textContent.trim();
            // Remove emojis for CSV
            text = text.replace(/[🌽🌾🫘🌱▲▼●]/g, '').trim();
            rowData.push(text);
        });
        csv.push(rowData.join(','));
    });
    
    // Download CSV
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `yield_data_${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
}