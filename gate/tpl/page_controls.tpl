
%### INCLUDES ###
%from gate.main import system_settings, pages

%from gate.tpl import checked, selected

%### CONSTANTS ###
%ONCLICK_FUNCTIONS = {'live': 'GetLiveData()', 'log': 'GetLogData()'}

%### HTML ###
%headers = group.headers.enabled(page_type, group.nodes)
%cookie = pages.get_cookie()
%selected_header = group.headers.selected(cookie, page_type)
%onclick_function = ONCLICK_FUNCTIONS[page_type]

%platform_name = group['platform']
%for header_name, header in headers.items():
    %if page_type == 'live':
        <input type='radio' name='{{platform_name}}_header' value="{{platform_name}}_{{header_name}}"
        onclick='{{onclick_function}}' {{checked(selected_header['internal_name'] == header_name)}} >{{header['name']}},
    %elif page_type == 'log':
        <input type='hidden' name='{{platform_name}}_header' value="{{platform_name}}_{{header_name}}" >
        <th scope="col">{{header['name']}},
    %end
    
    <select name="{{platform_name}}_{{header_name}}_units" onchange='{{onclick_function}}' >
        %for unit_name, unit_value in header.unit_list.items():
            <option value="{{unit_name}}" {{selected(unit_name == header.units(cookie, page_type)['internal_name'])}}>
                {{unit_value['measuring_units']}}
            </option>
        %end
    </select>
    
    %if page_type == 'log':
        </th>
    %end
%end

%if page_type == 'log' and system_settings.manual_log:
    <th scope='col'>Manual Log</th>
%end
    
