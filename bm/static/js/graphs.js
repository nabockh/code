google.load("visualization", "1", {packages:["corechart"]});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
        var donutChartData = google.visualization.arrayToDataTable(mainChartData.pie);
        var columnChartData = google.visualization.arrayToDataTable(mainChartData.column);
        var lineChartData = google.visualization.arrayToDataTable(mainChartData.line);

        var roleChartData = google.visualization.arrayToDataTable(statisticRoleData);
        var geoChartData = google.visualization.arrayToDataTable(statisticGeoData);
        var countryChartData = google.visualization.arrayToDataTable(statisticCountriesData);
        var industryChartData = google.visualization.arrayToDataTable(statisticIndustriesData);

        var statsOptions = {
            legend: 'none',
            pieSliceText: 'none',
            tooltip: { text: 'percentage' },
            // 'width':334,
            // 'height':238,
            slices: {
                0: {color: '#202C45'},
                1: {color: '#41495D'},
                2: {color: '#8592B2'},
                3: {color: '#98b0b3'},
                4: {color: '#608a94'},
                5: {color: '#33626e'}
            },
            chartArea: { 
                // left: 20, 
                // top: 20, 
                width: "90%", 
                height: "90%" 
            }
        };
        
        var donutOptions = {
            pieHole: 0.35,
            legend: 'none',
            pieSliceText: 'label',
            tooltip: { text: 'percentage' },
            // 'width': 480,
            // 'height':480,
            slices: {
                0: {color: '#202C45'},
                1: {color: '#41495D'},
                2: {color: '#8592B2'},
                3: {color: '#98b0b3'},
                4: {color: '#608a94'},
                5: {color: '#33626e'}
            },
            chartArea: { 
                // left: 25, 
                // top: 25, 
                width: "90%", 
                height: "90%" 
            }

        };

        var columnOptions = {
            legend: { position: "none" },
            hAxis: {title: 'none'},
            // width: 480,
            // height: 238,
            chartArea: { 
                // left: 45, 
                // top: 35, 
                width: "85%", 
                height: "65%" 
            },
            colors: [
                '#202C45',
                '#41495D',
                '#8592B2',
                '#98b0b3',
                '#608a94',
                '#33626e'
            ],
            bar: {
                groupWidth: 50
            }

        };

        var lineOptions = {
            legend: 'none',
            colors: ['#8592B2'],
            lineWidth: 3
        };


    var donutChart = new google.visualization.PieChart(document.getElementById('donutChart'));
    var columnChart = new google.visualization.ColumnChart(document.getElementById('columnChart'));
    var lineChart = new google.visualization.ScatterChart(document.getElementById('lineChart'));

    var roleChart = new google.visualization.PieChart(document.getElementById('roleChart'));
    var geoChart = new google.visualization.PieChart(document.getElementById('geoChart'));
    var countryChart = new google.visualization.PieChart(document.getElementById('countryChart'));
    var industryChart = new google.visualization.PieChart(document.getElementById('industryChart'));

    // main charts
    donutChart.draw(donutChartData, donutOptions);
    columnChart.draw(columnChartData, columnOptions);
    lineChart.draw(lineChartData, lineOptions);


    // stat charts
    roleChart.draw(roleChartData, statsOptions);
    geoChart.draw(geoChartData, statsOptions);
    countryChart.draw(countryChartData, statsOptions);
    industryChart.draw(industryChartData, statsOptions);
}