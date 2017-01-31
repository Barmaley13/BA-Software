
%### INCLUDES ###
%from gate.tpl import checked


%### HTML ###
<td>
    <input type='checkbox' name="{{enable['key']}}" value="{{enable['name']}}" 
    onclick="AdcEnables('{{enable['key']}}', '{{enable['name']}}')" {{checked(enable['check'])}} >
</td>

%if enable['indeterminate']:
    <script><!--
        $("input:checkbox[name='{{enable['key']}}'][value='{{enable['name']}}']").prop('indeterminate', true);
    //--></script>
%end
