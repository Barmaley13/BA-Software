
%### INCLUDES ###
%from bottle import template

%from gate.main import manager, system_settings, pages, users


%### CONSTANTS ###
%COOKIE = pages.get_cookie()


%### JS ###
%active_tab = 0
%if 'active_tab' in COOKIE:
    %active_tab = COOKIE['active_tab']
%end
<script><!--
    $("#tabs").tabs({active: {{active_tab}}});
    $("#tabs").removeClass('ui-widget');
    
    %if manager.update_in_progress():
        Overlay('software');
    %end

//--></script>


%### HTML ###
<div id="tabs">
    <ul>
        <li><a href="#system_settings" >System Settings</a></li>
        
        %if system_settings.modbus_enable:
            <li><a href="#modbus_settings" >Modbus Settings</a></li>
        %end
        
        %if system_settings.snmp_enable:
            <li><a href="#snmp_settings" >SNMP Settings</a></li>
        %end
        
        <li><a href="#export_import" >Export/Import Database</a></li>
        
        %if users.check_access('admin'):
            <li><a href="#software_update" >Software Update</a></li>
        %end
    </ul>

    <div id="system_settings">
        {{!pages.template_html(None, 'system_settings')}}
    </div>
    
    %if system_settings.modbus_enable:
        <div id="modbus_settings">
            {{!pages.template_html(None, 'modbus_settings')}}
        </div>
    %end
    
    %if system_settings.snmp_enable:
        <div id="snmp_settings">
            {{!pages.template_html(None, 'snmp_settings')}}
        </div>
    %end

    <div id="export_import">
        {{!pages.template_html(None, 'export_import')}}
    </div>
        
    %if users.check_access('admin'):
        <div id="software_update">
            {{!template('software_update')}}
        </div>
    %end
</div>
