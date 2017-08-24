
%### INCLUDES ###
%from gate.main import pages
%from gate.tpl import checked


%### HTML ###
%# Platform and Group Names
%platform_name = group['platform']
%group_name = group['internal_name']
%headers = group.enabled_headers('live')

%if page_type == 'live':
    <table class='hor-minimalist-b' >
%elif page_type == 'log':
    <table class='inner_table' >
%end
    %# Header Names
    <thead>
        <tr>
            %for header in headers.values():
                <th colspan="{{len(header.unit_list)}}">{{header['name']}}</th>
            %end
        </tr>
    </thead>
    <tbody>
        %# Unit Names
        <tr>
            %for header in headers.values():
                %for unit in header.unit_list.values():
                    <td>{{unit['measuring_units']}}</td>
                %end                            
            %end
        </tr>
        
        %# Unit Checkboxes
        <tr>
            %for header_name, header in headers.items():
                %for unit_name, unit_value in header.unit_list.items():
                    <td>
                        <input type='checkbox' name='{{platform_name}}_{{group_name}}_{{header_name}}_table_units'
                        value='{{unit_name}}'
                        %if page_type == 'live':
                            onclick='GetLiveData()'
                        %elif page_type == 'log':
                            onclick='GetLogData(false, true)'
                        %end
                        %cookie = pages.get_cookie()
                        %table_units = getattr(group, page_type + '_table_units')(cookie, header_name).keys()
                        {{checked(unit_name in table_units)}} >
                    </td>
                %end
            %end
        </tr>
    </tbody>
</table>
