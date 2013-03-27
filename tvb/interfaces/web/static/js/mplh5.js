var canvas_socket = null;
var contexts = new Array();
 // holds the contexts for this page
var canvii = new Array();
var last_frames = new Array();
var last_id = 0;
var ztop = 0;
var base_port = 4567;
var management_socket = null;
var canvas_errors = new Array();
var ax_bb = new Array();
cursor_info = new Array();
frame_counter = new Array();
frame_start = new Array();

var zdiv = new Array();
var ldiv = new Array();



function change_cursor_info(id) {
     document.getElementById('cursor_info_' + id).innerHTML = "";
     cursor_info[id] += 1;
     if (cursor_info[id] > 1) {
         cursor_info[id] = 0;
     }
}

function exec_user_cmd(id, cmd_str) {
    //this command is sent only to close the blocker overlay if the user clicks on a figure(not on a button)
    if (cmd_str.indexOf("FAKE_COMMAND") == 18) {
        return;
    }

     var ret_str = "";
     try {
        ret_str = eval(cmd_str);
     } catch(err) { 
         ret_str = "user command failed: " + err;
     }
      try {
        sendMessage("<user_cmd_ret id='"+id+"' args='" + ret_str + "'>");
      } catch (err) { 
          displayMessage('error returning output of user cmd:' + err, 'errorMessage'); 
      }
}

function draw_frame(id) {
     try {
          if (frame_counter[id] == 0) { 
              frame_start[id] = new Date().getTime();
          }
          var c = contexts[id];
          // when in client mode we cannot zoom anyway...
          for (var i=0; i < ldiv[id].length; i++) 
              ldiv[id][i].style.display= "none";
          // hide any existing limit divs...
          ax_bb = new Array();
          eval(last_frames[id]); 
          frame_header();
          // execute the header. This will perform initial setup that is required (such as images) and then run frame_body..
          // we need a zoom limit div per axes
          for (var i=0; i < ax_bb.length; i++) {
               if (!(i in ldiv[id])) {
                    var nid = 'limit_div_' + i + '_' + id;  
                    var ndiv = ldiv[id][0].cloneNode(false);
                    ndiv.id = nid;
                     // fix the id
                    //ndiv.removeEventListener('mousedown', mouseDownLdiv, false);
                    ndiv.addEventListener('mousedown', function (e) {wrapClickCanvas(e,this);}, false);
                    document.getElementById('plot_canvas_' + id).appendChild(ndiv);
                    ldiv[id][i] = document.getElementById('limit_div_' + i + '_' + id); 
               } // we need a limit div for this axes
               ldiv[id][i].style.display = "inline";
               ldiv[id][i].style.left = canvii[id].offsetLeft + ax_bb[i][0] + "px";
               ldiv[id][i].style.top = canvii[id].offsetTop + ax_bb[i][1] + "px";
               ldiv[id][i].style.width = ax_bb[i][4] - ax_bb[i][0] + "px";
               ldiv[id][i].style.height = ax_bb[i][3] - ax_bb[i][1] + "px";
               frame_counter[id] += 1;
               if (frame_counter[id] > 30) { 
                    fps = (frame_counter[0] / (new Date().getTime() - frame_start[id]) * 1000);
                    if (cursor_info[id] == 1) document.getElementById('cursor_info_' + id).innerHTML = "FPS:" + fps;
                    frame_counter[id] = 0;
               }
          }
     } catch (err) {
         displayMessage(err, "errorMessage");
         canvas_errors.push("draw_frame(" + id + "): " + err);
     }
}

var last_manage = "";
    
