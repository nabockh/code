google.load("visualization", "1", {packages:["corechart"]});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
        var lineChartData = google.visualization.arrayToDataTable(mainChartData.line);

        var lineOptions = {
            legend: 'none',
            colors: ['#8592B2'],
            lineWidth: 3,
            chartArea: { 
                width: "90%", 
                height: "90%" 
            }
        };

    var lineChart = new google.visualization.ScatterChart(document.getElementById('lineChart'))

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}