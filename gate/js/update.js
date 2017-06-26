<!--

function CancelForm()
{
    $("#form").empty();
    GetForm('table', null);
}

function DisplayForm(form_name)
{
    $("#" + form_name).show();
}

function HideForm(form_name)
{
    $("input[name='" + form_name + "'][value='0']").prop('checked', true);
    $("#" + form_name).hide();
}

function AdcEnables(type, value)
{
    var total_display = new Object();
    var total_track = new Object();
    var total_diagnostics = new Object();
    
    if (type == 'live_enable')
    {
        if ($("input[name='live_enable'][value='"+value+"']").prop('checked') == false)
        {
            $("input[name='live_enable'][value='"+value+"']").prop('indeterminate', false);
            $("input[name='log_enable'][value='"+value+"']").prop('indeterminate', false);
            $("input[name='log_enable'][value='"+value+"']").prop('checked', false);
        }
        else if ($("input[name='live_enable'][value='"+value+"']").prop('checked') == true)
        {
            $("input[name='diagnostics'][value='"+value+"']").prop('checked', false);
        }
    }
    else if(type == 'log_enable')
    {
        if ($("input[name='log_enable'][value='"+value+"']").prop('checked') == true)
        {
            $("input[name='log_enable'][value='"+value+"']").prop('indeterminate', false);
            $("input[name='live_enable'][value='"+value+"']").prop('indeterminate', false);
            $("input[name='live_enable'][value='"+value+"']").prop('checked', true);
            $("input[name='diagnostics'][value='"+value+"']").prop('checked', false);
        }
    }
    else if(type == 'diagnostics')
    {
        if ($("input[name='diagnostics'][value='"+value+"']").prop('checked') == true)
        {
            $("input[name='log_enable'][value='"+value+"']").prop('indeterminate', false);
            $("input[name='log_enable'][value='"+value+"']").prop('checked', false);
            $("input[name='live_enable'][value='"+value+"']").prop('indeterminate', false);
            $("input[name='live_enable'][value='"+value+"']").prop('checked', false);
        }

    }

    $("input[name='live_enable']").each(function() {
        if ($(this).prop('indeterminate') == true)
            total_display[$(this).val()] = null;
        else
            total_display[$(this).val()] = $(this).prop('checked');
    });
    
    $("input[name='log_enable']").each(function() {
        if ($(this).prop('indeterminate') == true)
            total_track[$(this).val()] = null;
        else
            total_track[$(this).val()] = $(this).prop('checked');
    });

     $("input[name='diagnostics']").each(function() {
        total_diagnostics[$(this).val()] = $(this).prop('checked');
    });

    $("input[name='total_display']").val(JSON.stringify(total_display));
    $("input[name='total_track']").val(JSON.stringify(total_track));
    $("input[name='total_diagnostics']").val(JSON.stringify(total_diagnostics));
    
    //console.log(total_display);
    //console.log(total_track);
    //console.log(total_diagnostics);
    
}

function AdcAlarms()
{
    var total_min_alarm = new Object();
    var total_max_alarm = new Object();
    
    $("input[name='min_alarm_enable']").each(function() {
        if ($(this).prop('indeterminate') == true)
            total_min_alarm[$(this).val()] = null;
        else
            total_min_alarm[$(this).val()] = $(this).prop('checked');
    });

    $("input[name='max_alarm_enable']").each(function() {
        if ($(this).prop('indeterminate') == true)
            total_max_alarm[$(this).val()] = null;
        else
            total_max_alarm[$(this).val()] = $(this).prop('checked');
    });
  
    $("input[name='total_min_alarm']").val(JSON.stringify(total_min_alarm));
    $("input[name='total_max_alarm']").val(JSON.stringify(total_max_alarm));
    
    //console.log(total_alarm);

}

function CreateNew()
{
    $("input:radio[name='index']:checked").prop('checked', false);
    GetForm('form', null);
}

