
%### INCLUDES ###
%from gate.tpl import selected, hidden


%### HTML ###
%constant_name = constant['data_field'] + '_' + constant['internal_name']
<p id="{{constant_name}}">{{constant['name']}}:
%if type(constant['default_value']) is not list:
    %if value == 'Multiple':
        <input type='text' name="{{constant_name}}-Multiple" value='{{value}}' size='10' onclick="DisableMultiple('{{constant_name}}')" >
        
        <input type='number' name="{{constant_name}}" min="{{constant['min_value']}}"
        max="{{constant['max_value']}}" step="{{constant['step']}}" size='5' {{!hidden(True)}} >
    %else:
        %if value == None:
            %value = ''
        %end
        <input type='number' name="{{constant_name}}" value='{{value}}' min="{{constant['min_value']}}"
        max="{{constant['max_value']}}" step="{{constant['step']}}" size='5' >    
    %end
%else:
    
    %if value != 'Multiple':
        <select name="{{constant_name}}">
    %else:
        <select name="{{constant_name}}" id='{{constant_name}}-Multiple'>    
            <option value='Multiple' {{selected(True)}} >Multiple</option>
    %end
    
    %for index, default in enumerate(constant['default_value']):
        %if type(value) in (str, unicode):
            %option_select = selected(value.decode('utf-8') == default)
        %else:
            %option_select = selected(value == default)
        %end

        <option value='{{default}}' {{option_select}} >
        %if type(constant['description']) is list:
            {{constant['description'][index]}}
        %else:
            {{default}}
        %end
        </option>
    %end
    </select>
%end

%if type(constant['description']) is not list and (constant['description'] or constant['measuring_units']):
    <small>*
    %if constant['description'] and constant['measuring_units']:
        {{constant['description'] + ", " + constant['measuring_units']}}
    %elif constant['description']:
        {{constant['description']}}
    %elif constant['measuring_units']:
        {{constant['measuring_units']}}
    %end
    </small>
%end
</p>
