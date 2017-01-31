
%### INCLUDES ###
%from bottle import template

%from gate.main import pages, snmp_traps

%### HTML ###
%## STATUS ##
<textarea id='traps_status2' rows='10' cols='100'></textarea>
<br />

%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table')}}
</div>

%## UPDATE FORM ##
<div id='form'></div>

%cookie = pages.get_cookie()
%if 'index' in cookie and cookie['index'] is not None and len(snmp_traps):
    <script><!--
        $(window).load(function(){GetForm('form')});
    //--></script> 
%end