function connect_manager(server_ip, server_port, id) {
    // create the contexts for our canvii
    cursor_info[id] = 0;
    frame_counter[id] = 0;
    frame_start[id] = 0;
    canvii[id] = document.getElementById('canvas_'+ id);
    contexts[id] = canvii[id].getContext('2d');
    zdiv[id] = document.getElementById('zoom_div_'+ id);
    ldiv[id] = new Array();
    ldiv[id][0] = document.getElementById('limit_div_0_'+ id);
    ldiv[id][0].addEventListener('mousedown', function (e) {clickCanvas(e, id, 0);}, false);

    if (window.MozWebSocket) {
        canvas_socket = new MozWebSocket('ws://' + server_ip + ':' + server_port + '/do');
    } else {
        canvas_socket = new WebSocket('ws://' + server_ip + ':' + server_port + '/');
    }
    document.getElementById('status_' + id).innerHTML = "Connecting to figure: " + id + "...";
    canvas_socket.onmessage = function(e) {
    								try {
	                                    document.getElementById('status_' + id).innerHTML = "Connected";
	                                    if (e.data.indexOf("/*exec_user_cmd*/") == 0) {
	                                        exec_user_cmd(id, e.data);
	                                    } else {
	                                        last_frames[id] = e.data;
	                                        draw_frame(id);
	                                    }
	                                }
	                                catch(err) {
	                                	displayMessage("Error encountered while updating image.", "errorMessage");
	                                }
                                    closeBlockerOverlay();
                                } 
    canvas_socket.onopen = function(e) {
                                    try{
                                        sendMessage("<register id='"+id+"'>");
                                        document.getElementById('status_' + id).innerHTML = "Register message sent ("+id+")";
                                    } catch (err) {
                                        displayMessage(err, "errorMessage");
                                    }
                              }
}

function sendMessage(msg) {
	showBlockerOverlay();
	canvas_socket.send(msg);
}

var allow_resize = true;
function resize_canvas(id, width, height) {
     if (allow_resize) {
          if (id >= 0) {
               canvii[id].width = width; 
               document.getElementById("button_menu_" + id).style.width = width + "px";
               canvii[id].height = height;
          }
     }
}


 // this style of event listener is an issue in Firefox 3.7. Will need to fix at some stage...
var native_w = new Array();
var native_h = new Array();
var zdraw = -1;
var resize = -1;
var startX = 0;
var startY = 0;
var stopX = 0;
var stopY = 0;
var rStartX = 0;
var rStartY = 0;

function wrapClickCanvas(e, ref) {
     var p = ref.id.split("_");
      // extract the figure and axes ids
     clickCanvas(e, p[3], p[2]);
}

function handle_user_event(arg_string, id) {
      try {
        sendMessage("<user_event id='"+id+"' args='" + id + "," + arg_string + "'>");
      } catch (err) {}
}

function handle_click(e, id) {
    try {
        var pc = document.getElementById('canvas_' + id);
        var pos = findPosition(pc);
        sendMessage("<click id='" + id + "' args='" + (e.pageX - pos[0]) +
            "," + (canvii[id].clientHeight - (e.pageY - pos[1])) + "," + (e.button + 1) + "'>");
        // we need coords based on 0,0 in bottom left corner...
    } catch (err) {}
}

/**
 * This method is used to find out where an element is on the page.
 *
 * In all browsers it's necessary to use the offsetTop and offsetLeft of the element.
 * These properties give the coordinates relative to the offsetParent of the element.
 * The script moves up the tree of offsetParents and adds the offsetTop and offsetLeft of each.
 * Eventually, regardless of the actual composition of the offsetParent tree,
 * this leads to the real coordinates of the element on the screen.
 *
 * @param obj the element for which we want to find the position.
 */
function findPosition(obj) {
    var currentLeft = 0;
    var currentTop = 0;
    if (obj.offsetParent) {
        do {
            //take into account the scroll
            currentLeft += obj.offsetLeft - $(obj).scrollLeft();
            currentTop += obj.offsetTop - $(obj).scrollTop();
        } while (obj = obj.offsetParent);
    }
    return [currentLeft, currentTop];
}


function clickCanvas(e,id,axes) {
     if (!e) {
        var e = window.event;
     }
      // e.button: 0 is left, 1 is middle, 2 is right.
     if ((e.button == 0) && (e.shiftKey == false)) {
          if (id > -1) {
              zoom_canvas_id = id;
          }
          var pc = document.getElementById('canvas_' + id);
          var pos = findPosition(pc);
          zdraw = axes;
          zdiv[id].style.width = 0;
          zdiv[id].style.height = 0;
          //the position of the div is absolute => compute it relative to its parent
          zdiv[id].style.top = e.pageY - pos[1] + "px";
          zdiv[id].style.left = e.pageX - pos[0] + "px";
          zdiv[id].style.display = "inline";
          // position the start of the zoom reticule
     }
     startX = e.pageX;
     startY = e.pageY;
     pause = true;
     return false;
}


/**
 * Used for starting the resize canvas operation.
 */
