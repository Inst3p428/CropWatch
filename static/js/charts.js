// --------------------
// Rainfall chart
// --------------------
Plotly.newPlot("rainfallChart", [{
    x: rainfallDates,
    y: rainfallValues,
    type: "scatter",
    mode: "lines+markers",
    name: "Rainfall (mm)"
}], {
    title: "Daily Rainfall",
    xaxis: { title: "Date" },
    yaxis: { title: "Rainfall (mm)" }
});


// --------------------
// Soil moisture chart
// --------------------
Plotly.newPlot("soilChart", [{
    x: soilDates,
    y: soilValues,
    type: "scatter",
    mode: "lines+markers",
    name: "Soil Moisture (%)"
}], {
    title: "Soil Moisture Levels",
    xaxis: { title: "Date" },
    yaxis: { title: "Moisture (%)" }
});


// --------------------
// Yield chart
// --------------------
if (typeof cropNames !== "undefined" && cropNames.length > 0) {
    Plotly.newPlot("yieldChart", [{
        x: cropNames,
        y: cropYields,
        type: "bar",
        name: "Yield (kg)"
    }], {
        title: "Total Yield per Crop",
        xaxis: { title: "Crop" },
        yaxis: { title: "Yield (kg)" }
    });
}

// --------------------
// Crop health summary (FIXED)
// --------------------
const healthCounts = healthLabels.reduce((acc, status) => {
    acc[status] = (acc[status] || 0) + 1;
    return acc;
}, {});

Plotly.newPlot("healthChart", [{
    labels: Object.keys(healthCounts),
    values: Object.values(healthCounts),
    type: "pie"
}], {
    title: "Crop Health Status Distribution"
});

Plotly.newPlot("rainfallChart", [{
    x: rainfallDates,
    y: rainfallValues,
    type: "scatter",
    mode: "lines+markers",
    name: "Rainfall (mm)",
    line: { color: 'blue', width: 2 },
    marker: { color: 'darkblue', size: 8 }
}], {
    title: " Daily Rainfall",
    xaxis: { title: "Date", tickangle: -45 },
    yaxis: { title: "Rainfall (mm)", range: [0, 100] },
    plot_bgcolor: '#f8f9fa',
    paper_bgcolor: 'white'
});

// Add a horizontal line showing optimal rainfall
// Add hover text showing "Dry day" or "Heavy rain"
