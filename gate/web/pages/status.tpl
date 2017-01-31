    
%### INCLUDES ###
%from gate.main import pages, manager
%from gate.strings import WEBSOCKET_ERROR, ONLINE, AWAKE, SLEEP, OFFLINE


%### CONSTANTS ###
%URL = pages.url()
%TIMEOUT = int((manager.sleep_period() + manager.wake_period()) * 1000)


%### JS ####
<script><!--
    %## WEB SOCKET ##
    $(function(){
        if (!window.WebSocket)
        {
            if (window.MozWebSocket)
                window.WebSocket = window.MozWebSocket;
            else
                alert("{{WEBSOCKET_ERROR}}");
        }

        var ws = new WebSocket("ws://"+window.location.hostname+":80/status");
        ws.onopen = function(){AppendStatus("{{ONLINE}}")};
        ws.onmessage = function(evt){UpdateStatus(evt.data)};
        ws.onclose = function(evt){AppendStatus("{{OFFLINE}}")};
        
        SetWatchDog();
    });
    
    %## WEB SOCKET FUNCTIONS ##
    function AppendStatus(message)
    {       
        switch(message)
        {
            %system_status_icon = pages.status_icons()['system_status']
            %#online = system_status_icon.current_icon('online')
            %awake = system_status_icon.current_icon('awake')
            %sleep = system_status_icon.current_icon('sleep')
            %offline = system_status_icon.current_icon('offline')

            case "{{ONLINE}}":
                StatusIcon('system_status', '{{!awake}}', false);
                break;
            case "{{AWAKE}}":
                StatusIcon('system_status', '{{!awake}}', false);
                break;
            case "{{SLEEP}}":
                StatusIcon('system_status', '{{!sleep}}', false);
                break;
            case "{{OFFLINE}}":
                StatusIcon('system_status', '{{!offline}}', false);
                break;
            default:
                break;
        }
        
        %if pages.url('diagnostics_page') in URL:
            $("#status2").append(message+"&#13;");
            $("#status2").scrollTop($("#status2")[0].scrollHeight - $("#status2").height());
        %end
    }
    
    function UpdateStatus(message)
    {
        var data = JSON.parse(message);
        
        // console.log(data);
        
        %# WatchDog BS #
        ClearWatchDog();
        SetWatchDog();
        
        %# Progress Bar (if needed) #
        var progress_bar = $('#progressbar');
        var progress_label = $('#progress-label');
        
        if (progress_bar && data.progress && data.progress != '' && data.progress != null)
        {
            progress_value = parseInt(data.progress);
            progress_message = data.progress + '%';

            progress_bar.progressbar({
                value: progress_value,
                change: function() {
                    progress_label.text(progress_message);
                }
            });
        }
        
        %# Web Socket Protocol #
        switch(data.type)
        {
            case 'ws_sleep':
                AppendStatus(data.message);
                %if pages.url('live_data') in URL:
                    GetLiveData();
                %elif pages.url('logs_data') in URL:
                    GetLogData(true);
                %else:
                    var table_index = $("[name='index']:checked").val();
                    GetForm('table', table_index);
                    %if pages.url('system_subpage') in URL:
                        AutoTime(true);
                    %end
                %end
                break;
            case 'ws_init':
                $("#software").html(data.message);
                break;
            case 'ws_append':
                $("#software").append(data.message);
                break;
            case 'ws_finish':
                $("#software").html(data.message);
                $('#overlay_cancel').hide();
                $('#overlay_okay').show();
                break;
            case 'ws_reload':
                AppendStatus(data.message);
                window.location = window.location.href;
                break;
            default:
                AppendStatus(data.message);
                break;
        }
    }

    %## WEB SOCKET WATCHDOG FUNCTIONS ##
    var ws_watchdog;
    function SetWatchDog()
    {
        ws_watchdog = window.setTimeout(function() {AppendStatus("{{OFFLINE}}")}, {{TIMEOUT}});
    }
    
    function ClearWatchDog()
    {
        window.clearTimeout(ws_watchdog);
    }
    
    %## AJAX LONG POLLING ##
    %"""
    $(window).load(function(){
        poll(true);
    });
    
    function poll(flush)
    {
        if (flush == "" || flush == null)
        {
            var request = $.ajax({
                url: "status",
                type: "GET",
                dataType: "html",
                timeout: 10000
            });
        }
        else
        {
            var request = $.ajax({
                url: "status",
                type: "GET",
                data: {flush: 'True'},
                dataType: "html",
                timeout: 10000
            });  
        }
    
        request.done(function(msg) {
            UpdateStatus(msg);
            // Continue Long Polling
            poll();
        });
 
        request.fail(function(jqXHR, textStatus) {
            AppendStatus("Offline");
        });
    }
    %"""
//--></script>
