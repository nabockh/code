
function drawBellcurveChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    var bellcurveChartData = google.visualization.arrayToDataTable(chartData);

    var bellcurveOptions = {
        legend: 'none',
        colors: ['#608a94'],
        lineWidth: 3
    };

    var bellcurveChart = new google.visualization.ScatterChart(document.getElementById(divId))

    // main charts
    bellcurveChart.draw(bellcurveChartData, bellcurveOptions);
};