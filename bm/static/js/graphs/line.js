function drawLineChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    function createCustomHTMLContent(chartData) {
        for(var i = 0; i < chartData.length; ++i){
            var votes = chartData[0];
            var min = chartData[1];
            var max = chartData[3];
            return '<div style="padding:5px 5px 5px 5px;">' +
      'Contributors: ' + '<b>' + votes + '</b>' + '<br/>'+ '<span style="display: block; border-bottom: 1px solid #ccc; padding-top: 5px; margin-bottom: 5px;"></span>' + 'Range: ' + '<b>' + min + ' - ' + max + '</b>' + '</div>';
        }
        
    };

    for(var i = 0; i < chartData.length; ++i){
        if(i==0){
            chartData[i].push({'type': 'string', 'role': 'tooltip', 'p': {'html': true}});
        }
        else{
            chartData[i].push(createCustomHTMLContent(chartData[i]));
        }
    }

    var lineChartData = google.visualization.arrayToDataTable(chartData);

    var lineOptions = {
        legend: 'none',
        colors: ['#8592B2'],
        lineWidth: 3,
        orientation: 'vertical',
        chartArea: {
            width: "85%", 
            height: "60%"
        },
        tooltip: { isHtml : true },
        bar: {groupWidth: '2'},
        vAxis: { title : 'Number of Contributors', titleTextStyle: {color: '#33626e'}, textStyle: {fontSize: '1'}, format:'#', gridlines: {count : "-1"}},
        hAxis: { title : 'Values', titleTextStyle: {color: '#33626e'}}
    };

    var lineChart = new google.visualization.CandlestickChart(document.getElementById(divId));

    

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}