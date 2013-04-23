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

function initISOData(metric, figDict, servIp, servPort) {
	figuresDict = $.parseJSON(figDict);
	serverIp = servIp;
	serverPort = servPort;
	connect_manager(serverIp, serverPort, figuresDict[metric]);
	$('#' + metric).show();
}

function updateMetric(selectComponent) {
	var newMetric = $(selectComponent).find(':selected').val();
	for (var key in figuresDict) {
		$('#' + key).hide();
	}
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
	document.getElementById('cursor_info_' + id).innerHTML = 'x axis:' + x + ' y axis:' + y + ' value:' + val;
}

