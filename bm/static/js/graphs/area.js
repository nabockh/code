function drawAreaChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    var areaChartData = google.visualization.arrayToDataTable(chartData);
            
    var areaOptions = {
        hAxis: {minValue: 0, maxValue: 100},
        legend: {position: 'none'},
        chartArea: {  
            width: "80%", 
            height: "65%" 
        },
        colors:['#608A94'],
    };

    var areaChart = new google.visualization.AreaChart(document.getElementById(divId));

    // main charts
    areaChart.draw(areaChartData, areaOptions);
}