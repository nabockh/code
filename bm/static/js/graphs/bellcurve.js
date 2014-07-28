google.load("visualization", "1", {packages:["corechart"]});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
        var bellcurveChartData = google.visualization.arrayToDataTable(mainChartData.bell_curve);

        var bellcurveOptions = {
            legend: 'none',
            colors: ['#608a94'],
            lineWidth: 3
        };

    var bellcurveChart = new google.visualization.ScatterChart(document.getElementById('bellcurveChart'))

    // main charts
    bellcurveChart.draw(bellcurveChartData, bellcurveOptions);
}