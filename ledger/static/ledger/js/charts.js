/* global am5 */
/* global am5flow */
/* global am5themes_Animated */
/* global am5themes_Dark */
/* global am5percent */
/* global am5xy */
/* global entityType */

// Function to dispose of a root instance if it exists
function disposeRoot(rootId) {
    const rootElement = am5.registry.rootElements.find(root => root.dom.id === rootId);
    if (rootElement) {
        rootElement.dispose();
    }
}

function load_or_create_Chart(div, data, chart) {
    // Dispose existing Root instances
    disposeRoot(div);

    let root = am5.Root.new(div);
    root.setThemes([am5themes_Animated.new(root), am5themes_Dark.new(root)]);

    if (chart === 'bar') {
        return createRattingBarChart(root, data, div);
    } else if (chart === 'chart') {
        return createChordChart(root, data, div);
    } else if (chart === 'gauge') {
        return createWorkflowGaugeChart(root, data, div);
    }

    return true;
}

function initCharts(data) {
    const billboard = data;
    if (!billboard) return;

    // Dispose of existing Root instances with the same id if they exist
    const rootChartId = 'rattingChart';
    const rootBarId = 'rattingBar';
    //const rootGaugeId = 'rattingworkGauge';

    // Create the chart
    const barChart = load_or_create_Chart(rootBarId, billboard.rattingbar, 'bar');
    const chart = load_or_create_Chart(rootChartId, billboard.charts, 'chart');
    //const gaugeChart = load_or_create_Chart(rootGaugeId, billboard.workflowgauge, 'gauge');
}

function createChordChart(root, data, id) {
    if (!data || !Array.isArray(data.series)) {
        console.log('Data is not in the expected format:', data);
        disposeRoot(id);
        $('#ChartContainer').addClass('d-none');
        $('#ChartContainer').removeClass('active');
        return;
    }

    // Store the root object globally
    window.chordsRoots = window.chordsRoots || {};
    window.chordsRoots[id] = root;

    var series = root.container.children.push(
        am5flow.ChordDirected.new(root, {
            sourceIdField: 'from',
            targetIdField: 'to',
            valueField: 'value',
            nodeWidth: 10,
            minSize: 0.10,
            hiddenSize: 0.10,
        })
    );

    series.links.template.set(
        'fillStyle',
        'source'
    );

    series.links.template.setAll({
        fillOpacity: 0.5,
        tension: 0.7,
        tooltipText: '[Bold]{sourceId}[/] \nTo: {targetId} ([Bold]{value.formatNumber("#,###.")}[/] ISK)'
    });

    series.nodes.get('colors').set('step', 2);

    series.bullets.push(function (_root, _series, dataItem) {
        var bullet = am5.Bullet.new(root, {
            locationY: Math.random(),
            sprite: am5.Circle.new(root, {
                radius: 5,
                fill: dataItem.get('source').get('fill')
            })
        });

        bullet.animate({
            key: 'locationY',
            to: 1,
            from: 0,
            duration: Math.random() * 1000 + 2000,
            loops: Infinity
        });

        return bullet;
    });

    series.nodes.labels.template.setAll({
        textType: 'radial',
        centerX: 0,
        fontSize: 16,
        maxWidth: 150,
        wrap: true,
    });

    series.children.moveValue(series.bulletsContainer, 0);
    series.data.setAll(data.series);

    // Remove Hide the chart container
    $('#ChartContainer').removeClass('d-none');
    $('#ChartContainer').addClass('active');

    // Make stuff animate on load
    series.appear(1000, 100);
}

