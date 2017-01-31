
%### INCLUDES ###
%import json

%from gate.tpl import selected, disabled


%### CONSTANTS ###
%MIN_LIST = dict()
%MAX_LIST = dict()

%for unit_name, unit_value in header['unit_list'].items():
    %MIN_LIST[unit_name] = unit_value.get_min(header['nodes'][0])
    %MAX_LIST[unit_name] = unit_value.get_max(header['nodes'][0])
%end


%### JS ###
<script><!--
var min_list_{{header['name']}} = {{!json.dumps(MIN_LIST)}};
var max_list_{{header['name']}} = {{!json.dumps(MAX_LIST)}};

function UpdateAlarmLimits_{{header['name']}}()
{
    %# Find what is currently selected
    var unit_name = $("#alarm_units_{{header['name']}}").val();
    console.log(unit_name);
    
    %# Find min/max
    var min_value = min_list_{{header['name']}}[unit_name];
    var max_value = max_list_{{header['name']}}[unit_name];
    
    %# console.log(min_list_{{header['name']}});
    %# console.log(min_value);
    %# console.log(max_list_{{header['name']}});
    %# console.log(max_value);
    
    %# Set min, max of those alarms depending on what is currently selected
    $("input[name='max_alarm_value_{{header['name']}}']").val('');
    $("input[name='min_alarm_value_{{header['name']}}']").attr('min', min_value);
    $("input[name='max_alarm_value_{{header['name']}}']").attr('min', min_value);
    
    $("input[name='min_alarm_value_{{header['name']}}']").val('');
    $("input[name='min_alarm_value_{{header['name']}}']").attr('max', max_value);
    $("input[name='max_alarm_value_{{header['name']}}']").attr('max', max_value);
}

//--></script>


%### HTML ###
<td><select name="alarm_units_{{header['name']}}" id="alarm_units_{{header['name']}}" onchange="UpdateAlarmLimits_{{header['name']}}()" {{disabled(header['disabled'])}} >
%for unit_name, unit_value in header['unit_list'].items():
    <option value='{{unit_name}}' {{selected(unit_value == header['alarm_units'])}} >
        {{unit_value['measuring_units']}}
    </option>
%end
</select></td>
