
%### INCLUDES ###
%import string

%from gate.main import system_settings, pages
%from gate.common import LIVE_NODES_NUMBER
%from gate.tpl import checked, selected


%### CONSTANTS ###
%cookie = pages.get_cookie()
%if not defined('group'):
    %group = pages.get_group()
%end


%### HTML ###
<table class="main_table" >
    %# Platform Name
    %platform_name = group['platform']
    <input type='hidden' name='platform' value="{{platform_name}}" >
    
    %## BODY ##
    <thead>
        <div id="form" >
            %# Node Names #
            <tr>
                %for index in range(-1, LIVE_NODES_NUMBER):
                    <th id="node{{index}}" ></th>
                %end
            </tr>
            %# Node Bar Graphs #
            <tr>
                %for index in range(-1, LIVE_NODES_NUMBER):
                    <td><div id="chart{{index}}" style="width:98px;height:500px;margin:15px 0px 15px 0px;" ></div></td>
                    %#<td id="chart{{index}}" style="width:98px;height:500px;" ></td>
                %end
            </tr>
        </div>
    </thead>
    <tbody>
        %# Table with alternative units #
        %live_headers = group.live_headers()
        %for header_name, header in live_headers.items():
            %for unit_name, unit_value in header.unit_list.items():
                %if unit_name in group.live_table_units(cookie, header).keys():
                    <tr>
                        <td>{{header['name']}}, {{unit_value['measuring_units']}}</td>
                        %for index in range(0, LIVE_NODES_NUMBER):
                            <td id="{{header_name}}_{{unit_name + str(index)}}"></td>
                        %end          
                    </tr>
                %end
            %end
        %end
    </tbody>
    
    %"""
    %if system_settings.manual_log:
        <tfoot><tr>
            %for index in range(-1, LIVE_NODES_NUMBER):
                <th id="node{{index}}" ></th>
                
                <td>
                    <form action='/{{URL}}' method='post' >
                        <input type='hidden' name='net_addr' value="{{node['net_addr']}}" >
                        <button type='submit' name='action_method' value='manual_log'>Log</button>
                    </form>
                </td>
            %end
        </tr></tfoot>
    %end
    %"""
    
</table>
