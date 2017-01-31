
%### INCLUDES ###
%from gate.main import pages

%### HTML ###
%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table')}}
</div>

%## UPDATE FORM ##
<div id='form'></div>

%# Trigger Form display #
%cookie = pages.get_cookie()
%if 'index' in cookie and cookie['index'] is not None:
    <script><!--
        $(window).load(function(){GetForm('form')});
    //--></script>
%end