function clickSize(e, id) {
     var cr = document.getElementById('resize_div');
     var pcs = document.getElementById('canvas_' + id);
     var pos = findPosition(pcs);
     cr.style.top = pcs.offsetTop + "px";
     cr.style.left = pcs.offsetLeft+ "px";
     cr.style.width = (e.pageX- pos[0]) + "px";
     cr.style.height = (e.pageY- pos[1]) + "px";
     cr.style.display = "inline";
     rStartX = e.pageX- pos[0];
     rStartY = e.pageY- pos[1];
     resize = id;
     document.getElementById('status_'+ id).innerHTML = "Click size at " + rStartX + "," + rStartY;
     return false;
}

/**
 * Used for changing the size of the 'resize_div' div. This div is
 * used for changing the size of the canvas.
 */
function slideSize(e) {
     if (resize > -1) {
          var cr = document.getElementById('resize_div');
          var pcs = document.getElementById('canvas_' + resize);
          var pos = findPosition(pcs);
          cr.style.width = (e.pageX- pos[0]) + "px";
          cr.style.height = (e.pageY- pos[1]) + "px";
          document.getElementById('status_'+ resize).innerHTML = "Slide size to " + (e.pageX - rStartX) + "," + (e.pageY - rStartY);
     } 
     return false;
}

function do_resize(id, w, h) {
      try {
        sendMessage("<resize id='"+id+"' args='" + w + "," + h + "'>");
      } catch (err) {
          displayMessage("Error when resizing!", "errorMessage");
      }
}

/**
 * Called on 'mouseup' event.
 * Sets the size of the 'resize_div' div to the canvas.
 */
function outSize() {
     if (resize > -1) {
          var cr = document.getElementById('resize_div');
          do_resize(resize, cr.style.width.replace("px",""), cr.style.height.replace("px",""));
          cr.style.display = "none";
     }
     resize = -1;
     zdraw = -1;
}

function close_plot(id) {
     sendMessage("<close id='"+id+"' args=''>");
     stop_plotting(id);
     canvii[id].width = canvii[id].width;
}

function go_home(id) {
     sendMessage("<home id='"+id+"' args=''>");
}

function maximise(id) {
    pcs = document.getElementById('main');
    var w = pcs.clientWidth; 
    var h = pcs.clientHeight - 20;
    resize = id;
    do_resize(id, w, h);
    resize = -1;
}

var zoom_canvas_id = 0;

function zoom_in(id, axes) {
     var atop = 0;
     var aleft = 0;
     if (document.getElementById("anchor_div") != null) {
          an = document.getElementById("anchor_div");
          atop = an.offsetTop;
          aleft = an.offsetLeft;
     }
     var plc = document.getElementById("canvas_" + id);
     var pos = findPosition(plc);
     var zoom_coords = axes + "," + (startX - (pos[0] + aleft)) + "," + (canvii[id].height - (stopY - (pos[1] + atop))) + "," + (stopX - (pos[0] + aleft)) + "," + (canvii[id].height - (startY - (pos[1] + atop)));
     sendMessage("<zoom id='"+id+"' args='" + zoom_coords + "'>");
     startX = stopX = startY = stopY = 0;
     zdiv[id].style.width = "0px";
     zdiv[id].style.height = "0px";
     zdiv[id].style.display = "none";
}

function releaseCanvas(e,id) {
     if (!e) {
        var e = window.event;
     }
     stopX = e.pageX;
     stopY = e.pageY;
     if (zdraw > -1 && ((stopX-startX)>5) && ((stopY-startY)>5)) { 
         zoom_in(zoom_canvas_id, zdraw);
     } else {
        // not in zdraw (or zoomed areas less than 5x5) so normal click
        handle_click(e,id);
        zdiv[id].style.display = "none";
     }
     zdraw = -1;
     pause = false;
     return false;
}

function slideCanvas(e,id,axes) {
     if (!e) var e = window.event;
     if (zdraw > -1)  {
        zdiv[id].style.width = e.pageX - startX + "px";
        zdiv[id].style.height = e.pageY - startY + "px";
     } 
     if (cursor_info[id] == 0) {
        document.getElementById('cursor_info_' + id).innerHTML = "Cursor at: " + e.pageX + "," + e.pageY;
     }
     return false;
 }
 
document.addEventListener("mousemove", slideSize, false);
document.addEventListener("mouseup", outSize, false);
 


