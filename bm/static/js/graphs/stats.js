

google.load("visualization", "1", {packages:["corechart"]});
    google.setOnLoadCallback(drawChart);


        function Gradient(){
            var startColor = { r : 96, g : 138, b : 148};
            var endColor = { r : 32, g : 44, b : 69};
            var slices = statisticRoleData.length;

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

    function drawChart() {
        var roleChartData = google.visualization.arrayToDataTable(statisticRoleData);
        var geoChartData = google.visualization.arrayToDataTable(statisticGeoData);
        var countryChartData = google.visualization.arrayToDataTable(statisticCountriesData);
        var industryChartData = google.visualization.arrayToDataTable(statisticIndustriesData);

        var statsOptions = {
            legend: 'none',
            pieSliceText: 'none',
            tooltip: { text: 'percentage' },
            slices: Gradient(),
            chartArea: { 
                width: "90%", 
                height: "90%" 
            }
        };
    

    var roleChart = new google.visualization.PieChart(document.getElementById('roleChart'));
    var geoChart = new google.visualization.PieChart(document.getElementById('geoChart'));
    var countryChart = new google.visualization.PieChart(document.getElementById('countryChart'));
    var industryChart = new google.visualization.PieChart(document.getElementById('industryChart'));

    
    // stat charts
    roleChart.draw(roleChartData, statsOptions);
    geoChart.draw(geoChartData, statsOptions);
    countryChart.draw(countryChartData, statsOptions);
    industryChart.draw(industryChartData, statsOptions);
}