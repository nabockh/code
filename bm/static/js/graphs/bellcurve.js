function drawBellcurveChart(chartData, divId) {
    if (typeof google == 'undefined') {
        throw new Exception();
    }
    console.log(chartData);
    var nd = function (x, avg, sd) {
        var C = (sd * Math.sqrt(2 * Math.PI));
        var dr = Math.pow(x - avg, 2) / (2 * Math.pow(sd, 2));
        return Math.exp(-dr) / C;

    };
    console.log('ND: '+ nd);
    var prepareData = function (avg, sd, min, max) {
        var y = function (x) {
            return nd(x, avg, sd);
        };
        var res = [];
        res.push(['Range', '%']);
        res.push([ avg-3*sd, 100 * y(avg-3*sd)])

        var x = avg-2*sd;
        while (x < (avg)) {
            res.push([x, 100 * y(x)]);
            x += sd;
        }
        res.push([ avg, 100 * y(avg)]);
        x = avg+sd;

        while (x < avg + 2*sd) {
            res.push([ x, 100 * y(x)]);
            x += sd;
        }
        res.push([ avg+2*sd, 100 * y(avg+2*sd)])
        res.push([ avg+3*sd, 100 * y(avg+3*sd)])

        return res;
    };
    console.log(prepareData(chartData.avg, chartData.sd,chartData.min, chartData.max));
    var y_max = nd(chartData.avg, chartData.avg, chartData.sd);
    y_max *= 1.1;
    y_max = Math.ceil(y_max * 100);
    var bellcurveChartData = new google.visualization.arrayToDataTable(
        prepareData(chartData.avg, chartData.sd,chartData.min, chartData.max));
        console.log(bellcurveChartData);

    var median = prepareData(chartData.avg,chartData.sd);

    var bellcurveOptions = {

        // pointSize: 0,
        enableInteractivity: false,
        legend: 'none',
        colors: ['#608a94'],
        lineWidth: 3,
        series: [
            {'color': '#33626e'}
        ],
        chartArea: {
            width: "75%",
            height: "65%"
        },
        tooltip: {'trigger': 'none'},
        curveType: 'function',
        vAxis: { title: '% of Respondents', titleTextStyle: {color: '#33626e'}, allowContainerBoundaryTextCufoff: true, format : "#%"},
        hAxis: { baselineColor : 'transparent', textStyle: {fontSize : '9'}, ticks: [{v:median[3][0], f:' ( ' + Math.round((chartData.avg - chartData.sd), 1).toFixed(0) + ' )' + '\n' + '- σ'}, {v:median[4][0], f:' ( ' + chartData.avg.toFixed(0) + ' )' + '\n' + 'μ'}, {v:median[5][0], f:' ( ' + Math.round((chartData.avg + chartData.sd), 1).toFixed(0) + ' )' + '\n' + '+ σ'}], titlePosition: 'in' },
        intervals: { 'style': 'area' },
    };

    var bellcurveChart = new google.visualization.LineChart(document.getElementById(divId));

    // main charts
    bellcurveChart.draw(bellcurveChartData, bellcurveOptions);
};