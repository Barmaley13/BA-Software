
%### INCLUDES ###
%import copy

%from bottle import template

%from gate.main import pages, users
%from gate.strings import ADC_DEFAULT_VALUES
%from gate.tpl import selected, checked, hidden


%### CONSTANTS ###
%if not defined('url'):
    %url = '/' + pages.url()
%end
%ADDRESS = pages.get_cookie('nodes_subpage')
%constants_js, constants_html = pages.platforms.constants_js_html(ADDRESS)


%### JS ###
<script><!--
    function validate_adc_update(form)
    {
        {{!constants_js}}
        
        %# Disable Multiples (if needed)
        $("input[value='Multiple']").each(function () {
            if ($(this).is(':visible'))
            {
                $(this).prop('disabled', true); 
                
                var constant_name = $(this).attr('name').replace('-Multiple', '');
                $("input[name='" + constant_name + "']").prop('disabled', true);
            }
        });
        
        %# $("input[value='Multiple']").prop('disabled', true);
        
        $("select[id$='Multiple']").each(function () {
            if ($(this).find(":selected").text() == 'Multiple')
            {
                $(this).prop('disabled', true); 
            }
        });
        
        %# Test that JS works properly
        %# alert('Success!')
        return true;
    }
    
    function SelectTank()
    {
        var tank_type = $("select[name$='tank_type']");
        var tank_type_val = tank_type.find(":selected").val();
        //console.log(tank_type_val);
        
        var data_field = tank_type.attr('name').split('_')[0];
        //console.log(data_field);
        
        if (tank_type_val == "Constant")
        {
            $("#" + data_field + "_area").show();
            $("#" + data_field + "_diameter").hide();
            $("#" + data_field + "_length").hide();
        }
        else if (tank_type_val == "Vertical")
        {
            $("#" + data_field + "_area").hide();
            $("#" + data_field + "_diameter").show();
            $("#" + data_field + "_length").hide();
        }
        else if(tank_type_val == "Horizontal")
        {
            $("#" + data_field + "_area").hide();
            $("#" + data_field + "_diameter").show();
            $("#" + data_field + "_length").show();
        }
        else
        {
            $("#" + data_field + "_area").hide();
            $("#" + data_field + "_diameter").hide();
            $("#" + data_field + "_length").hide();
        }    
    }
//--></script>


%### HTML ###
<form action='{{url}}' onsubmit='return validate_adc_update(this)' method='post' ><fieldset>
    %if len(ADDRESS['nodes']) == 0:
        {{!template('display_warnings', messages=ADC_DEFAULT_VALUES)}}
    %end
    
    %# Action Type
    <input type='hidden' name='action_method' value='update_adc' >

    {{!constants_html}}
    
    %# Save, Reset, Cancel Buttons
    %if users.check_access('write'):
        <p><span class="float_right">
            <input type='submit' name='submit' value='Save' >
    %else:
        <p><span class="float_right">
    %end
        <input type='button' value='Cancel' onclick="GoCancel()" >
    </span></p>

</fieldset></form>

%if 'jowa-1203' in ADDRESS['platform']:
    <script><!--
        $("select[name$='tank_type']").change(function(){SelectTank()});
        SelectTank();
    //--></script>
%end
