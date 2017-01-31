    
%### INCLUDES ###
%from bottle import template

%from gate.main import pages


%### CONSTANTS ###
%group = pages.get_group()


%### HTML ###
%## WARNINGS ##
{{!template('display_warnings')}}

%## TABLE ##
<div id='table'>
    {{!pages.template_html(None, 'table', group=group)}}
</div>

{{!template('plot_tooltip')}}

%## INITIAL DATA DISPLAY ##
<script><!--
    $(window).load(function (){GetLiveData(true)});
//--></script>
