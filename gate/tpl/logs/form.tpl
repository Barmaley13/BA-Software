
%### INCLUDES ###
%from bottle import template

%from gate.main import manager, pages


%### HTML ###
%## LOG CHART ##
<div id="form" style="width:1100px;height:500px;margin:0px 0px 15px 0px;"></div>

%## AXIS LABELS ##
%#<div class='flot-y-axis flot-y1-axis'><div class='flot-tick-label'>Meters</div></div>
%#<div class='flot-y2-axis'><div class='flot-tick-label'>%</div></div>

{{!template('plot_tooltip')}}

{{!pages.template_html(None, 'plot_hover')}}

%## INITIAL DATA DISPLAY ##
<script><!--
    $(window).load(function (){
        GetLogData(true);
        %if manager.update_in_progress():
            Overlay('software');
        %end
    });
//--></script>