function createRattingChart(root, data, id) {
    if (!data || !Array.isArray(data.series)) {
        console.log('Data is not in the expected format:', data);
        disposeRoot(id);
        $('#ChartContainer').addClass('d-none');
        $('#ChartContainer').removeClass('active');
        return;
    }

    // Store the root object globally
    window.chartsRoots = window.chartRoots || {};
    window.chartsRoots[id] = root;

    let chart = root.container.children.values.find(child => child instanceof am5xy.XYChart);
    if (chart) {
        // Update existing chart data
        chart.series.values[0].data.setAll(data.series);
    } else {
        // Create a new chart
        chart = root.container.children.push(am5percent.PieChart.new(root, {
            innerRadius: am5.percent(50),
            layout: root.verticalLayout
        }));

        const series = chart.series.push(am5percent.PieSeries.new(root, {
            valueField: 'value',
            categoryField: 'category',
            alignLabels: false,
        }));

        const colorSet = am5.ColorSet.new(root, {
            colors: [series.get('colors').getIndex(0)], passOptions: { lightness: -0.05, hue: 0 }
        });

        series.states.create('hidden', { startAngle: 180, endAngle: 180 });

        series.slices.template.setAll({
            templateField: 'sliceSettings',
            strokeOpacity: 0,
            tooltipText: '{category}: {valuePercentTotal.formatNumber("0.00")}% ({value} ISK)',
        });

        // Labels for category names outside the pie chart
        series.labels.template.setAll({
            textType: 'circular',
            centerX: 0,
            centerY: 0,
            text: '' // Display only the category name
        });

        // Transform the data to the required format
        var transformedData = [];
        var seriesData = data.series[0];
        for (var category in seriesData) {
            if (category !== 'date') {
                transformedData.push({
                    category: category,
                    value: seriesData[category].value,
                    percentage: seriesData[category].percentage,
                    mode: seriesData[category].mode
                });
            }
        }

        const legend = chart.children.push(am5.Legend.new(root, {
            centerX: am5.percent(50),
            x: am5.percent(50),
            centerY: am5.percent(100),
            y: am5.percent(100),
            layout: am5.GridLayout.new(root, {
                maxColumns: 5,
                fixedWidthGrid: true
            })
        }));

        // Increase the spacing between legend items
        legend.itemContainers.template.setAll({
            paddingTop: 10,
            paddingBottom: 10,
            paddingLeft: 10,
            paddingRight: 10
        });

        series.data.setAll(transformedData);

        legend.labels.template.setAll({
            text: '{category}', // Display the category name and mode symbol in the legend
        });

        legend.valueLabels.template.setAll({
            text: '' // Hide the percentage values in the legend
        });

        // Set custom markers for legend items
        legend.markers.template.setup = function(marker) {
            marker.events.on('dataitemchanged', function() {
                var dataItem = marker._dataItem;
                var series = dataItem.dataContext;
                var iconColor = series.dataContext.mode === 'income' ? 'income' : 'cost';
                marker.children.push(am5.Picture.new(root, {
                    width: 64,
                    height: 64,
                    src: '/static/ledger/images/' + iconColor + '.png',
                    centerX: am5.percent(35),
                    centerY: am5.percent(35),
                    x: am5.percent(-50),
                }));

                dataItem.on('markerRectangle', function(rectangle) {
                    rectangle.set('forceHidden', true);
                });
            });
        };

        legend.data.setAll(series.dataItems);

        // Remove Hide the chart container
        $('#ChartContainer').removeClass('d-none');
        $('#ChartContainer').addClass('active');

        series.appear();
        chart.appear(1000, 100);
    }
    return chart;
}

