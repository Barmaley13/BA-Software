
%### INCLUDES ###
%import json

%from bottle import template

%from gate.main import system_settings, pages
%from gate.tpl import checked


%### CONSTANTS ###
%URL = pages.url()
%cookie = pages.get_cookie()


%### HTML ###
%# Display Select #
<table class="hor-minimalist-b" >
    %# Platform Name
    %platform_name = group['platform']
    <input type='hidden' name='platform' value="{{platform_name}}" >
    
    %# Header Names
    <thead><tr>
        %if len(group.nodes):

            %#<th scope='col'>Select</th>
            <th scope='col'>Name</th>
            <th scope='col'>MAC</th>
        
            {{!template('page_controls', group=group, page_type='log')}}            
        %end
    </tr></thead>

    %# Header Data
    <tbody>
    %log_headers = group.log_headers()
    %selected_nodes = group.log_header(cookie)
    %for node in group.nodes.values():
        <tr>
            <input type='hidden' name='net_addr' value="{{node['net_addr']}}" >
            <td>{{node['name']}}</td>
            <td>{{node['mac']}}</td>          
            
            %for header_name, header in log_headers.items():
                <td>
                    %selected_headers = {}
                    %if node['net_addr'] in selected_nodes:
                        %selected_headers = selected_nodes[node['net_addr']]
                    %end
                
                    %if header.enables(node, 'log_enables'):
                        %check_mark = bool(header_name in selected_headers.keys())
                        <input type='checkbox' name="log_{{node['net_addr']}}"
                        value="{{header_name}}" onclick="GetLogData()" {{checked(check_mark)}} >
                    %end
                </td>
            %end
            
            %if system_settings.manual_log:
                <td>
                    <form action='/{{URL}}' method='post' >
                        <input type='hidden' name='net_addr' value="{{node['net_addr']}}" >
                        <button type='submit' name='action_method' value='manual_log'>Log</button>
                    </form>
                </td>
            %end

        </tr>
    %end
    </tbody>
</table>
