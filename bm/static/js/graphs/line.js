function drawLineChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    // function createCustomHTMLContent(ChartData) {
    //     for(var i = 0; i < chartData.length; ++i){
    //         var votes = chartData;
    //         return 'Votes: ' + votes
    //     }
        
    // };

    // for(var i = 0; i < chartData.length; ++i){
    //     if(i==0){
    //         chartData[i].push({type: 'string', role: 'tooltip'});
    //     }
    //     else{
    //         chartData[i].push(createCustomHTMLContent());
    //     }
    // }

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
        // tooltip: { isHtml : true },
        bar: {groupWidth: '2'},
        vAxis: { title : 'Number of Contributors', titleTextStyle: {color: '#33626e'}, textStyle: {fontSize: '1'}, format:'#', gridlines: {count : "-1"}},
        hAxis: { title : 'Values', titleTextStyle: {color: '#33626e'}}
    };

    var lineChart = new google.visualization.CandlestickChart(document.getElementById(divId));

    

    // main charts
    lineChart.draw(lineChartData, lineOptions);
}