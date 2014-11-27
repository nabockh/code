
function barGradient(slices){
    var startColor = { r : 51, g : 98, b : 110};
    var endColor = { r : 152, g : 176, b : 179};
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

function drawBarChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    var barChartData = google.visualization.arrayToDataTable(chartData);
            
    var barOptions = {
        chartArea: {  
            width: "65%", 
            height: "65%",
            left: 150
        },
        legend: { position: 'top', maxLines: 1 },
        bar: { groupWidth: '75%' },
        isStacked: true,
        colors: barGradient(chartData.length),
    };

    var barChart = new google.visualization.BarChart(document.getElementById(divId));

    // main charts
    barChart.draw(barChartData, barOptions);
}