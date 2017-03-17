
%### INCLUDES ###
%from gate.main import pages, users
%from gate.tpl import disabled

%### CONSTANTS ###
%URL = pages.url()
%ADDRESS = pages.get_cookie()

%### JS/HTML ###
%if 'group' in ADDRESS:
    %GROUP = None
    %if ADDRESS['group'] is not None:
        %GROUPS = pages.platforms.platform(ADDRESS).groups
        %GROUP = pages.platforms.group(ADDRESS)
        %INDEX = GROUPS.keys().index(ADDRESS['group'])
    %end

    %## JS ##
    <script><!--
    function validate_update_group_form(form)
    {
        if (form.action_method.value == 'update_group' || form.action_method.value == 'create_group')
        {
            if (form.group_name.value == "" || form.group_name.value == null) 
            {
                alert("Group name can not be empty!");
                form.group_name.focus();
                return false;
            }
            else if (name_taken == true)
            {
                alert("This group name is taken already!");
                form.group_name.focus();
                return false;
            }
        }

        %# Test that JS works properly
        %# alert('Success!')
        return true;
    }
    //--></script>

    %## HTML ##
    <form action='/{{URL}}' onsubmit='return validate_update_group_form(this)' method='post' ><fieldset>
        %if GROUP is not None:
            <legend><h3>{{GROUP['name']}} Update</h3></legend>
        %else:
            <legend><h3>New Group</h3></legend>
        %end
        
        %## FORM FIELDS ##
        %if GROUP is not None:
            <input type='hidden' name='action_method' value='update_group' >
        %else:
            <input type='hidden' name='action_method' value='create_group' >
        %end
        <input type='hidden' name='platform' value="{{ADDRESS['platform']}}" >
        <input type='hidden' name='group' value="{{ADDRESS['group']}}" >

        %## INPUT FIELDS ##
        <p>Group Name:
            <input type='text' name='group_name'
            %if GROUP is not None:
                value="{{GROUP['name']}}" {{disabled(INDEX == 0)}}
            %else:
                value=""
            %end
            size='20' onkeyup="GetNameValidation()" >
            <small id='name_validation' ></small>
        </p>

        %if GROUP is not None and len(GROUP.nodes):
            <p><b>Field Units</b></p>
            {{!pages.template_html(None, 'node_table', group = GROUP)}}
            <p><input type='button' value='Edit Field Units' onclick="CheckNode()" ></p>
        %end

        %## BUTTONS ##
        <p>
            %if GROUP is not None:
                <span class="float_left">
                    %if users.check_access('write') and INDEX != 0:
                        <input type='button' value='Up' onclick="SubmitAction('group', 'up')" {{disabled(INDEX == 1)}} >
                        <input type='button' value='Down' onclick="SubmitAction('group', 'down')" {{disabled(INDEX == len(GROUPS)-1)}} >
                        <input type='button' value='Remove' onclick="SubmitAction('group', 'remove')" >
                    %end
                </span>
                <span class="float_right">
                    %if users.check_access('write') and INDEX != 0:
                        <input type='submit' name='group_submit' value='Save' >
                    %end
                    <input type='button' value='Cancel' onclick="GoCancel()" >
                </span>
            %else:
                <span class="float_right">
                    %if users.check_access('write'):
                        <input type='submit' name='group_submit' value='Create' >
                    %end
                    <input type='button' value='Cancel' onclick="GoCancel()" >
                </span>
            %end
        </p>
        
    </fieldset></form>

%end
