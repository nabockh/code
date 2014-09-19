function drawLineChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    if(chartData.length > 1){
        for(var i = 1; i < chartData.length; ++i){
            for(var j = 1; j < chartData[i].length; ++j){
                chartData[i][j] = {"v": chartData[i][j], "f": null};
            }
        }
    }
    var lineChartData = google.visualization.arrayToDataTable(chartData);

    var lineOptions = {
        legend: 'top',
        colors: ['#8592B2'],
        lineWidth: 3,
        orientation: 'vertical',
        chartArea: {
            width: "85%", 
            height: "60%"
        },
        bar: {groupWidth: '2'},
        vAxis: { title : 'Number of Contributors', format:'#', titleTextStyle: {color: '#33626e'}},
        hAxis: { title : 'Values', titleTextStyle: {color: '#33626e'}}
    };

    var lineChart = new google.visualization.CandlestickChart(document.getElementById(divId));

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}