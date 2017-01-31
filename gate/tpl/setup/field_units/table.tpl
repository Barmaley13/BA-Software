
%### INCLUDES ###
%import logging

%from bottle import template

%from gate.main import pages
%from gate.strings import NO_NODES


%### CONSTANTS ###
%ADDRESS = pages.get_cookie()

%## Logger ##
%LOGGER = logging.getLogger(__name__)
%# LOGGER.setLevel(logging.DEBUG)

%## Debugging ##
%LOGGER.debug("TABLE ADDRESS = " + str(ADDRESS))

%"""
%for platform_name, platform in pages.platforms.items():
    %LOGGER.debug("platform: " + platform_name + " len = " + str(len(platform.groups.values()[0].nodes)))
%end
%LOGGER.debug("len(nodes) = " + str(len(pages.platforms.select_nodes('ALL'))))
%"""


%### SCRIPTS ###
<script><!--
    %if 'group' in ADDRESS:
        $("#page_header").html("Groups");
        %if ADDRESS['group'] is not None:
            %group_name = pages.platforms.group(ADDRESS)['name']
            $("#page_header_extra").html(" - {{group_name}}");
        %else:
            $("#page_header_extra").empty();
        %end
    %elif len(pages.platforms.active_platforms()) > 1:
        $("#page_header").html("Platforms");
        %if 'platform' in ADDRESS and ADDRESS['platform'] is not None:
            %platform_name = pages.platforms.platform(ADDRESS)['name']
            $("#page_header_extra").html(" - {{platform_name}}");
        %else:
            $("#page_header_extra").empty();
        %end
    %else:
        $("#page_header").html("Groups");
        $("#page_header_extra").empty();
    %end
//--></script>


%### HTML ###
%if len(pages.platforms.select_nodes('ALL')) > 0:
    {{!pages.template_html(None, 'node_addressing', template_type='table')}}
%else:
    {{!template('display_warnings', messages=NO_NODES)}}
%end
