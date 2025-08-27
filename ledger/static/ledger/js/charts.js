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
    }

    return true;
}

function initCharts(data) {
    const billboard = data;
    if (!billboard) return;

    // Dispose of existing Root instances with the same id if they exist
    const rootChartId = 'rattingChart';
    const rootBarId = 'rattingBar';

    // Create the chart
    const barChart = load_or_create_Chart(rootBarId, billboard.rattingbar, 'bar');
    const chart = load_or_create_Chart(rootChartId, billboard.charts, 'chart');
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
            padAngle: 1,
            startAngle: 80,
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
        fontSize: 16,
        centerX: am5.percent(0),
        oversizedBehavior: 'fit',
        maxWidth: 100,
        wrap: true,
        layer: 0,
        layerMargin: { left: 30, right: 30, top: 70, bottom: 70 }
    });

    series.children.moveValue(series.bulletsContainer, 0);
    series.data.setAll(data.series);

    // Remove Hide the chart container
    $('#ChartContainer').removeClass('d-none');
    $('#ChartContainer').addClass('active');

    // Make stuff animate on load
    series.appear(1000, 100);
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

        // Use categories from the data (now as array of dicts: {name, label})
        if (Array.isArray(data.categories) && typeof data.categories[0] === 'object') {
            data.categories.forEach((cat) => makeSeries(cat.label || cat.label, cat.name));
        } else {
            // fallback for old format (array of strings)
            data.categories.forEach((name) => makeSeries(name, name));
        }

        // Remove Hide the chart container
        $('#rattingBarContainer').removeClass('d-none');
        $('#rattingBarContainer').addClass('active');

        chart.appear(1000, 100);
    }
    return chart;
}
