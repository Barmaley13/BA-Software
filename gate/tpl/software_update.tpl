
%### INCLUDES ###
%from bottle import template

%from gate.main import pages
%from gate.strings import UPLOAD_WARNING, NO_FILE, WRONG_FILENAME, WRONG_EXTENSION, SOFTWARE_UPDATE
%from gate.tpl import form_extension


%### CONSTANTS ###
%if not defined('url'):
    %url = '/' + pages.url()
%end
%if not defined('upload_type'):
    %upload_type = pages.upload_types[pages.template()]
%end

%ADDRESS = pages.get_cookie('nodes_subpage') 
   

%### JS ###
<script><!--
function validate_{{upload_type}}_update(form)
{
    if (form.data.value == "" || form.data.value == null) 
    {
        alert('{{NO_FILE}}');
        form.data.focus();
        return false;
    }
    else
    {
        %# Separate filename from path
        var file = form.data.value.split('\\').pop();
        var parts = file.toLowerCase().split('.');
  
        var extension = parts[parts.length - 1];
        var filename = parts.slice(0, parts.length - 1).join('.');
        
        %# filename_list = filename.split('/-|_/');
        %# var name = filename_list[0];
        %# For future use
        %# var version = filename_list[filename_list.length - 1];
    
        if (!(filename.includes('{{upload_type}}')))
        {
            alert('{{WRONG_FILENAME}}');
            form.data.focus();
            return false;
        }
        %if (upload_type != 'gate'):
            else if (extension != 'spy')
        %else:
            else if ($.inArray(extension, ['vol', 'zip', 'pea']))
        %end
        {
            alert('{{WRONG_EXTENSION}}');
            form.data.focus();
            return false;
        }
    }
    
    %if upload_type == 'gate':
        SoftwareOverlay();
        
        %# Test that JS works properly
        %# alert('Success!')
        return true;
    %else:
        return TryAjaxFileUpload(form);
    %end
}
//--></script>


%### HTML ###
<form action='{{url}}' id='software_update' onsubmit='return validate_{{upload_type}}_update(this)' enctype='multipart/form-data' method='post' >
    <fieldset>
        %if upload_type == 'node':
            %if 'platform' in ADDRESS and ADDRESS['platform'] == 'virgins':
                <legend><h3>{{SOFTWARE_UPDATE}}</h3></legend>
            %end
        %end
        
        {{!template('display_warnings', messages=UPLOAD_WARNING)}}
        <p>
            <span class='float_left' >
                <input type='file' name='data' accept='{{form_extension(upload_type)}}' >
            </span>
            <span class='float_right' >
                <input type='submit' name='submit' value='Start Upload' >
                
                %if upload_type == 'node':
                    <input type='button' value='Cancel' onclick='GoCancel()' >
                %else:
                    <input type='button' value='Cancel' onclick='CancelForm()' >
                %end
            </span>
        </p>
            
        <input type='hidden' name='action_method' value='save_software' >
    </fieldset>
</form>
