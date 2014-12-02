
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

    var view = new google.visualization.DataView(barChartData);
    var arr = [0];

    for(var i=1;i<=barChartData.getNumberOfRows();i++) {
        arr.push(i);
        arr.push({ calc: "stringify", sourceColumn: i, type: "string", role: "annotation" });
    }


    view.setColumns(arr);



    var barOptions = {
        chartArea: {  
            width: "65%", 
            height: "65%",
            left: 100,
            right: 100,
        },
        legend: { position: 'top', maxLines: 1 },
        bar: { groupWidth: '75%' },
        isStacked: true,
        colors: barGradient(chartData.length),
        hAxis: {title : '% of Respondents'},
    };

    var barChart = new google.visualization.BarChart(document.getElementById(divId));

    // main charts
    barChart.draw(view, barOptions);
};

function drawCircles(avgCircles, containerId) {
    avgCircles.sort(function(a, b){return a-b}); // Sort

    $.each(avgCircles, function(index, value) {
      $("#" + containerId + ".avgBar").append("<div class='barCircle'><span class='avgValue'>" + value + "</span><span class='tt'>" + "Avarage Rank: <b>" + value + "</b></span></div>");
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