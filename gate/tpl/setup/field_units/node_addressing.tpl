
%### INCLUDES ###
%from gate.main import pages

%### CONSTANTS ###
%ADDRESS = pages.get_cookie()

%### HTML ###
%active_platforms = pages.platforms.active_platforms()
%if len(active_platforms) <= 1:
    %if 'nodes' in ADDRESS:
        {{!pages.template_html(None, 'node_' + template_type)}}
    %else:
        {{!pages.template_html(None, 'group_' + template_type)}}
    %end
%else:    
    %if 'nodes' in ADDRESS:
        {{!pages.template_html(None, 'node_' + template_type)}}
    %elif 'group' in ADDRESS:
        {{!pages.template_html(None, 'group_' + template_type)}}
    %else:
        {{!pages.template_html(None, 'platform_' + template_type)}}
    %end
%end
