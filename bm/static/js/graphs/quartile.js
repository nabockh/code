function drawQuartileChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    var quartileChartData = google.visualization.arrayToDataTable(chartData);
            
    var quartileOptions = {
        legend: {position: 'none'},
        chartArea: {  
            width: "80%", 
            height: "65%" 
        },
        colors: ['#8592B2'],
        bar: {groupWidth: 6}
    };

    var quartileChart = new google.visualization.QuartileChart(document.getElementById(divId));

    // main charts
    quartileChart.draw(quartileChartData, quartileOptions);
}