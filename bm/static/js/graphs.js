google.load("visualization", "1", {packages:["corechart"]});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
        var roleChartData = google.visualization.arrayToDataTable(statisticRoleData);
        var geoChartData = google.visualization.arrayToDataTable(statisticGeoData);
        var countryChartData = google.visualization.arrayToDataTable(statisticCountriesData);
        var industryChartData = google.visualization.arrayToDataTable(statisticIndustriesData);

        var statsOptions = {
        legend: 'none',
        pieSliceText: 'none',
        tooltip: { text: 'percentage' },
        'width':334,
        'height':238,
        slices: {
            0: {color: '#202C45'},
            1: {color: '#41495D'},
            2: {color: '#8592B2'},
            3: {color: '#98b0b3'},
            4: {color: '#608a94'},
            5: {color: '#33626e'}
          }

        
    };

    // var donutChart = new google.visualization.PieChart(document.getElementById('donutChart'));
    var roleChart = new google.visualization.PieChart(document.getElementById('roleChart'));
    var geoChart = new google.visualization.PieChart(document.getElementById('geoChart'));
    var countryChart = new google.visualization.PieChart(document.getElementById('countryChart'));
    var industryChart = new google.visualization.PieChart(document.getElementById('industryChart'));
    // roleChart.draw(roleChartData, statsOptions);
    roleChart.draw(roleChartData, statsOptions);
    geoChart.draw(geoChartData, statsOptions);
    countryChart.draw(countryChartData, statsOptions);
    industryChart.draw(industryChartData, statsOptions);
}