/**
 * TheVirtualBrain-Framework Package. This package holds all Data Management, and 
 * Web-UI helpful to run brain-simulations. To use it, you also need do download
 * TheVirtualBrain-Scientific Package (for simulators). See content of the
 * documentation-folder for more details. See also http://www.thevirtualbrain.org
 *
 * (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
 *
 * This program is free software; you can redistribute it and/or modify it under 
 * the terms of the GNU General Public License version 2 as published by the Free
 * Software Foundation. This program is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
 * License for more details. You should have received a copy of the GNU General 
 * Public License along with this program; if not, you can download it here
 * http://www.gnu.org/licenses/old-licenses/gpl-2.0
 *
 **/

// We keep all-nodes information for current PSE as a global, to have them ready at node-selection, node-overlay.
var PSE_nodesInfo;
// Keep Plot-options and MIN/MAx colors for redraw (e.g. at resize).
var _PSE_plotOptions; 
var _PSE_minColor;
var _PSE_maxColor;
var _PSE_plot = undefined;

/*
 * @param canvasId: the id of the HTML DIV on which the drawing is done. This should have sizes defined or else FLOT can't do the drawing.
 * @param xLabels: the labels for the x - axis
 * @param yLabels: the labels for the y - axis
 * @param seriesArray: the actual data to be used by FLOT
 * @param data_info: additional information about each node. Used when hovering over a node
 * @param min_color: minimum color, used for gradient
 * @param max_color: maximum color, used for gradient
 * @param backPage: page where visualizers fired from overlay should take you back.
 */
function _updatePlotPSE(canvasId, xLabels, yLabels, seriesArray, data_info, min_color, max_color, backPage) {
	
	_PSE_minColor = min_color;
	_PSE_maxColor = max_color;
    PSE_nodesInfo = data_info;
    
    _PSE_plotOptions = {
        series: {
            lines: {
                show: false
            },
            points: {
                lineWidth: 0,
                show: true,
                fill: true
            }
        },
        xaxis: {
            min: -1,
            max: xLabels.length,
            tickSize: 1,
            shouldRotateLabels: true,
            tickFormatter: function(val, axis) {
                if (val < 0 || val >= xLabels.length) {
                    return "";
                }
                return xLabels[val];
            }
        },
        yaxis: {
            min: -1,
            max: yLabels.length,
            tickSize: 1,
            tickFormatter: function(val, axis) {
                if (val < 0 || val >= yLabels.length || yLabels[val] == "_") {
                    return "";
                }
                return yLabels[val];
            }
        },
        grid: {
//            show: false,
            clickable: true,
            hoverable: true
        }

    };
    
    _PSE_plot = $.plot($("#" + canvasId), $.parseJSON(seriesArray), $.extend(true, {}, _PSE_plotOptions));
    changeColors();
    $(".tickLabel").each(function(i) { $(this).css("color", "#000000"); });

    //if you want to catch the right mouse click you have to change the flot sources
    // because it allows you to catch only "plotclick" and "plothover"
    applyClickEvent(canvasId, backPage);
    applyHoverEvent(canvasId);
}

/*
 * Do a redraw of the plot. Be sure to keep the resizable margin elements as the plot method seems to destroy them.
 */
function redrawPlot(plotCanvasId) {
	
	if (_PSE_plot != undefined) {
	    _PSE_plot = $.plot($('#'+plotCanvasId)[0], _PSE_plot.getData(), $.extend(true, {}, _PSE_plotOptions));
	}
}

/*
 * Fire DataType overlay when clicking on a node in PSE.
 */
function applyClickEvent(canvasId, backPage) {

	$("#"+canvasId).unbind("plotclick");
	$("#"+canvasId).bind("plotclick", function (event, pos, item) { 
				if (item != null) {
						var dataPoint = item.datapoint;
			            var dataInfo = PSE_nodesInfo[dataPoint[0]][dataPoint[1]];
			            if (dataInfo['dataType'] != undefined) {
			            	displayNodeDetails(dataInfo['Gid'], dataInfo['dataType'], backPage);
						}
				}
			});
}