// FIELD UNIT FUNCTIONS
function ComposeCookies()
{
    var cookies = new Object();

    var page_type = $('#group option');
    if (page_type.length > 0)
    {
        var platform = $('#platform').val();
        var group = $('#group').val();
        var node = $('#node').val();

        if (!(platform == undefined || platform == ''))
        {
            cookies.platform = platform;

            if (!(group == undefined || group == ''))
            {
                cookies.group = group;

                if (!(node == undefined || node == ''))
                {
                    cookies.nodes = [node];
                }
            }
        }
    }
    else
    {
        var platform = $("input[name='platform']:checked").val();
        var group = $("input[name='group']:checked").val();
        var node_array = $("input[name='net_addr']");

        if (node_array.length > 0)
        {
            cookies.nodes = new Array();
            $("input[name='net_addr']:checked").each(function () {
                cookies.nodes.push($(this).val());
            });
            cookies.group = $("input[name='group']:hidden").val();
            cookies.platform = $("input[name='platform']:hidden").val();
        }
        else if (!(group == undefined || group == ''))
        {
            cookies.group = group;
            cookies.platform = $("input[name='platform']:hidden").val();
        }
        else if (!(platform == undefined || platform == ''))
            cookies.platform = platform;
        else
        {
            cookies.group = $("input[name='group']:hidden").val();
            cookies.platform = $("input[name='platform']:hidden").val();
        }
    }

    // console.log(cookies);

    return cookies;
}

function GoForward()
{
    var cookies = ComposeCookies();

    UpdatePage(cookies);
}

function GoCancel()
{
    var cookies = ComposeCookies();
    //console.log(cookies);

    if (cookies.nodes !== undefined)
    {
        cookies.nodes = [];
        $("input[name='net_addr']:checked").each(function () {
            $(this).prop('checked', false);
        });
    }
    else if (cookies.group !== undefined)
    {
        if (cookies.group == null || cookies.group == 'None')
        {
            delete cookies.group;
        }
        else
        {
            cookies.group = null;
        }
        $("input[name='group']:checked").prop('checked', false);
    }
    else if (cookies.platform !== undefined)
    {
        cookies.platform = null;
        $("input[name='platform']:checked").prop('checked', false);
    }

    GetForm('table', cookies);
    //console.log(cookies);
    $("#form").empty();
    //GetForm('form', cookies);
}

function GoBack()
{
    var cookies = ComposeCookies();

    if (cookies.nodes !== undefined)
        delete cookies.nodes;
    else if (cookies.group !== undefined)
        delete cookies.group;
    else if (cookies.platform !== undefined)
        delete cookies.platform;

    UpdatePage(cookies);
}

function NewGroup()
{
    var cookies = ComposeCookies();
    cookies.group = null;
    $("input[name='group']:checked").prop('checked', false);
    GetForm('form', cookies)
}

function CheckGroup()
{
    var cookies = ComposeCookies();
    if (cookies.group === undefined)
        cookies.group = null;

    GetForm('table', cookies);
    $("#form").empty();
}

function CheckNode()
{
    var cookies = ComposeCookies();
    if (cookies.nodes === undefined)
        cookies.nodes = new Array();

    UpdatePage(cookies);
}

function UpdateCheckAll(node_number)
{
    if (node_number == 0)
    {
        $("input:checkbox[name='net_addr_all']").prop('indeterminate', false);
        $("input:checkbox[name='net_addr_all']").prop('checked', false);
    }
    else if (node_number == $("input:checkbox[name='net_addr']").length)
    {
        $("input:checkbox[name='net_addr_all']").prop('indeterminate', false);
        $("input:checkbox[name='net_addr_all']").prop('checked', true);
    }
    else
    {
        $("input:checkbox[name='net_addr_all']").prop('indeterminate', true);
        $("input:checkbox[name='net_addr_all']").prop('checked', false);
    }
}

function CheckAll()
{
    var check_all_state = $("input:checkbox[name='net_addr_all']").prop('checked');

    $("input:checkbox[name='net_addr']").each(function () {
        $(this).prop('checked', check_all_state)
    });

    var cookies = ComposeCookies();
    UpdatePage(cookies);
}

function UpdatePage(cookies)
{
    GetForm('table', cookies);
    GetForm('form', cookies);
}

