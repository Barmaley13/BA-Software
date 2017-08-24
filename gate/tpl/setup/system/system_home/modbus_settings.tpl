
%### INCLUDES ###
%from gate.main import system_settings, pages
%from gate.tpl import selected, BYTE_ORDER, REGISTER_ORDER


%### CONSTANTS ###
%URL = pages.url()


%### HTML ###
<form action='/{{URL}}' method='post' ><fieldset>
    %# Action
    <input type='hidden' name='action_method' value='update_modbus' >
   
    <p><b>Modbus Float Settings</b><p>
        <p>Byte Order:
            <select name="modbus_byte_order" >
                %byte_order = system_settings['modbus_byte_order']
                <option value="0" {{selected(not byte_order)}}>{{BYTE_ORDER[0]}}</option>
                <option value="1" {{selected(byte_order)}}>{{BYTE_ORDER[1]}}</option>
            </select>
        </p>
        <p>Register Order:
            <select name="modbus_register_order" >
                %register_order = system_settings['modbus_register_order']
                <option value="0" {{selected(not register_order)}}>{{REGISTER_ORDER[0]}}</option>
                <option value="1" {{selected(register_order)}}>{{REGISTER_ORDER[1]}}</option>
            </select>
        </p>
    
    <p><b>Modbus Units</b><p>
    %active_platforms = pages.platforms.active_platforms()
    %for platform_name, platform in active_platforms.items():
        %if len(active_platforms) > 1:
            <p>{{pages.platforms[platform_name]['name']}}</p>
        %end
        %display_headers = platform.read_headers('display')
        %for header_name, header in display_headers.items():
            <p>{{header['name']}}:
                <select name="{{platform_name}}_{{group_name}}_{{header_name}}_units" >
                    %for unit_name, unit_value in header.unit_list.items():
                        <option value="{{unit_name}}" {{selected(unit_value == header.modbus_units())}}>
                            {{unit_value['measuring_units']}}
                        </option>
                    %end
                </select>
            </p>
        %end
    %end

    %## BUTTONS ##
    <p>
        %# Update, Reset, Cancel Buttons
        <span class="float_right">
            <input type='submit' name='submit' value='Save' >
            <input type='button' value='Cancel' onclick="CancelForm()" >
        </span>
    </p>

</fieldset></form>
