function columnGradient(){
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
        legend: { position: "none" },
        hAxis: {title: 'none'},
        chartArea: {  
            width: "85%", 
            height: "65%" 
        },
        colors: columnGradient(),
        bar: {
            groupWidth: 50
        }

    };


var columnChart = new google.visualization.ColumnChart(document.getElementById(divId));

// main charts
columnChart.draw(columnChartData, columnOptions);


}