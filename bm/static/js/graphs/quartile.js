function drawQuartileChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    function quartileTooltips(chartData) {
        var votes = chartData[0]['f'],
            min = chartData[1],
            avg = chartData[3],
            max = chartData[4];
        return '<div style="padding:5px 5px 5px 5px;">' + '<b>' + votes + '</b>' + '<br/>'+ '<span style="display: block; border-bottom: 1px solid #ccc; padding-top: 5px; margin-bottom: 5px;"></span>' + 'Range: ' + '<b>' + min + ' - ' + max + '</b>' + '<br/>'+ 'Avarage: ' + '<b>' + avg + '</b>' + '</div>';
    };

    for(var i = 0; i < chartData.length; ++i){
        if(i==0){
            chartData[i].push({'type': 'string', 'role': 'tooltip', 'p': {'html': true}});
        }
        else{
            chartData[i].push(quartileTooltips(chartData[i]));
        }
    };

    var quartileChartData = google.visualization.arrayToDataTable(chartData);
            
    var quartileOptions = {
        legend: {position: 'none'},
        chartArea: {  
            width: "80%", 
            height: "65%" 
        },
        colors: ['#8592B2'],
        bar: {groupWidth: 6},
        tooltip: { isHtml : true },
        hAxis: { title : 'of Respondents', baselineColor: '#fff', gridlines: {color: '#fff'}, textStyle: { fontSize: 10, bold: true}, viewWindow: { min: 0, max: 5}, ticks: [{v:0, f: ''}, {v:1, f: '1st Quartile'}, {v:2, f: '2nd Quartile'}, {v:3, f: '3rd Quartile'}, {v:4, f: '4th Quartile'}]},
        vAxis: { title : 'Values', textStyle: { fontSize: 10}},
    };

    var quartileChart = new google.visualization.CandlestickChart(document.getElementById(divId));

    // main charts
    quartileChart.draw(quartileChartData, quartileOptions);
}