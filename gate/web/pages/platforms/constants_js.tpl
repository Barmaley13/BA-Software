
%### HTML ###
%constant_name = constant['data_field'] + '_' + constant['internal_name']
if (
%if value is None:
    form.{{constant_name}}.value != '' &&
    form.{{constant_name}}.value != null &&
%end
    (form.{{constant_name}}.value < {{constant['min_value']}} ||
    form.{{constant_name}}.value > {{constant['max_value']}}) &&
    $("input[name='{{constant_name}}']").is(':visible'))
    {
        // console.log($("input[name='{{constant_name}}']").is(':visible'));
        alert("{{constant['name']}} has to be in the range of "
            + "{{constant['min_value']}} to {{constant['max_value']}} {{constant['measuring_units']}}");
        form.{{constant_name}}.focus();
        return false;
    }
%if multiple_allowed is False:
    else if ($("input[name='{{constant_name}}-Multiple']").is(':visible'))
    {
        alert("{{constant['name']}} is not allowed to have multiple values! Try setting sensor parameters for the selected field units individually!");
        form.{{constant_name}}.focus();
        return false;
    }
%end