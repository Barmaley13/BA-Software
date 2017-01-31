
%### INCLUDES ###
%from gate.main import manager, pages
%from gate.strings import SOFTWARE_UPDATE, UPDATE_HEADERS
%from gate.tpl import hidden
%from gate.sleepy_mesh.networks import NETWORK_UPDATE_TYPES


%### CONSTANTS ###
%URL = pages.url()
%update_type = manager.update_in_progress()

%## Strings ##
%DEFAULT_OVERLAY_MESSAGE = "Processing current request..."


%### HTML ###
%update_id = 'undefined_update'
%if update_type is not None:
    %update_id = update_type + '_update'
%end

<form action='/{{URL}}' method='post' id='{{update_id}}' >
    %# Header
    <h3>
    %if update_type in UPDATE_HEADERS:
        {{UPDATE_HEADERS[update_type]}}
    %else:
        {{SOFTWARE_UPDATE}}
    %end
    </h3>
    
    %# Action
    %if update_type in NETWORK_UPDATE_TYPES:
        <input type='hidden' name='action_method' value='cancel_network_update' >
    %elif update_type in ('log_export', 'database_export', 'database_import'):
        <input type='hidden' name='action_method' value='cancel_{{update_type}}' >
    %else:
        <input type='hidden' name='action_method' value='cancel_software_update' >
    %end
    
    %# Progress Bar
    <div id="progressbar"><div id="progress-label">Loading...</div></div>
    
    %# Progress Message
    <p style='text-align:left;' ><small><span id='software' >
        %if update_type is not None:
            {{manager.websocket.buffer()}}
        %else:
            {{DEFAULT_OVERLAY_MESSAGE}}
        %end
    </span></small></p>
    
    %# Okay, Cancel buttons
    <span class="float_right">
        <input type='button' id='overlay_okay' value='Okay' onclick='Overlay(false)' {{!hidden(update_type is not None)}} >
        <input type='submit' id='overlay_cancel' name='submit' value='Cancel' >
    </span>
</form>


%### JS ###
<script>
    %# Initialize Progress Bar
    $('#progressbar').progressbar({
        value: false,
        create: function() {
            $('#progress-label').text('Loading...');
        },
        complete: function() {
            $('#progress-label').text('Complete!');
        }
    });
    
    %# Initialize Onclick Events
    // console.log('{{update_type}}');
    %if update_type in ('gate', ):
        $('#overlay_okay').click(function() {
            %# Does not matter what method we use because it triggers reboot
            %# AJAX
            $.post('', {action_method: 'post_upload'});
            %# Page Submit
            %# $("<form action='/{{URL}}' method='post'><input type='hidden' name='action_method' value='post_upload'></form>").submit();
            window.location = window.location.protocol + "//" + window.location.hostname + '/logout';
        });
    %elif update_type in ('log_export', 'database_export'):
        $('#overlay_okay').click(function() {
            %# AJAX
            %# $.post('', {action_method: 'finish_{{update_type}}'});
            %# Page Submit
            $("<form action='/{{URL}}' method='post'><input type='hidden' name='action_method' value='finish_{{update_type}}'></form>").submit();
            %# Update page content via ajax
            UpdatePage();
        });
    %elif update_type in ('database_import', ):
        $('#overlay_okay').click(function() {
            %# Close Overlay
            Overlay(false);
            %# Reload Page
            window.location = window.location.href;
        });    
    %elif update_type in ('base', 'node'):
        $('#overlay_okay').click(function() {
            %# Close Overlay
            Overlay(false);
            %# Update page content via ajax
            var cookies = ComposeCookies();
            UpdatePage(cookies);            
        });
    %# elif update_type in NETWORK_UPDATE_TYPES:
    %else:
        $('#overlay_okay').click(function() {
            %# Close Overlay
            Overlay(false);
            %# Update page content via ajax
            UpdatePage();
        });
    %end

    %if update_type:
        Overlay('software');
    %end
    
//--></script>
