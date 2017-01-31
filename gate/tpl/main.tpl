
%### INCLUDES ###
%from gate.main import system_settings, pages
%from gate.strings import NO_JAVASCRIPT, SUCCESS

%### HTML ###
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html lang="en" xml:lang="en" xmlns="http://www.w3.org/1999/xhtml"> 
    <head>
        %## TITLE ##
        {{!pages.title()}}
        %## CSS ##
        <link rel='stylesheet' type='text/css' href='/style/common.css' />
        <link rel='stylesheet' type='text/css' href='/style/{{system_settings.name}}/style.css' />
        %## ICON ##
        <link rel='shortcut icon' href='/favicon.ico' />
        %## META ##
        <meta http-equiv='Content-Type' content='text/html; charset=utf-8' />
        %## JAVASCRIPT ##
        %# Dynamic Selections #
        <script><!--
            %# if (navigator.onLine == false)
            %#    document.getElementById('jquery').src = '/js/jquery.js';
            
            var Path = window.location.pathname.substring(1);
            %#var Path = window.location.pathname.split("/");
            %#Path = Path[Path.length-1];
            if (Path.split("/")[0] == "")
                Path = "{{pages.url(pages.index_page)}}" + Path;
            %#console.log(Path);
            var LogLimit = {{system_settings['log_limit']}};
        //--></script>
        %# JQUERY #
        <link rel='stylesheet' href='/js/jquery-ui-1.11.4/jquery-ui.min.css'>
        <script id='jquery' src='/js/jquery-1.11.2.min.js'></script>
        <script src='/js/jquery-ui-1.11.4/jquery-ui.min.js'></script>
        
        %# FLOT #
        <script src='/js/jquery.flot.js'></script>
        <script src='/js/jquery.flot.time.js'></script>
        <script src='/js/jquery.flot.navigate.js'></script>
        <!--[if lte IE 8]><script language="javascript" type="text/javascript" src="excanvas.min.js"></script><![endif]-->
        %# CUSTOM SCRIPTS #
        <script src='/js/ajax.js'></script>
        <script src='/js/autofill.js'></script>
        <script src='/js/update.js'></script>
    </head>
    
    <body>
        <noscript><p>{{NO_JAVASCRIPT}}</p></noscript>
    
        <div class="main">
            %# LOGOS
            <div id='logo1' ><img alt='logo' src='/img/{{system_settings.name}}/logo.png' /></div>
            %if system_settings.name == 'jowa':
                <div id='logo2' >
                    <h2>{{system_settings.product}}</h2>
                    <p>Wireless</p><p>Monitoring</p><p>System</p>
                </div>
            %end
            %# HEADER
            <div class="header"><h1>{{system_settings.title()}}</h1></div>
            %# BUTTONS
            %#<div id="buttons"><h2>{{!pages.buttons()}}</h2></div>
            <div id="buttons">{{!pages.buttons()}}</div>
            %# CONTENT
            <div class="content">
                {{!pages.websocket_html()}}
                {{!pages.header()}}
                {{!pages.html()}}
            </div>
            %# FOOTER
            <div class="footer">
                <p style="margin:0px;" >&copy; {{system_settings.company}}</p>
                <a href="http://{{system_settings.url}}" target="_blank" >{{system_settings.url}}</a>
            </div>
        </div>
    
        %# CONFIRMATIONS, ALERTS
        %if defined('confirm'):
            <script><!--
                $(window).load(function(){
                    var confirmResponse = confirm("{{confirm}}");
                    if (confirmResponse == true)
                    {
                        %if defined('reboot'):
                            {{!reboot}}
                        %end
                    }
                });
            //--></script>
        %end
        
        %if defined('alert'):
            <script><!--
                $(window).load(function(){alert("{{alert}}")});
            //--></script>
        %end
        
        %# NOT USED. FOR TESTING ONLY!
        %if defined('success'):
            <script><!--
                $(window).load(function(){alert("{{SUCCESS}}")});
            //--></script>
        %end
        
    </body>
</html>
