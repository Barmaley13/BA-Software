
%### INCLUDES ###
%from bottle import template

%from gate.main import pages

%### HTML ###
%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table')}}
</div>

%## UPDATE FORM ##
<div id='form'></div>

%cookie = pages.get_cookie()
%if cookie is not None:
    <script><!--
        $(window).load(function(){GetForm('form')});
    //--></script> 
%end
