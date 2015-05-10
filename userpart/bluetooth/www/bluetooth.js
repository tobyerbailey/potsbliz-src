$(document).ready(function () {

	$('#li-speeddial').after('<li><a href="#tabs-bluetooth">Bluetooth</a></li>');
	$('#tabs-speeddial').after('<div id="tabs-bluetooth"><div id="BluetoothContainer"></div><br /><div><form id="discovery_form"><input type="checkbox" id="DiscoveryCheckbox" name="discovery"><label for="discovery" id="discovery_label">Search new devices</label></form></div></div>');

    $('#BluetoothContainer').jtable({
        title: '&nbsp;',
        jqueryuiTheme: true,
        actions: {
            listAction:   '/plugin/bluetooth/bluetooth.py/list',
            deleteAction: '/plugin/bluetooth/bluetooth.py/delete'
        },
        fields: {
            device: {
                key: true,
                list: false
            },
            name: {
                title: 'Device',
	          	width: '99%',
            },
            paired: {
	          	display: function (data) {
	          		if (!data.record.paired) {
	          			return '<input type="submit" onclick="pairDevice(\'' + data.record.device + '\');" value="Connect ..." />';
	          		}
                }
            },
            connected: {
	          	display: function (data) {
	          		if (data.record.connected) {
                		return '<a href="javascript:;" title="Disconnect" onclick="disconnectDevice(\'' + data.record.device + '\');"><img src="/images/bluetooth-active.png" alt="Connected" width="12" height="16" /></a>';
	          		}
	          		else {
                		return '<a href="javascript:;" title="Try to Connect" onclick="connectDevice(\'' + data.record.device + '\');"><img src="/images/bluetooth-inactive.png" alt="Disconnected" width="12" height="16" /></a>';
                    }
                }
            },
        }
    });
    
    $('#BluetoothContainer').jtable('load');
    
    var discovery_timeout;         
    $('#discovery_form :checkbox').change(function() {
      if ($('#DiscoveryCheckbox').is(':checked')) {
    	$.ajax( {
		  url: "/plugin/bluetooth/bluetooth.py/start_discovery",
		  success: function(info) {
        	$.ajax( {
  			  url: "/plugin/bluetooth/bluetooth.py/get_discoverable_timeout",
			  dataType: "json",
  			  success: function(data) {
  			    // checking the Discovering flag always returns true
  			    // ==> uncheck checkbox after timeout
				discovery_timeout = setTimeout(function() {
					$('#DiscoveryCheckbox').prop('checked', false);
				}, data.DiscoverableTimeout * 1000);
			  }
		    });
			alert('Make your Bluetooth device visible!');
		  },
		  error: function(info) {
			//alert('Discovery start failed!');
			$('#DiscoveryCheckbox').prop('checked', false);
		  },
	    });
      }
      else {
		clearTimeout(discovery_timeout);
    	$.ajax( {
		  url: "/plugin/bluetooth/bluetooth.py/stop_discovery",
		  // errors occur quite often: we silently ignore them here
		  //error: function(info) {
			//alert('Discovery stop failed!');
		  //},
	    });
      }    
    });
    
	// reload bluetooth info periodically if bluetooth tab is selected
	setInterval(function() {
		if ($('#Tabs').tabs('option', 'selected') == 1) {
			// load list
			$('#BluetoothContainer').jtable('load');
		}
	}, 3000);

    // let label blink while discovery is active 
    setInterval(function() {
      var label = $('#discovery_label');
      if ($('#DiscoveryCheckbox').is(':checked')) {
        if (label.css('visibility') == 'hidden') {
          label.css('visibility', 'visible');
        }
        else {
          label.css('visibility', 'hidden');
        }
      }
      else {
        label.css('visibility', 'visible');          
      }    
    }, 500);
});

function pairDevice(device) {
  	//alert('Trying to pair with ' + device);

  	var dataString = 'device=' + device;
  	//alert (dataString);return false;
	$.ajax({
		type: "POST",
		url: "/plugin/bluetooth/bluetooth.py/pair",
		data: dataString,
		dataType: "json",
		success: function(response) {
			alert('Pairing done.');
		},
		error: function (xhr, ajaxOptions, thrownError) {
    				alert('Error: ' + xhr.status + ' - ' + thrownError);
  		},
	});
}

function connectDevice(device) {
	$.ajax({
		type: "POST",
		url: "/plugin/bluetooth/bluetooth.py/connect",
		data: 'device=' + device,
		dataType: "json",
	    success: function(response) {
	      if (response.Result != 'OK') {
		      alert('Cannot establish bluetooth connection.');
		      //alert(response.Message);
	      }
	    },
	});
}

function disconnectDevice(device) {
	$.ajax({
		type: "POST",
		url: "/plugin/bluetooth/bluetooth.py/disconnect",
		data: 'device=' + device,
		dataType: "json",
	});
}
    