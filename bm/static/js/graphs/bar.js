
function barGradient(slices){
    var startColor = { r : 51, g : 98, b : 110};
    var endColor = { r : 207, g : 207, b : 207};
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

    var view = new google.visualization.DataView(barChartData);
    var arr = [0];

    for(var i=1;i<=barChartData.getNumberOfRows();i++) {
        arr.push(i);
        arr.push({ calc: "stringify", sourceColumn: i, type: "string", role: "annotation" });
    }


    view.setColumns(arr);

    if( screen.width < 641 ) {
        var barOptions = {
            chartArea: {
                top: 25,
                left: 60,
                width: '75%'
            },
            legend: { position: 'bottom', maxLines: 1 },
            bar: { groupWidth: '75%' },
            isStacked: true,
            colors: barGradient(chartData.length),
            hAxis: {title : '% of Respondents', viewWindow: { min: 1, max: 100.9}, ticks: [{v:1, f: '0'}, {v:25, f: '25'}, {v:50, f: '50'}, {v:75, f: '75'}, {v:100, f: '100'}]},
            // annotations: {
            //   textStyle: {fontSize: 2, color: '#000' },
            // }
            // orientation: 'horizontal'
        };
    } else {

        var barOptions = {
            chartArea: {  
                width: "65%", 
                height: "65%",
                left: 100,
            },
            legend: { position: 'top', maxLines: 1 },
            bar: { groupWidth: '75%' },
            isStacked: true,
            colors: barGradient(chartData.length),
            hAxis: {title : '% of Respondents', viewWindow: { min: 1, max: 100.9}, ticks: [{v:1, f: '0'}, {v:25, f: '25'}, {v:50, f: '50'}, {v:75, f: '75'}, {v:100, f: '100'}]}

        };
    };


    var barChart = new google.visualization.BarChart(document.getElementById(divId));

    // main charts
    barChart.draw(view, barOptions);
};

function drawCircles(avgCircles, containerId) {
    avgCircles.sort(function(a, b){return a-b}); // Sort
    $.each(avgCircles, function(index, value) {
      $("#" + containerId + ".avgBar").append("<div class='barCircle'><span class='avgValue'>" + value + "</span><span class='tt'>" + "Average Rank: <b>" + value + "</b></span></div>");
    });

    var len = avgCircles.length,
        size = 195 / len,
        margins = size * 0.354;

    $("#" + containerId + ".avgBar .barCircle").each(function(){
        $(this).height(size - margins).width(size - margins).css('line-height', size - margins + 'px').css('margin-top', margins / 2 + 1).css('margin-bottom', margins);
        if ( len > 5 ) {
            $(this).css('line-height', '16px').children('span.avgValue').css('font-size', '8px');
        };
         if ( len > 7 ) {
            $(this).css('line-height', '8px').children('span.avgValue').text('A').css('font-size', '8px');
        };
    });
};