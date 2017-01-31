
%### INCLUDES ###
%from bottle import template

%from gate.main import pages

%### HTML ###
%## STATUS ##
<textarea id='status2' rows='10' cols='100'></textarea>
<br />
<div id='form'></div>

%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table')}}
</div>
