function drawLineChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    var lineChartData = google.visualization.arrayToDataTable(chartData);

    var lineOptions = {
        legend: 'none',
        colors: ['#8592B2'],
        lineWidth: 3,
        chartArea: { 
            width: "90%", 
            height: "80%" 
        }
    };

    var lineChart = new google.visualization.ScatterChart(document.getElementById(divId))

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}