// Collapsible Groups
function CreateGroup(group_name)
{
    // Create Button(Image)
    $('td.' + group_name).prepend("<img class='" + group_name + " button_closed'> ");
    // Align Data
    $('td.' + group_name).css('text-align', 'left');
    $('tr.' + group_name).each(function () {
        var first_td = $(this).find('td').first();
        var padding_left = parseInt($(first_td).css('padding-left'));
        $(first_td).css('text-align', 'left');
        $(first_td).css('padding-left', String(padding_left + 25) + 'px');
    });
    RestoreGroup(group_name);

    // Tie toggle function to the button
    $('img.' + group_name).click(function(){
        ToggleGroup(group_name);
    });
}

function ToggleGroup(group_name)
{
    ToggleButton($('img.' + group_name));
    RestoreGroup(group_name);
}

function RestoreGroup(group_name)
{
    if ($('img.' + group_name).hasClass('button_open'))
    {
        // Open everything
        $('tr.' + group_name).show();
        $('select.' + group_name).hide();

        // Close subgroups that been closed
        $('tr.' + group_name).find('img.button_closed').each(function () {
            sub_group_name = $(this).attr('class').split(/\s+/)[0];
            //console.log(sub_group_name);
            RestoreGroup(sub_group_name);
        });
    }

    if ($('img.' + group_name).hasClass('button_closed'))
    {
        // Close everything
        $('tr.' + group_name).hide();
        $('select.' + group_name).show();
    }
}

function ToggleButton(button)
{
    $(button).toggleClass('button_open');
    $(button).toggleClass('button_closed');
}

function UpdateWarnings(column_name, group_name)
{
    var group_select = $('select.' + group_name + "[name='" + column_name + "']");
    $(group_select).find("option[value='multiple']").remove();

    var update_value = $(group_select).val();
    //console.log(update_value);

    $('tr.' + group_name).find("select[name$='" + column_name + "']").each(function () {
        $(this).val(update_value);
    });


    var group_names = $(group_select).closest('tr').attr('class');
    if (group_names.length > 0)
    {
        //console.log(group_names);
        UpdateGroups(column_name, group_names);
    }
}

function UpdateGroups(column_name, group_names)
{
    var groups = group_names.split(' ');

    for (var group_index = 0; group_index < groups.length; group_index++) {
        group_name = groups[group_index];

        var update_value = null;
        $('tr.' + group_name).find("select[name$='-" + column_name + "']").each(function () {
            var this_value = $(this).val();
            if (update_value == null){
                update_value = this_value;
            }
            else if (update_value != this_value)
            {
                update_value = 'multiple';
            }

        });

        //console.log(update_value);

        var group_select = $('select.' + group_name + "[name='" + column_name + "']");
        var multiple_option = $(group_select).find("option[value='multiple']");

        if (update_value == 'multiple')
        {
            if (multiple_option.length < 1)
            {
                $(group_select).prepend("<option value='" + update_value + "'>Multiple</option>");
            }
        }
        else
        {
            $(multiple_option).remove();
        }

        $(group_select).val(update_value);
    }
}

function DisableMultiple(constant_name)
{
    $("input[name='" + constant_name + "-Multiple']").hide();
    $("input[name='" + constant_name + "-Multiple']").prop('disabled', true);
    $("input[name='" + constant_name + "']").show();
    $("input[name='" + constant_name + "']").focus();
}

function OverlayIsOpen()
{
    return Boolean($("[id$='_overlay']:not(.hidden)").length > 0);
}

function Overlay(on_off)
{
    var overlay_selection;
    if (on_off != false)
    {
        overlay_selection = on_off;
        on_off = true;
    }

    // Do not toggle overlay if something is up already
    if (!OverlayIsOpen() || on_off == false || overlay_selection == 'software')
    {
        // Hide everything
        $("[class^='overlay']").each(function () {
            $(this).toggleClass('invisible', !(on_off));
        });


        $("[id$='_overlay']").each(function () {
            $(this).toggleClass('hidden', true);
        });

        if (overlay_selection !== undefined)
        {
            $("#" + overlay_selection + '_overlay').toggleClass('hidden', false);
        }
    }
}

//-->
