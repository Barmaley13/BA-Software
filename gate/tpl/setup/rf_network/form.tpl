
%### INCLUDES ###
%from bottle import template

%from gate.main import manager, pages, users


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
        <li><a href="#network_update" >Network Update</a></li>
        %if users.check_access('admin'):
            <li><a href="#software_update" >Software Update</a></li>
        %end
    </ul>

    <div id="network_update">
        {{!pages.template_html(None, 'network_update')}}
    </div>
    
    %if users.check_access('admin'):
        <div id="software_update">
            {{!template('software_update')}}
        </div>
    %end
    
</div>
