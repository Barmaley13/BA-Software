
%### INCLUDES ###
%from bottle import template

%from gate.main import pages, users
%from gate.tpl import selected


%### CONSTANTS ###
%URL = pages.url()
%REMOVE_ENABLE = users.check_access('write')

%if not defined('group'):
    %group = pages.get_group()
%end


%### JS ###
<script><!--
function validate_remove(form)
{
    var removeConfirm = confirm("Are you sure you want to remove this Log?");
    return removeConfirm;
}

//--></script>


%### HTML ###
%# Log Export Options #
<h3>Log Export Menu</h3>
<table class="hor-minimalist-b" >
    %# Export Headers
    <thead>
        <tr>
            <th>Select</th>
            <th>Export Units</th>
        </tr>
    </thead>
    %# Export Data
    <tbody>
        <tr>
            <td>
                <form action='/{{URL}}' id='log_export' method='post' >
                    %# Action
                    <input type='hidden' name='action_method' value='start_log_export' >
                    <input type='hidden' name='ajax' value='true' >
                    <select name="net_addr" onchange='GetLogData(false, true)' >
                        %export_net_addr = None
                        %cookie = pages.get_cookie()
                        %if 'export_net_addr' in cookie:
                            %export_net_addr = cookie['export_net_addr']
                        %end
                        %for node in group.nodes.values():
                            <option value="{{node['net_addr']}}"
                            {{selected(node['net_addr'] == export_net_addr)}} >
                                {{node['name']}}
                            </option>
                        %end
                    </select>
                </form>
            </td>
            <td>{{!template('table_units', group=group, page_type='log')}}</td>
            <td><input type='button' value='Export Log' onclick="SoftwareOverlay($('#log_export').serialize())" ></td>
            %if REMOVE_ENABLE:
                <td>
                    <form action='/{{URL}}' onsubmit='return validate_remove(this)' method='post' >
                        <button type='submit' name='action_method' value='remove_log'>Delete Log</button>
                    </form>
                </td>
            %end
        </tr>
    </tbody>
</table>
