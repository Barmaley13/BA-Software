
%### INCLUDES ###
%from gate.tpl import selected


%### HTML ###
<select name="{{header['internal_name']}}" onchange="SensorCode('{{header['internal_name']}}')" >
%for _header in header_group.values():
    <option value='{{_header['sensor_code']}}' {{selected(_header['selected'])}} >
        {{_header['name']}}
    </option>
%end
</select>
