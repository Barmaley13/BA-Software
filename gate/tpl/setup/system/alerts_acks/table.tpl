
%### INCLUDES ###
%from bottle import template

%from gate.main import pages
%from gate.strings import NO_ACTIVE_PLATFORMS
%from gate.tpl import selected


%### CONSTANTS ###
%ADDRESS = pages.get_cookie()
%ACTIVE_PLATFORMS = pages.platforms.active_platforms()


%### HTML ###
<p><span class="float_right">
    <input type="button" onclick="location.href='/{{pages.url('system_home')}}'" value="Back">
</span></p>

%if not len(ACTIVE_PLATFORMS):
    {{!template('display_warnings', messages=NO_ACTIVE_PLATFORMS)}}
%else:
    <table class='hor-minimalist-b'>
        %# Static Header Names
        <thead><tr>
            %# Select field for user id
            %if len(ACTIVE_PLATFORMS) > 1:
                <th scope='col'>Platform</th>
            %end
            <th scope='col'>Group</th>
            <th scope='col'>Node</th>
        </tr></thead>

        %# Table Data
        <tr>
            %# Platforms
            %if len(ACTIVE_PLATFORMS) > 1:
                <td>
                    <select id='platform' onchange='GoForward()' >
                        %for platform_name, platform in ACTIVE_PLATFORMS.items():
                            %selected_platform = False
                            %if 'platform' in ADDRESS:
                                %selected_platform = bool(ADDRESS['platform'] == platform_name)
                            %elif len(ACTIVE_PLATFORMS):
                                %selected_platform = bool(ACTIVE_PLATFORMS.keys()[0] == platform_name)                  
                            %end
                            <option value='{{platform_name}}' {{selected(selected_platform)}} >{{platform['name']}}</option>
                        %end
                    </select>
                </td>
            %else:
                <input type='hidden' id='platform' value="{{ACTIVE_PLATFORMS.keys()[0]}}" >
            %end
            
            %# Groups
            <td>
                <select id='group' onchange='GoForward()' >
                    <option value=''>All Groups</option>
                    %platform = None
                    %if 'platform' in ADDRESS:
                        %platform = pages.platforms.platform(ADDRESS)
                    %elif len(ACTIVE_PLATFORMS):
                        %platform = ACTIVE_PLATFORMS.values()[0]
                    %end
                    
                    %if platform is not None:
                        %for group_name, group in platform.groups.items():
                            %if group_name != 'inactive_group':
                                %selected_group = bool('group' in ADDRESS and ADDRESS['group'] == group_name)
                                <option value='{{group_name}}' {{selected(selected_group)}} >{{group['name']}}</option>
                            %end
                        %end
                    %end
                </select>
            </td>
            
            %# Nodes
            <td>
                <select id='node' onchange='GoForward()' >
                %# Can potentially make this multiple selection!
                %#<select name='nodes' onchange='GoForward()' multiple='multiple' >
                    <option value=''>All Nodes</option>
                    %if 'group' in ADDRESS:
                        %group = pages.platforms.group(ADDRESS)
                        %for net_addr, node in group.nodes.items():
                            %selected_node = bool('nodes' in ADDRESS and net_addr in ADDRESS['nodes'])
                            <option value='{{net_addr}}' {{selected(selected_node)}} >{{node['name']}}</option>
                        %end
                    %end
                </select>
            </td>
            
        </tr>
    </table>
%end
