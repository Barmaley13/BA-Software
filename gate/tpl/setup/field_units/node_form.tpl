
%### INCLUDES ###
%import logging
%from bottle import template

%from gate.main import pages, users


%### CONSTANTS ###
%URL = pages.url()
%ADDRESS = pages.get_cookie()
%PLATFORM = pages.platforms.platform(ADDRESS)
%INACTIVE_GROUP = bool(ADDRESS['group'] == PLATFORM.groups.keys()[0])

%## Logger ##
%LOGGER = logging.getLogger(__name__)
%# LOGGER.setLevel(logging.DEBUG)


%### JS/HTML ###
%if len(ADDRESS['nodes']):
    %if ADDRESS['platform'] == 'virgins':
        {{!template('software_update')}}
    %else:
        %## JS ##
        %active_tab = 0
        %if 'active_tab' in ADDRESS:
            %active_tab = ADDRESS['active_tab']
        %end
        <script><!--    
            $("#tabs").tabs({
                active: {{active_tab}},
                beforeLoad: function(event, ui) {
                    %# Setting up Progress Bar
                    ui.panel.html("<fieldset><div id='progressbar'><div id='progress-label'>Loading...</div></div></fieldset>");
                    $('#progressbar').progressbar({
                        value: false,
                        create: function() {
                            $('#progress-label').text('Loading...');
                        },
                        complete: function() {
                            $('#progress-label').text('Complete!');
                        }
                    });
                    
                    %# Setting up AJAX for the tabs
                    var url = window.location.protocol + "//" + window.location.hostname + "/ajax";
                    var data = {
                        data: JSON.stringify({
                            url: ui.tab.find('a').attr('href'),
                            kwargs: {upload_type: 'node'}
                        })
                    };
                    // console.log(ui.tab.find('a').attr('href'));
                    
                    ui.ajaxSettings.type = 'GET';
                    ui.ajaxSettings.url = url  + "?" + $.param(data, false);
                    // console.log(ui.ajaxSettings.url);
                    
                    ui.jqXHR.fail(function() {
                        ui.panel.html('<fieldset><p><small>Unable to load tab via AJAX!</small></p></fieldset>');
                    });
                    ui.jqXHR.done(function(JsonData){
                        ParseTable(JsonData);
                        if (JsonData.form !== undefined)
                        {
                            setTimeout(function(){
                                ui.panel.html(JsonData.form);
                            }, 10);
                        }
                    });
                }
            });
            $("#tabs").removeClass('ui-widget');
        //--></script>

        %## HTML ##
        <div id="tabs">
            <ul>
                <li><a href="/{{URL}}/field_unit_update" >Field Unit Update</a></li>
                
                %if not INACTIVE_GROUP:
                    <li><a href="/{{URL}}/sensor_parameters" >Sensor Parameters</a></li>
                %end
                
                %if users.check_access('admin'):
                    <li><a href="/{{URL}}/software_update" >Software Update</a></li>
                %end
            </ul>
        </div>
    %end
%end
