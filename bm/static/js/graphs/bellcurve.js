function drawBellcurveChart(chartData, divId) {
        if (typeof google == 'undefined') {
            throw new Exception();
        }

        var prepareData = function (avg, sd){
            var x1 = avg - 3*sd,
                    x2 = avg + 3*sd;
            var d  = 6*sd/50;

            var C = (sd*Math.sqrt(2*Math.PI));

            var res = [];

            var y = function(x){
                var e = Math.exp(1),
                        dr = Math.pow(x - avg, 2)/(2*Math.pow(sd,2));
                return Math.exp(-dr) / C;
            };

            for(var x = x1; x < x2; x+=d){
                res.push([x, y(x), y(x), 0]);
            }
            return res;
        };

        var bellcurveChartData = new google.visualization.DataTable();
        bellcurveChartData.addColumn('number', 'x');
        bellcurveChartData.addColumn('number', 'values');
        bellcurveChartData.addColumn({id:'i0', type:'number', role:'interval'});
        bellcurveChartData.addColumn({id:'i1', type:'number', role:'interval'});

        bellcurveChartData.addRows(prepareData(chartData.avg,chartData.sd));
        var median = prepareData(chartData.avg,chartData.sd);

        var bellcurveOptions = {
            curveType: 'function',
            pointSize: 0,
            enableInteractivity: false,
            legend: 'none',
            colors: ['#608a94'],
            lineWidth: 3,
            intervals: { 'style':'area' },
            series: [{'color': '#33626e'}],
            chartArea: {
                width: "80%",
                height: "70%"
            },
            tooltip: {'trigger' : 'none'},
            hAxis: { baselineColor : 'transparent', ticks: [{v:median[16][0], f:'σ-1'}, {v:median[25][0], f:'avg'}, {v:median[34][0], f:'σ+1'}] }
        };

        var bellcurveChart = new google.visualization.LineChart(document.getElementById(divId));

        // main charts
        bellcurveChart.draw(bellcurveChartData, bellcurveOptions);
    };