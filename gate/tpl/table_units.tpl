
%### INCLUDES ###
%from gate.main import pages
%from gate.tpl import checked


%### HTML ###
%# Platform and Group Names
%platform_name = group['platform']
%group_name = group['internal_name']
%cookie = pages.get_cookie()
%group_headers = group.live_headers()

%if page_type == 'live':
    <table class='hor-minimalist-b' >
%elif page_type == 'log':
    <table class='inner_table' >
%end
    %# Header Names
    <thead>
        <tr>
            %for header in group_headers.values():
                <th colspan="{{len(header.unit_list)}}">{{header['name']}}</th>
            %end
        </tr>
    </thead>
    <tbody>
        %# Unit Names
        <tr>
            %for header in group_headers.values():
                %for unit in header.unit_list.values():
                    <td>{{unit['measuring_units']}}</td>
                %end                            
            %end
        </tr>
        
        %# Unit Checkboxes
        %onclick_functions = {'live': 'GetLiveData()', 'log': 'GetLogData(false, true)'}
        <tr>
            %for header_name, header in group_headers.items():
                %for unit_name, unit_value in header.unit_list.items():
                    <td>
                        <input type='checkbox' name='{{platform_name}}_{{group_name}}_{{header_name}}_table_units'
                        value='{{unit_name}}' onclick='{{onclick_functions[page_type]}}'
                        %table_units = getattr(group, page_type + '_table_units')(cookie, header_name).keys()
                        {{checked(unit_name in table_units)}} >
                    </td>
                %end
            %end
        </tr>
    </tbody>
</table>
