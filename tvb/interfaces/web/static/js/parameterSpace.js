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
                var dataInfo = PSE_nodesInfo[dataPoint[0]][dataPoint[1]];
                var tooltipText = ("" + dataInfo["tooltip"]).split("&amp;").join("&").split("&lt;").join("<").split("&gt;").join(">");

                $('<div id="tooltip"> </div>').html(tooltipText
                    ).css({ position: 'absolute', display: 'none', top: item.pageY + 5, left: item.pageX + 5,
						   border: '1px solid #fdd', padding: '2px', 'background-color': '#C0C0C0', opacity: 0.80 }
                    ).appendTo('body').fadeIn(200);
            }
        } else {
            $("#tooltip").remove();
            previousPoint = null;
        }
    });
}


function PSE_previewBurst(parametersCanvasId, labelsXJson, labelsYJson, series_array, dataJson,
						 min_color, max_color, backPage, color_metric, size_metric) {
	drawColorPickerComponent('startColorSelector', 'endColorSelector', changeColors);
	var labels_x = $.parseJSON(labelsXJson);
	var labels_y = $.parseJSON(labelsYJson);
	var data = $.parseJSON(dataJson);
	
	var colorMetricSelect = document.getElementById('color_metric_select');
	var sizeMetricSelect = document.getElementById('size_metric_select');
	
	_updatePlotPSE('main_div_pse', labels_x, labels_y, series_array, data, 
				   min_color, max_color, backPage);
						
	for (var i=0; i<colorMetricSelect.options.length; i++) {
		if (colorMetricSelect.options[i].value == color_metric) {
			colorMetricSelect.selectedIndex = i;
		}
	}
	for (var i=0; i<sizeMetricSelect.options.length; i++) {
		if (sizeMetricSelect.options[i].value == size_metric) {
			sizeMetricSelect.selectedIndex = i;
		}
	}
	$('#startColorLabel')[0].innerHTML = '<mark>Minimum</mark> ' + min_color;
	$('#endColorLabel')[0].innerHTML = '<mark>Maximum</mark> ' + max_color;
	
	if (status == "started") {
		var timeout = setTimeout("PSE_mainDraw('"+parametersCanvasId+"','"+backPage+"')", 3000);
	}
}


/*
 * Take currently selected metrics and refresh the plot. 
 */
function PSE_mainDraw(parametersCanvasId, backPage, groupGID, selectedColorMetric, selectedSizeMetric) {
	
	if (groupGID == undefined) {
		// We didn't get parameter, so try to get group id from page
		groupGID = document.getElementById("datatype-group-gid").value
	}
	var url = '/burst/explore/draw_discrete_exploration/' + groupGID
	
	if (selectedColorMetric == undefined) {
		selectedColorMetric = $('#color_metric_select').val()
	}
	if (selectedSizeMetric == undefined) {
		selectedSizeMetric = $('#size_metric_select').val()
	}
	
	if (selectedColorMetric != '' && selectedColorMetric != undefined) { 
			url += '/' + selectedColorMetric;
			if (selectedSizeMetric != ''  && selectedSizeMetric != undefined) {
				url += '/' + selectedSizeMetric
			}
		 }
	
	$.ajax({  	
			type: "POST", 
			url: url,
            success: function(r) { 
            		$('#' + parametersCanvasId).html(r);
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


/*************************************************************************************************************************
 * 			ISOCLINE PSE BELLOW
 *************************************************************************************************************************/


var serverIp = null;
var serverPort = null;
var figuresDict = null;
var currentFigure = null;
var width = null;
var height = null;

/*
 * If for some reason we change the plot size for one of the images,
 * store it so we can resize all other plots on the onchange event.
 */
function resizeFigures(newWidth, newHeight) {

	width = newWidth;
	height = newHeight;
	resizePlot(currentFigure, width, height);
}

/*
 * Do the actual resize, given a figure id, width and height.
 */
function resizePlot(id, width, height) {

	if (currentFigure != null) {
		resize = id;
	    do_resize(currentFigure, width, height);
	    resize = -1;
	}
}

/*
 * Store all needed data as js variables so we can use later on.
 */
function initISOData(metric, figDict, servIp, servPort) {

	figuresDict = $.parseJSON(figDict);
	serverIp = servIp;
	serverPort = servPort;
	currentFigure = figuresDict[metric];
	connect_manager(serverIp, serverPort, figuresDict[metric]);
	$('#' + metric).show();
}

/*
 * On plot change upldate metric and do any required changes liek resize on new selected plot.
 */
function updateMetric(selectComponent) {

	var newMetric = $(selectComponent).find(':selected').val();
	showMetric(newMetric);
	if (width != null && height != null) {
		waitOnConnection(currentFigure, 'resizePlot(currentFigure, width, height)', 200, 50);
	}
}

/*
 * Update html to show the new metric. Also connect to backend mplh5 for this new image.
 */
function showMetric(newMetric) {

	for (var key in figuresDict) {
		$('#' + key).hide();
	}
	currentFigure = figuresDict[newMetric];
	connect_manager(serverIp, serverPort, figuresDict[newMetric]);
	$('#' + newMetric).show();
}

/*
 * This is the callback that will get evaluated by an onClick event on the canvas through the mplh5 backend.
 */
function clickedDatatype(datatypeGid) {

	displayNodeDetails(datatypeGid);
}

/*
 * Update info on mouse over. This event is passed as a callback from the isocline python adapter.
 */
function hoverPlot(id, x, y, val) {

	document.getElementById('cursor_info_' + id).innerHTML = 'x axis:' + x + ' y axis:' + y + ' value:' + val;
}


function Isocline_MainDraw(groupGID, divId, width, height) {

	$('#' + divId).html('');
	$.ajax({
            type: "POST",
            url: '/burst/explore/draw_isocline_exploration/' + groupGID + '/' + width + '/' + height,
            success: function(r) {
                    $('#' + divId).html(r);
                },
            error: function(r) {
                displayMessage("Could not refresh with the new metrics.", "errorMessage");
	}});
}


