google.load("visualization", "1", {packages:["corechart"]});
    google.setOnLoadCallback(drawChart);

    function pieGradient(){
        var startColor = { r : 32, g : 44, b : 69};
        var endColor = { r : 96, g : 138, b : 148};
        var slices = mainChartData.pie.length;

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

    function drawChart() {
        var donutChartData = google.visualization.arrayToDataTable(mainChartData.pie);
                
        var donutOptions = {
            pieHole: 0.35,
            legend: 'none',
            pieSliceText: 'label',
            tooltip: { text: 'percentage' },
            slices: pieGradient(),
            chartArea: { 
                width: "90%", 
                height: "90%" 
            }

        };

       
    var donutChart = new google.visualization.PieChart(document.getElementById('donutChart'));

    // main charts
    donutChart.draw(donutChartData, donutOptions);
}