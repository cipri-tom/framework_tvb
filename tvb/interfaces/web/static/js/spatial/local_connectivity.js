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

function displayGradientForThePickedVertex() {
	/**
	 * Displays a gradient on the surface used by the selected local connectivity.
	 */
    if (TRIANGLE_pickedIndex >= 0) {
        if (!LEG_legendBuffers.length) LEG_generateLegendBuffers();         // only generate them on first pick
        var selectedLocalConnectivity = $("select[name='existentEntitiesSelect']").val();
        if (selectedLocalConnectivity == undefined || selectedLocalConnectivity == "None" ||
            selectedLocalConnectivity.trim().length == 0) {
            LCONN_PICK_drawDefaultColorBuffers();
            return;
        }
        var url = '/spatial/localconnectivity/compute_data_for_gradient_view?local_connectivity_gid=';
        url += selectedLocalConnectivity + "&selected_triangle=" + TRIANGLE_pickedIndex;
        $.ajax({
            async:false,
            type:'POST',
            url:url,
            success: LCONN_PICK_updateBrainDrawing
        });
        TRIANGLE_pickedIndex = GL_NOTFOUND;             // disable data retrieval until next triangle pick
    }
}

function LCONN_disableView(message) {
	/*
	 * Disable the view button in case we don't have some existing entity loaded
	 */
	var stepButton = $("#lconn_step_2");
	stepButton[0].onclick = null;
	stepButton.unbind("click");
	stepButton.click(function() { displayMessage(message, 'infoMessage'); return false; });
	stepButton.addClass("action-idle");
}

function LCONN_disableCreate(message) {
	/*
	 * Disable the create button and remove action in case we just loaded an entity.
	 */
	var stepButton = $('#lconn_step_3');
	stepButton[0].onclick = null;
	stepButton.unbind("click");
	stepButton.click(function() { displayMessage(message, 'infoMessage'); return false; });
	stepButton.addClass("action-idle");
}


function LCONN_enableCreate() {
	/*
	 * Enable the create button and add the required action to it in case some parameters have changed.
	 */
	var stepButton = $('#lconn_step_3');
	stepButton[0].onclick = null;
	stepButton.unbind("click");
	stepButton.click(function() { createLocalConnectivity(); return false; });
	stepButton.removeClass("action-idle");
}