function createRattingBarChart(root, data, id) {
    if (!data || !Array.isArray(data.series)) {
        console.debug('Data is not in the expected format:', data);
        disposeRoot(id);
        $('#rattingBarContainer').addClass('d-none');
        $('#rattingBarContainer').removeClass('active');
        return;
    }

    // Store the root object globally
    window.rattingRoots = window.rattingRoots || {};
    window.rattingRoots[id] = root;

    let chart = root.container.children.values.find(child => child instanceof am5xy.XYChart);
    if (chart) {
        // Update existing chart data
        chart.series.values[0].data.setAll(data.series);
    } else {
        chart = root.container.children.push(am5xy.XYChart.new(root, {
            panX: false,
            panY: false,
            wheelX: 'panX',
            wheelY: 'zoomX',
            paddingLeft: 0,
            layout: root.verticalLayout
        }));

        chart.set('scrollbarX', am5.Scrollbar.new(root, { orientation: 'horizontal' }));

        const xRenderer = am5xy.AxisRendererX.new(root, {
            minorGridEnabled: true }
        );
        xRenderer.grid.template.setAll({ location: 1 });

        const yAxis = chart.yAxes.push(am5xy.ValueAxis.new(root, {
            numberFormat: "#,###' ISK'",
            renderer: am5xy.AxisRendererY.new(root, {
            })
        }));

        const xAxis = chart.xAxes.push(am5xy.CategoryAxis.new(root, {
            categoryField: 'date',
            renderer: xRenderer,
            tooltip: am5.Tooltip.new(root, {})
        }));

        xAxis.data.setAll(data.series);

        const legend = chart.children.push(am5.Legend.new(root, { centerX: am5.p50, x: am5.p50 }));

        function makeSeries(name, fieldName) {
            const series = chart.series.push(am5xy.ColumnSeries.new(root, {
                name: name,
                stacked: true,
                xAxis: xAxis,
                yAxis: yAxis,
                valueYField: fieldName,
                categoryXField: 'date'
            }));

            series.columns.template.setAll({
                tooltipText: "{name}: {valueY.formatNumber('#,###')} ISK", tooltipY: am5.percent(10)
            });

            series.data.setAll(data.series);
            series.appear();

            series.bullets.push(function () {
                return am5.Bullet.new(root, {
                    sprite: am5.Label.new(root, {
                        text: '', fill: root.interfaceColors.get('alternativeText'),
                        centerY: am5.p50, centerX: am5.p50, populateText: false
                    })
                });
            });

            legend.data.push(series);
        }

        // Use categories from the data
        data.categories.forEach((name, i) => makeSeries(name, name.toLowerCase()));

        // Remove Hide the chart container
        $('#rattingBarContainer').removeClass('d-none');
        $('#rattingBarContainer').addClass('active');

        chart.appear(1000, 100);
    }
    return chart;
}

function createWorkflowGaugeChart(root, data, id) {
    if (!data || !Array.isArray(data.series)) {
        console.debug('Data is not in the expected format:', data);
        disposeRoot(id);
        $('#workGaugeContainer').addClass('d-none');
        $('#workGaugeContainer').removeClass('active');
        return;
    }

    // Store the root object globally
    window.gaugesRoots = window.gaugesRoots || {};
    window.gaugesRoots[id] = root;

    const chart = root.container.children.push(am5percent.PieChart.new(root, {
        startAngle: 160, endAngle: 380
    }));

    const series = chart.series.push(am5percent.PieSeries.new(root, {
        valueField: 'value',
        categoryField: 'category',
        startAngle: 180,
        endAngle: 360,
        radius: am5.percent(95),
        innerRadius: am5.percent(50),
        alignLabels: false,
    }));

    const colorSet = am5.ColorSet.new(root, {
        colors: [series.get('colors').getIndex(0)], passOptions: { lightness: -0.05, hue: 0 }
    });

    series.states.create('hidden', { startAngle: 180, endAngle: 180 });

    const legend = chart.children.push(am5.Legend.new(root, {
        centerX: am5.percent(50),
        x: am5.percent(50),
        centerY: am5.percent(100),
        y: am5.percent(100),
        marginTop: 15,
        marginBottom: 15
    }));

    series.slices.template.setAll({
        templateField: 'sliceSettings',
        strokeOpacity: 0
    });

    series.labels.template.setAll({
        textType: 'circular',
        text: '',
        radius: am5.percent(-30),
        inside: false,
        centerX: am5.percent(50),
        centerY: am5.percent(50),
    });

    series.labels.template.adapters.add('radius', function (radius, target) {
        var dataItem = target.dataItem;
        var slice = dataItem.get('slice');
        return -(slice.get('radius') - slice.get('innerRadius')) / 2 - 10;
    });

    // Transform the data to the required format
    var transformedData = [];
    var seriesData = data.series[0];
    for (var category in seriesData) {
        if (category !== 'date') {
            transformedData.push({
                category: category,
                value: seriesData[category].value,
                mode: seriesData[category].mode
            });
        }
    }

    series.data.setAll(transformedData);

    legend.labels.template.setAll({
        text: '{category}', // Display the category name and mode symbol in the legend
    });

    legend.valueLabels.template.setAll({
        text: '' // Hide the percentage values in the legend
    });

    legend.data.setAll(series.dataItems);

    $('#workGaugeContainer').removeClass('d-none');
    $('#workGaugeContainer').addClass('active');

    series.appear();
    chart.appear(1000, 100);
    return chart;
}
