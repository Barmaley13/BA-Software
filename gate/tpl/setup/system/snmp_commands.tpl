
%### INCLUDES ###
%from bottle import template

%from gate.main import pages, snmp_commands

%### HTML ###
%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table')}}
</div>

%## UPDATE FORM ##
<div id='form'></div>

%cookie = pages.get_cookie()
%if 'index' in cookie and cookie['index'] is not None and len(snmp_commands):
    <script><!--
        $(window).load(function(){GetForm('form')});
    //--></script> 
%end
