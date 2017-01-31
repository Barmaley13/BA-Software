    
%### INCLUDES ###
%from gate.strings import WEBSOCKET_ERROR, ONLINE, OFFLINE


%### JAVASCRIPT ###
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

        var traps_ws = new WebSocket("ws://"+window.location.hostname+":80/traps");
        traps_ws.onopen = function(){AppendTrapsStatus("{{ONLINE}}")};
        traps_ws.onmessage = function(evt){UpdateTrapsStatus(evt.data)};
        traps_ws.onclose = function(evt){AppendTrapsStatus("{{OFFLINE}}")};
    });
    
    %## WEB SOCKET FUNCTIONS ##
    function AppendTrapsStatus(message)
    {               
        $("#traps_status2").append(message+"&#13;");
        $("#traps_status2").scrollTop($("#traps_status2")[0].scrollHeight - $("#traps_status2").height());
    }
    
    function UpdateTrapsStatus(message)
    {
        var data = JSON.parse(message);
        //console.log(data);
        
        AppendTrapsStatus(data.message);
    }

//--></script>
