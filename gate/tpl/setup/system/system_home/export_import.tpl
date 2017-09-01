
%### INCLUDES ###
%from gate.main import pages
%from gate.strings import NO_FILE, WRONG_FILENAME, WRONG_EXTENSION


%### CONSTANTS ###
%URL = pages.url()


%### JS ###
<script><!--
function validate_import_form(form)
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
    
        % """
        if (!(filename.includes('database')))
        {
            alert('{{WRONG_FILENAME}}');
            form.data.focus();
            return false;
        }
        else if ($.inArray(extension, ['zip', 'dea']))
        % """
        if ($.inArray(extension, ['zip', 'dea']))
        {
            alert('{{WRONG_EXTENSION}}');
            form.data.focus();
            return false;
        }
    }
    
    return TryAjaxFileUpload(form);
}

function RemoveDatabase()
{
    var removeConfirm = confirm("Are you sure you want to remove database?");
    if (removeConfirm)
    {
        %# Page Submit
        var remove_form = $("<form action='/{{URL}}' method='post'><input type='hidden' name='action_method' value='remove_database'></form>");
        $(document.body).append(remove_form);
        remove_form.submit();
    }
}
//--></script>


%### HTML ###
%## Import/Export Form ##
<form action='/{{URL}}' id='import_export' onsubmit='return validate_import_form(this)' enctype='multipart/form-data' method='post' ><fieldset>
    %# Action
    <input type='hidden' name='action_method' value='start_database_import' >
    
    %# Upload database settings from E10
    <p><b>Export Database</b></p>
    <p>
        <input type='button' value='Export' onclick="SoftwareOverlay({action_method: 'start_database_export', ajax: true})" >
    </p>

    %# Remove Database
    <p><b>Remove Database</b></p>
    <p>
        <input type='button' value='Remove' onclick="RemoveDatabase()" >
    </p>
    
    %# Save database settings to E10
    <p><b>Import Database</b></p>
    <p>
        <span class='float_left' >
            <input type='file' name='data' accept='.dea' >
        </span>
        <span class="float_right">
            <input type='submit' name='submit' value='Import' >
            <input type='button' value='Cancel' onclick="CancelForm()" >
        </span>
    </p>

</fieldset></form>
