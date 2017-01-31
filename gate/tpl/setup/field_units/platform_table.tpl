
%### INCLUDES ###
%from gate.main import pages
%from gate.tpl import checked


%### CONSTANTS ###
%ADDRESS = pages.get_cookie()


%### HTML ###
%if len(pages.platforms.select_nodes('ALL')) > 0:
    <table class='hor-minimalist-b'>
        %# Static Header Names #
        <thead><tr>
            %# Select Field for id
            <th scope='col'>Select</th>
            <th scope='col'>Name</th>
            <th scope='col'>Number of Groups</th>
        </tr></thead>
        
        %# Table Data #
        %for platform_name, platform in pages.platforms.active_platforms().items():
            <tr>
                <td>
                    %checkbox_status = bool('platform' in ADDRESS and ADDRESS['platform'] == platform_name)
                    <input type='radio' name='platform' value="{{platform_name}}" onchange='GoForward()'
                    {{checked(checkbox_status)}} >
                    %if not checkbox_status:
                        <input type='hidden' name='platform_name' value="{{platform['name']}}" >
                    %end
                </td>
                <td>{{platform['name']}}</td>
                <td>{{len(platform.groups)}}</td>
            </tr>
        %end
    </table>
%end
