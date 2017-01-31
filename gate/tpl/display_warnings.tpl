
%### INCLUDES ###
%from gate.tpl import hidden

%### HTML ###
<table id='display_warnings' {{!hidden(not defined('messages'))}} >
    <tr>
        <td><small><b>Warnings:</b></small></td>
        <td>
            <textarea id='display_warnings_html' rows='2' cols='100'>
                %if defined('messages'):
%# Looks funky but that is the easiet way to align text properly in the textarea
{{!messages}}
                %end
            </textarea>
        </td>
    </tr>
</table>