var previousPoint = null;
/*
 * On hover display few additional information about this node.
 */
function applyHoverEvent(canvasId) {
	
    $("#" + canvasId).bind("plothover", function (event, pos, item) {
        if (item) {
            if (previousPoint != item.dataIndex) {
                previousPoint = item.dataIndex;
                $("#tooltip").remove();
                var dataPoint = item.datapoint;
                var dataIndex = item.dataIndex;

                var dataInfo = PSE_nodesInfo[dataPoint[0]][dataPoint[1]];
                $('<div id="tooltip">' + dataInfo["tooltip"] + '</div>').css({ position: 'absolute', display: 'none',
							                						top: item.pageY + 5, left: item.pageX + 5,
							                						border: '1px solid #fdd', padding: '2px',
							                						'background-color': '#C0C0C0', opacity: 0.80
							            						   }).appendTo("body").fadeIn(200);
            }
//            plot.unhighlight(item.series, item.datapoint);
        } else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    });
}


/*
 * Take currently selected metrics and refresh the plot. 
 */
function PSE_mainDraw(parametersCanvasId, backPage) {
	
	var colorMetricSelect = document.getElementById('color_metric_select');
	var selectedColorMetric = colorMetricSelect.options[colorMetricSelect.selectedIndex].value;
	
	var sizeMetricSelect = document.getElementById('size_metric_select');
	var selectedSizeMetric = sizeMetricSelect.options[sizeMetricSelect.selectedIndex].value;
	
	var groupId = document.getElementById("datatype-group-id").value
	$.ajax({  	
			type: "POST", 
			url: '/burst/explore/draw_parameter_exploration/' + groupId + '/' + selectedColorMetric + '/' + selectedSizeMetric,
            success: function(r) { 
            	
            		var parameterSpaceData = $.parseJSON(r);
            		$("#" +parametersCanvasId).empty();
            		
            		_updatePlotPSE(parametersCanvasId, parameterSpaceData['labels_x'], parameterSpaceData['labels_y'], 
								   parameterSpaceData['series_array'], parameterSpaceData['data'], 
								   parameterSpaceData['min_color'], parameterSpaceData['max_color'], backPage);
										
					var color_metric = parameterSpaceData['color_metric'];
					for (var i=0; i<colorMetricSelect.options.length; i++) {
						if (colorMetricSelect.options[i].value == color_metric) {
							colorMetricSelect.selectedIndex = i;
						}
					}
					var size_metric = parameterSpaceData['size_metric'];
					for (var i=0; i<sizeMetricSelect.options.length; i++) {
						if (sizeMetricSelect.options[i].value == size_metric) {
							sizeMetricSelect.selectedIndex = i;
						}
					}
					$('#startColorLabel')[0].innerHTML = '<mark>Minimum</mark> ' + parameterSpaceData['min_color'];
					$('#endColorLabel')[0].innerHTML = '<mark>Maximum</mark> ' + parameterSpaceData['max_color'];
					
					var status = parameterSpaceData['status'];
					if (status == "started") {
	            		var timeout = setTimeout("PSE_mainDraw('"+parametersCanvasId+"','"+backPage+"')", 3000);
	            	}
            	},
            error: function(r) {
                displayMessage("Could not refresh with the new metrics.", "errorMessage");
            }});
}


/**
 * Changes the series colors according to the color picker component.
 */
function changeColors() {
    var series = _PSE_plot.getData();
    for (var i = 0; i < series.length; i++) {
        var indexes = series[i].datapoints.points;
        var dataInfo = PSE_nodesInfo[indexes[0]][indexes[1]];
        var colorWeight = dataInfo['color_weight'];
        var color = getGradientColorString(colorWeight, _PSE_minColor, _PSE_maxColor);
        series[i].points.fillColor = color;
        series[i].color = color;
    }
    _PSE_plot.draw();
}




