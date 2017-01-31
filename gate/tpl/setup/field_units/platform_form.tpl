
%### INCLUDES ###
%from gate.main import pages, users
%from gate.tpl import disabled

%### CONSTANTS ###
%URL = pages.url()
%ADDRESS = pages.get_cookie()

%### HTML/JS ###
%if 'platform' in ADDRESS and ADDRESS['platform'] is not None:
    %INDEX = pages.platforms.keys().index(ADDRESS['platform'])
    %## JS ##
    <script><!--
    function validate_update_platform_form(form)
    {
        if (form.action_method.value == 'update_platform')
        {    
            if (form.platform_name.value == "" || form.platform_name.value == null) 
            {
                alert("Platform name can not be empty!");
                form.platform_name.focus();
                return false;
            }
            else
            {
                var user_answer = true;
                
                $("input:hidden[name='platform_name']").each(function () {
                    if ($(this).val() == form.platform_name.value)
                    {
                        user_answer = confirm("This name is already in use! Would you like to proceed?");
                    }
                });
                return user_answer;
            }
        }

        %# Test that JS works properly
        %# alert('Success!')
        return true;
    }
    //--></script>

    %## HTML ##
    %platform = pages.platforms.platform(ADDRESS)
    <form action='/{{URL}}' onsubmit='return validate_update_platform_form(this)' method='post' ><fieldset>
        <legend><h3>{{platform['name']}} Update</h3></legend>

        %## FORM FIELDS ##
        <input type='hidden' name='action_method' value='update_platform' >
        <input type='hidden' name='platform' value="{{ADDRESS['platform']}}" >

        %## INPUT FIELDS ##
        <p>Platform Name:
            <input type='text' name='platform_name' value="{{platform['name']}}" size='20' {{disabled(platform['platform'] == 'virgins')}} >
        </p>

        <p><b>Groups</b></p>
        
        {{!pages.template_html(None, 'group_table', platform = platform)}}
        <p><input type='button' value='Edit Groups' onclick="CheckGroup()" ></p>

        %## BUTTONS ##
        <p>
            %if users.check_access('write'):
                <span class="float_left">
                    <input type='button' value='Up' onclick="SubmitAction('platform', 'up')" {{disabled(INDEX == 0)}} >
                    <input type='button' value='Down' onclick="SubmitAction('platform', 'down')" {{disabled(INDEX == len(pages.platforms)-1)}} >
                    <input type='button' value='Restore to Defaults' onclick="SubmitAction('platform', 'restore')" >
                </span>
                <span class="float_right">
                    <input type='submit' name='platform_submit' value='Save' {{disabled(platform['platform'] == 'virgins')}} >
            %else:
                <span class="float_right">
            %end
                <input type='button' value='Cancel' onclick="GoCancel()" >
            </span>
        </p>
        
    </fieldset></form>
%end
