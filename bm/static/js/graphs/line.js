function drawLineChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    var lineChartData = google.visualization.arrayToDataTable(chartData);

    var lineOptions = {
        legend: 'top',
        colors: ['#8592B2'],
        lineWidth: 3,
        orientation: 'vertical',
        chartArea: { 
            width: "90%", 
            height: "80%" 
        },
        vAxis: { title : 'Count of Votes', textStyle: {fontSize : '1', color: '#FFFFFF'}}
    };

    var lineChart = new google.visualization.CandlestickChart(document.getElementById(divId));

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}