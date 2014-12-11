function drawAreaChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    };

    var areaChartData = google.visualization.arrayToDataTable(chartData);
    

    if( screen.width < 641 ) {
        var areaOptions = {
            legend: {position: 'bottom'},
            chartArea: {
                top: 25,
                left: 60,
                width: '70%'
            },
            colors:['#608A94'],
            hAxis: {title : '% of Respondents', minValue: 0, maxValue: 100},
            vAxis: {title : 'Values' },
            pointSize: 5
        }

    } else {
        var areaOptions = {
            hAxis: {title : '% of Respondents', minValue: 0, maxValue: 100},
            vAxis: {title : 'Values' },
            legend: {position: 'none'},
            chartArea: {  
                width: "80%", 
                height: "65%" 
            },
            colors:['#608A94'],
            pointSize: 3
        };
    };
    

    var areaChart = new google.visualization.AreaChart(document.getElementById(divId));

    // main charts
    areaChart.draw(areaChartData, areaOptions);
}