    
%### INCLUDES ###
%from bottle import template

%from gate.main import pages


%### CONSTANTS ###
%group = pages.get_group()


%### HTML ###
%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table', group=group)}}
</div>

%## WARNINGS ##
{{!template('display_warnings')}}
    
{{!pages.template_html(None, 'form')}}
