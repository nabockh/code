function drawLineChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    function lineTooltips(chartData) {
        var votes = chartData[0],
            min = chartData[1],
            max = chartData[3];
        return '<div style="padding:5px 5px 5px 5px;">' + 'Contributors: ' + '<b>' + votes + '%' + '</b>' + '<br/>'+ '<span style="display: block; border-bottom: 1px solid #ccc; padding-top: 5px; margin-bottom: 5px;"></span>' + 'Range: ' + '<b>' + min + ' - ' + max + '</b>' + '</div>';
    };

    for(var i = 0; i < chartData.length; ++i){
        if(i==0){
            chartData[i].push({'type': 'string', 'role': 'tooltip', 'p': {'html': true}});
        }
        else{
            chartData[i].push(lineTooltips(chartData[i]));
        }
    };

    chartData = chartData.filter(function(element, index){
        return index == 0 || element[0] > 0;
    });

    var lineChartData = google.visualization.arrayToDataTable(chartData);

    var lineOptions = {
        width: '100%',
        legend: 'none',
        colors: ['#8592B2'],
        lineWidth: 3,
        orientation: 'vertical',
        chartArea: {
            width: "75%", 
            height: "60%"
        },
        tooltip: { isHtml : true },
        bar: {groupWidth: '2'},
        vAxis: { title : '% of Respondents', titleTextStyle: {color: '#33626e'}, viewWindow: { min: 0, max: 100}, ticks: [{v:0, f: '0'}, {v:25, f: '25%'}, {v:50, f: '50%'}, {v:75, f: '75%'}, {v:100, f: '100%'}]},
        hAxis: { title : 'Value', titleTextStyle: {color: '#33626e'}}
    };

    var lineChart = new google.visualization.CandlestickChart(document.getElementById(divId));

    

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}