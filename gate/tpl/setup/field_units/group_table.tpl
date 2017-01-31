
%### INCLUDES ###
%from gate.main import system_settings, pages, users
%from gate.tpl import checked, disabled


%### CONSTANTS ###
%ADDRESS = pages.get_cookie()

%PLATFORM = None
%if not defined('platform'):   
    %if 'platform' in ADDRESS:
        %PLATFORM = pages.platforms.platform(ADDRESS)
    %else:
        %active_platforms = pages.platforms.active_platforms()
        %if len(active_platforms) == 1:
            %PLATFORM = active_platforms.values()[0]
        %end
    %end
%else:
    %PLATFORM = platform
%end


%### FUNCTIONS ###
%def generate_buttons():
    %if not defined('platform'):
        <p>
            %if users.check_access('write') and PLATFORM['platform'] != 'virgins':
                <input type='button' value='Create New Group' onclick="NewGroup()" />
            %end        
            %if len(pages.platforms.active_platforms()) > 1:
                <span class="float_right">
                    <input type='button' value='Back' onclick="GoBack()" >
                </span>
            %end
        </p>
    %end
%end


%### HTML ###
%if PLATFORM is not None:
    %if system_settings.name == 'jowa':
        %generate_buttons()
    %end
    
    <table class='hor-minimalist-b'>
        %# Static Header Names #
        <thead><tr>
            %# Select Field for id
            %if not defined('platform'):
                <th scope='col'>Select</th>
            %end
            <th scope='col'>Name</th>
            <th scope='col'>Platform</th>
            <th scope='col'>Number of Field Units</th>              
        </tr></thead>

        <input type='hidden' name='platform' value="{{PLATFORM['platform']}}" >
        
        %# Table Data #
        %for group_name, group in PLATFORM.groups.items():
            <tr>
                %if not defined('platform'):
                    <td>
                        <input type='radio' name='group' value="{{group_name}}" onchange="GoForward()"
                        {{checked('group' in ADDRESS and ADDRESS['group'] == group_name)}} >
                    </td>
                %end
                <td>{{group['name']}}</td>
                <td>{{group['platform']}}</td>
                <td>{{len(group.nodes)}}</td>
            </tr>
        %end
    </table>

    %if system_settings.name != 'jowa':
        %generate_buttons()
    %end
%end
