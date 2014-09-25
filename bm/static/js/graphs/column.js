function columnGradient(slices){
    var startColor = { r : 96, g : 138, b : 148};
    var endColor = { r : 32, g : 44, b : 69};
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
    if(chartData.length > 1){
        for(var i = 1; i < chartData.length; ++i){
            for(var j = 1; j < chartData[i].length; ++j){
                chartData[i][j] = {"v": chartData[i][j], "f": chartData[i][j]+"%"};
            }
        }
    }

    var columnChartData = google.visualization.arrayToDataTable(chartData);
 
    var columnOptions = {
        legend: { position: "top" },
        chartArea: {  
            width: "70%", 
            height: "65%" 
        },
        colors: columnGradient(chartData.length),
        bar: {
            groupWidth: "80%"
        },
        vAxis: { title : '% of Respondants', viewWindow: { min: 0, max: 100}, ticks: [{v:0, f: '0'}, {v:25, f: '25%'}, {v:50, f: '50%'}, {v:75, f: '75%'}, {v:100, f: '100%'}]},
    };
 

var columnChart = new google.visualization.ColumnChart(document.getElementById(divId));

// main charts
columnChart.draw(columnChartData, columnOptions);


}