function statsGradient(slices){
    var startColor = { r : 96, g : 138, b : 148};
    var endColor = { r : 32, g : 44, b : 69};

    var results = {};

    var deltaR = ((endColor.r + startColor.r) / slices);
    var deltaG = ((endColor.g + startColor.g) / slices);
    var deltaB = ((endColor.g + startColor.g) / slices);

    for (var i = 0; i < slices; i++){
        var r = Math.round(startColor.r + deltaR * i);
        var g = Math.round(startColor.g + deltaG * i);
        var b = Math.round(startColor.b + deltaB * i);

        results[i] = {'color' : 'rgb(' + r + ',' + g + ',' + b + ')'};
    }

    return results;
}

function drawStatsChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    var roleChartData = google.visualization.arrayToDataTable(chartData);
    var geoChartData = google.visualization.arrayToDataTable(chartData);
    var countryChartData = google.visualization.arrayToDataTable(chartData);
    var industryChartData = google.visualization.arrayToDataTable(chartData);

    var statsOptions = {
        legend: 'none',
        pieSliceText: 'none',
        tooltip: { text: 'percentage' },
        slices: statsGradient(chartData.length),
        chartArea: { 
            width: "90%", 
            height: "90%" 
        }
    };


    var roleChart = new google.visualization.PieChart(document.getElementById(divId));
    var geoChart = new google.visualization.PieChart(document.getElementById(divId));
    var countryChart = new google.visualization.PieChart(document.getElementById(divId));
    var industryChart = new google.visualization.PieChart(document.getElementById(divId));

    
    // stat charts
    roleChart.draw(roleChartData, statsOptions);
    geoChart.draw(geoChartData, statsOptions);
    countryChart.draw(countryChartData, statsOptions);
    industryChart.draw(industryChartData, statsOptions);
}