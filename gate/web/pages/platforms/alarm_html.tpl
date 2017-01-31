
%### INCLUDES ###
%from gate.tpl import checked, disabled


%### HTML ###
<td>
    <input type='checkbox' name="{{alarm['enable_name']}}" value="{{alarm['name']}}" 
    onclick='AdcAlarms()' {{checked(alarm['enable'])}} >
</td>

%if alarm['indeterminate1']:
    <script><!--
        $("input:checkbox[name='{{alarm['enable_name']}}'][value='{{alarm['name']}}']").prop('indeterminate', true);
    //--></script>
%end

%if alarm['value'] is None:
    %alarm_value = ''
%else:
    %alarm_value = alarm['value']
%end

<td>
    <input type='number' name="{{alarm['value_name']}}" value="{{str(alarm_value)}}"
    min="{{alarm['min_value']}}" max="{{alarm['max_value']}}" 
    step="{{str(alarm['units']['step'])}}" size='5' {{disabled(alarm['disabled'])}} >
</td>
