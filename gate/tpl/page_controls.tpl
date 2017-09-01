
%### INCLUDES ###
%from gate.main import system_settings, pages

%from gate.tpl import checked, selected

%### CONSTANTS ###
%INPUT_TYPES = {'live': 'radio', 'log': 'hidden'}
%ONCLICK_FUNCTIONS = {'live': 'GetLiveData()', 'log': 'GetLogData()'}

%### HTML ###
%cookie = pages.get_cookie()
%group_headers = getattr(group, page_type + '_headers')()
%input_type = INPUT_TYPES[page_type]
%onclick_function = ONCLICK_FUNCTIONS[page_type]

%# Platform and Group Names
%platform_name = group['platform']
%group_name = group['internal_name']
<input type='hidden' name='{{platform_name}}_group' value='{{group_name}}' >

%for header_name, header in group_headers.items():
    %if page_type == 'live':
        %selected_name = None
        %selected_header = getattr(group, page_type + '_header')(cookie)
        %if selected_header and 'internal_name' in selected_header:
            %selected_name = selected_header['internal_name']
        %end
        <input type='{{input_type}}' name='{{platform_name}}_{{group_name}}_header' value='{{header_name}}'
        onclick='{{onclick_function}}' {{checked(header_name == selected_name)}} >{{header['name']}},
    %elif page_type == 'log':
        <input type='{{input_type}}' name='{{platform_name}}_{{group_name}}_header' value='{{header_name}}' >
        <th scope="col">{{header['name']}},
    %end
    
    <select name='{{platform_name}}_{{group_name}}_{{header_name}}_units' onchange='{{onclick_function}}' >
        %for unit_name, unit_value in header.unit_list.items():
            %selected_units = getattr(group, page_type + '_units')(cookie, header)['internal_name']
            <option value='{{unit_name}}'' {{selected(unit_name == selected_units)}}>
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
    
