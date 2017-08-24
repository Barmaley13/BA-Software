
%### INCLUDES ###
%from bottle import template

%from gate.main import manager, pages
%from gate.strings import NO_ACTIVE_NODES
%from gate.tpl import selected


%### HTML ###
%page_urls = pages.platforms.compose_group_urls()
%if not len(page_urls):
    {{!template('display_warnings', messages=NO_ACTIVE_NODES)}}
%else:
    <h3>Group Statistics</h3>
    %group_title = None
    %for page_url in page_urls:
        %group = pages.platforms.fetch_group_from_url(page_url['url'])
        
        %if len(group.nodes):
            %# Platform and Group Names
            %platform_name = group['platform']
            %group_name = group['internal_name']
            <input type='hidden' name='platform' value='{{platform_name}}' >
            <input type='hidden' name='{{platform_name}}_group' value='{{group_name}}' >
            
            %## Group Title ##
            %active_platforms = pages.platforms.active_platforms()
            %if len(active_platforms) == 1:
                %new_group_title = group['name']
            %else:
                %new_group_title = pages.platforms[platform_name]['name'] + ' - ' + group['name']
            %end
            
            %if group_title != new_group_title:
                %group_title = new_group_title
                <p>{{group_title}}</p>
            %end

            %## Group Data ##
            <table class="hor-minimalist-b" >
                %# Table Headers #
                <thead><tr>
                    <th></th>
                    %for node in group.nodes.values():
                        <th>{{node['name']}}</th>
                    %end
                </tr></thead>
                
                %# Table Data #
                <tfoot>
                    %diagnostics_headers = group.read_headers('diagnostics')
                    %for header_name, header in diagnostics_headers.items():
                        <input type='hidden' name='{{platform_name}}_{{group_name}}_header' value='{{header_name}}' >
                        <tr>
                            %cookie = pages.get_cookie()
                            %live_units = group.units(cookie, 'live', header_name)
                            <td>{{header['name']}}, 
                                <select name='{{platform_name}}_{{group_name}}_{{header_name}}_units' onchange="GetDiagnostics()" >
                                    %for unit_name, unit_value in header.unit_list.items():
                                        <option value="{{unit_name}}" {{selected(unit_name == live_units['internal_name'])}} >
                                            {{unit_value['measuring_units']}}
                                        </option>
                                    %end
                                </select>
                            </td>
                            %for node in group.nodes.values():
                                %current_value = live_units.get_string(node)
                                <td>{{current_value}}</td>
                            %end                
                        </tr>
                    %end
                </tfoot>
            </table>
        %end
    %end

    <h3>System Statistics</h3>
    <table class="hor-minimalist-b" >
        <tfoot>
            %platform_name = 'system'
            %group_name = 'system'
            <input type='hidden' name='platform' value='{{platform_name}}' >
            <input type='hidden' name='{{platform_name}}_group' value='{{group_name}}' >
            
            %diagnostics_headers = manager.read_headers('diagnostics')
            %for header_name, header in diagnostics_headers.items():
                <input type='hidden' name='{{platform_name}}_{{group_name}}_header' value='{{header_name}}' >
                <tr>
                    %cookie = pages.get_cookie()
                    %live_units = header.units(cookie, 'live')
                    <td>{{header['name']}}, 
                        <select name='{{platform_name}}_{{group_name}}_{{header_name}}_units' onchange="GetDiagnostics()" >
                            %for unit_name, unit_value in header.unit_list.items():
                                <option value='{{unit_name}}' {{selected(unit_name == live_units['internal_name'])}} >
                                    {{unit_value['measuring_units']}}
                                </option>
                            %end
                        </select>
                    </td>
                    %current_value = live_units.get_string(manager)
                    <td>{{current_value}}</td>
                </tr>
            %end
        </tfoot>
    </table>

%end
