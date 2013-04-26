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
var serverIp = null;
var serverPort = null;
var figuresDict = null;
var currentFigure = null;
var width = null;
var height = null;

function resizeFigures(newWidth, newHeight) {
	/*
	 * If for some reason we change the plot size for one of the images,
	 * store it so we can resize all other plots on the onchange event.	
	 */ 
	width = newWidth;
	height = newHeight;
	resizePlot(currentFigure, width, height);
}

function resizePlot(id, width, height) {
	/*
	 * Do the actual resize, given a figure id, width and height.
	 */
	if (currentFigure != null) {
		resize = id;
	    do_resize(currentFigure, width, height);
	    resize = -1;
	}
}

function initISOData(metric, figDict, servIp, servPort) {
	/*
	 * Store all needed data as js variables so we can use later on.
	 */
	figuresDict = $.parseJSON(figDict);
	serverIp = servIp;
	serverPort = servPort;
	currentFigure = figuresDict[metric];
	connect_manager(serverIp, serverPort, figuresDict[metric]);
	$('#' + metric).show();
}

function updateMetric(selectComponent) {
	/*
	 * On plot change upldate metric and do any required changes liek resize on
	 * new selected plot.
	 */
	var newMetric = $(selectComponent).find(':selected').val();
	showMetric(newMetric);
	if (width != null && height != null) {
		waitOnConnection(currentFigure, 'resizePlot(currentFigure, width, height)', 200, 50);
	}
}

function showMetric(newMetric) {
	/*
	 * Update html to show the new metric. Also connect to backend mplh5 for
	 * this new image.
	 */
	for (var key in figuresDict) {
		$('#' + key).hide();
	}
	currentFigure = figuresDict[newMetric];
	connect_manager(serverIp, serverPort, figuresDict[newMetric]);
	$('#' + newMetric).show();
}

function clickedDatatype(datatypeGid) {
	/*
	 * This is the callback that will get evaluated by an onClick event on the canvas
	 * through the mplh5 backend.
	 */
	displayNodeDetails(datatypeGid);
}


function hoverPlot(id, x, y, val) {
	/*
	 * Update info on mouse over. This event is passed as a callback from the isocline python adapter.
	 */
	document.getElementById('cursor_info_' + id).innerHTML = 'x axis:' + x + ' y axis:' + y + ' value:' + val;
}

