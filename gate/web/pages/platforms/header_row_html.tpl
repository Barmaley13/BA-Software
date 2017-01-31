
%### INCLUDES ###
%from gate.tpl import hidden

%### HTML ###
<tr {{!hidden(hide_header)}}>
    %# Name
    <td>{{!header_name}}</td>
    %# Alarms, Enables
    {{!header_html}}
</tr>
