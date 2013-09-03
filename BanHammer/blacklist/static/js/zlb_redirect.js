var oTable
var gaiSelected = []

$(document).ready(function() {
    oTable = $('#virtualservers').dataTable( {
        "aaSorting": [[ 1, "desc" ]],
        "aoColumns": [
	      { "bSortable": false },
	      null,
	      null,
	      null,
	      null,
	      null,
	      null,
	      null,
	      null,
	    ],
	    "fnRowCallback": function( nRow, aData, iDisplayIndex ) {
			if ( jQuery.inArray(aData[0], gaiSelected) != -1 )
			{
				$(nRow).addClass('row_selected');
			}
			return nRow;
		},
    } );
} );

$('#virtualservers tbody tr').live('click', function () {
		var aData = oTable.fnGetData( this );
		var iId = aData[0];
		
		if ( jQuery.inArray(iId, gaiSelected) == -1 )
		{
			gaiSelected[gaiSelected.length++] = iId;
		}
		else
		{
			gaiSelected = jQuery.grep(gaiSelected, function(value) {
				return value != iId;
			} );
		}
		
		if ($(this).hasClass('row_selected')) {
			$('#id_select_'+$(this).attr('id')).prop("checked", false);
			$(this).removeClass('row_selected');
		}
		else {
			if ($(this).hasClass('other_protection'))
				confirmation = confirm('This virtual server has a non-banhammer protection class. Do you really want to disable this class on this virtual server?')
			if ($(this).hasClass('confirmation'))
				confirmation = confirm($('#flag'+$(this).attr('id')).text())
			else
				confirmation = true
			if (confirmation) {
				$('#id_select_'+$(this).attr('id')).prop("checked", true);
				$(this).addClass('row_selected');
			}
		}
} );
