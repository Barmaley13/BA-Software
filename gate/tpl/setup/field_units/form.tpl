
%### INCLUDES ###
%import logging
%from bottle import template

%from gate.main import manager, pages


%### CONSTANTS ###
%ADDRESS = pages.get_cookie()

%## Logger ##
%LOGGER = logging.getLogger(__name__)
%# LOGGER.setLevel(logging.DEBUG)

%## Debugging ##
%# LOGGER.debug("FORM ADDRESS = " + str(ADDRESS))


%### JS ###
%if manager.update_in_progress():
    <script><!--
        Overlay('software');
    //--></script>
%end
    
%### HTML ###
{{!pages.template_html(None, 'node_addressing', template_type='form')}}
