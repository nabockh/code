function pieGradient(slices){
    var startColor = { r : 32, g : 44, b : 69};
    var endColor = { r : 96, g : 138, b : 148};

    var results = {};

    var deltaR = ((endColor.r - startColor.r) / slices);
    var deltaG = ((endColor.g - startColor.g) / slices);
    var deltaB = ((endColor.g - startColor.g) / slices);

    for (var i = 0; i < slices; i++){
        var r = Math.round(startColor.r + deltaR * i);
        var g = Math.round(startColor.g + deltaG * i);
        var b = Math.round(startColor.b + deltaB * i);

        results[i] = {'color' : 'rgb(' + r + ',' + g + ',' + b + ')'};
    }

    return results;
}

function drawPieChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }

    var donutChartData = google.visualization.arrayToDataTable(chartData);
            
    if( screen.width < 641 ) {
        var donutOptions = {
            legend: { position: "bottom" },
            pieSliceText: 'percentage',
            tooltip: { text: 'percentage' },
            slices: pieGradient(chartData.length),
            chartArea: {
                top: 25,
                width: '80%'
            },
        };
    } else {
        var donutOptions = {
            legend: { position: "bottom" },
            pieSliceText: 'percentage',
            tooltip: { text: 'percentage' },
            slices: pieGradient(chartData.length),
            chartArea: {
                top: '5%',
                width: "90%", 
                height: "80%" 
            }
        };
    };

   
    var donutChart = new google.visualization.PieChart(document.getElementById(divId));

    // main charts
    donutChart.draw(donutChartData, donutOptions);
}