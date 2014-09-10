function columnGradient(slices){
    var startColor = { r : 32, g : 44, b : 69};
    var endColor = { r : 96, g : 138, b : 148};
    var slices = mainChartData.column.length;
    var results = [];

    var deltaR = ((endColor.r - startColor.r) / slices);
    var deltaG = ((endColor.g - startColor.g) / slices);
    var deltaB = ((endColor.g - startColor.g) / slices);

    for (var i = 0; i < slices; i++){
        var r = Math.round(startColor.r + deltaR * i);
        var g = Math.round(startColor.g + deltaG * i);
        var b = Math.round(startColor.b + deltaB * i);

        results.push('rgb(' + r + ',' + g + ',' + b + ')');
    }

    return results;
}

function drawColumnChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    var columnChartData = google.visualization.arrayToDataTable(chartData);

    var columnOptions = {
        legend: { position: "top" },
        chartArea: {  
            width: "85%", 
            height: "65%" 
        },
        bar: {
            groupWidth: 50
        },
        vAxis: { title : 'Count of Votes', textStyle: {fontSize : '1', color: '#FFFFFF'}},
    };
 

var columnChart = new google.visualization.ColumnChart(document.getElementById(divId));

// main charts
columnChart.draw(columnChartData, columnOptions);


}