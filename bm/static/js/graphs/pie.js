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
            slices: {
                0: {color: '#202c45'},
                1: {color: '#5c6e7c'},
                2: {color: '#41495d'},
                3: {color: '#636e88'},
                4: {color: '#8592b2'},
                5: {color: '#8fa1b3'},
                6: {color: '#98b0b3'},
                7: {color: '#608a94'},
                8: {color: '#33626e'},
                9: {color: '#2a475a'}
            },
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
            // slices: pieGradient(chartData.length),
            slices: {
                0: {color: '#202c45'},
                1: {color: '#5c6e7c'},
                2: {color: '#41495d'},
                3: {color: '#636e88'},
                4: {color: '#8592b2'},
                5: {color: '#8fa1b3'},
                6: {color: '#98b0b3'},
                7: {color: '#608a94'},
                8: {color: '#33626e'},
                9: {color: '#2a475a'}
            },
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