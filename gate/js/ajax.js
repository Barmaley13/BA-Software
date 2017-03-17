<!--
// AJAX GET FUNCTIONS //
function RequestForm(data, JsonParser)
{    
    //console.log(data);
    
    //var url_array = data.url.split('/');
    //var form_id = url_array[url_array.length - 1];
    var error_message = '<p><small>Error: Unable to parse AJAX!</small></p>';

    var ajax_options = {
        url: window.location.protocol + "//" + window.location.hostname + "/ajax",
        type: "GET",
        data: {data: JSON.stringify(data)}
    };
    var request = $.ajax(ajax_options);
    //console.log(ajax_options);
    
    request.done(function(msg) {
        if (typeof JsonParser == "string")
        {
            if (typeof msg == "string")
                $("#" + JsonParser).html(msg);
            else
                $("#" + JsonParser).html(error_message);
        }
        else if (typeof JsonParser == "function"  && typeof msg == "object")
        {
            JsonParser(msg);
        }
        else
        {
            $("#form").html(error_message);
        }
    });
}

function GetForm(form_name, cookies)
{   
    if (form_name == 'form')
    {
        $("#form").empty();
    }

    var JsonData = new Object();
    JsonData.url = Path + '/' + form_name;
    if (cookies !== undefined)
    {
        if (typeof cookies !== 'object' || cookies === null)
        {
            JsonData.cookies = new Object();
            JsonData.cookies.index = cookies;
        }
        else
        {
            JsonData.cookies = cookies;
        }

        if ($('#tabs').length)
        {
            var active_tab = $("#tabs").tabs("option", "active");
            JsonData.cookies.active_tab = active_tab;
        }

        // console.log(JsonData.cookies);
    }
    
    RequestForm(JsonData, ParseForm);
}

function ParseForm(JsonData)
{
    ParseTable(JsonData);

    if (JsonData.form !== undefined)
        $("#form").html(JsonData.form);
}

// Generates Header Cookies //
function GenerateHeaderCookies()
{
    var cookies = new Object();

    var platforms = new Object();
    $("input[name='platform']").each(function() {

        var platform_name = $(this).val();
        platforms[platform_name] = new Object();

        var header_fields = $("input[name='" + platform_name + "_header']");
        if (header_fields.length > 0)
        {
            var selected_header = header_fields.filter(':checked');
            var nodes = $("input[name='net_addr']");
            if (selected_header.length > 0)
            {
                platforms[platform_name].selected = selected_header.val().replace(platform_name + '_', '');
            }
            else if (nodes.length > 0)
            {
                platforms[platform_name].selected = new Object();
                nodes.each(function (){
                    //var node_enables = 0;
                    var net_addr = $(this).val();

                    platforms[platform_name].selected[net_addr] = new Array();
                    $("input[name='log_"+$(this).val()+"']:checked").each(function (){
                        platforms[platform_name].selected[net_addr].push($(this).val());
                    });

                });
            }

            var headers = new Object();
            header_fields.each(function() {
                var header_field = $(this).val();
                var header_name = header_field.replace(platform_name + '_', '');
                headers[header_name] = new Object();

                var units_fields = $("[name='" + header_field + "_units']");
                if (units_fields.length > 0)
                {
                    headers[header_name]['units'] = units_fields.val();
                }

                var table_units_fields = $("[name='" + header_field + "_table_units']");
                if (table_units_fields.length > 0)
                {
                    headers[header_name]['table_units'] = new Array();
                    table_units_fields.filter(':checked').each(function() {
                        headers[header_name]['table_units'].push($(this).val());
                    });
                }

            });

            platforms[platform_name].headers = headers;
        }

    });

    cookies.platforms = platforms;

    //console.log(cookies);

    return cookies;
}

// AJAX JSON FUNCTIONS //
function GetLiveData(preserve_old_cookies)
{
    preserve_old_cookies = preserve_old_cookies === undefined ? false : preserve_old_cookies;

    var JsonData = new Object();
    JsonData.url = Path + '/table';

    if (preserve_old_cookies == false)
    {
        JsonData.cookies = GenerateHeaderCookies();
        //console.log(JsonData.cookies);
    }

    RequestForm(JsonData, ParseLiveDataTable);
}

function ParseLiveDataTable(JsonData)
{
    ParseTable(JsonData);

    if (JsonData.form !== undefined)
        ParseLiveDataForm(JsonData.form);
}

var plot = new Array();
function ParseLiveDataForm(JsonData)
{
    // console.log(JsonData);
    
    ParseDisplayWarnings(JsonData);
    
    if (JsonData.nodes !== undefined)
    {
        plot = [];
        // Remove old tooltips
        $("[id^='tooltip']").remove();

        for(i=0; i < JsonData.nodes.length; i++)
        {
            // Fill in Table header
            $("#node" + (i).toString()).html(JsonData.nodes[i].name);
           
            // Fill in Table body
            if (JsonData.nodes[i].series)
            {
                plot[i] = $.plot("#chart" + (i).toString(), JsonData.nodes[i].series, JsonData.nodes[i].options);
                
                var series = plot[i].getData();
                //console.log(series);
                for (var j = 0; j < series.length; j++)
                {
                    if (series[j].data.length)
                    {
                        var x = series[j].data[0][0];
                        var y = series[j].data[0][1];
                        //alert("x:"+x+"\ny:"+y);
                        var chart = $('#chart'+(i).toString()).offset();
                        //alert("Chart Offset\nx:"+chart.left+"\ny:"+chart.top);
                        var point = plot[i].pointOffset({x:x, y:y, xaxis:1, yaxis:j+1});
                        //alert("Point Offset\nx:"+point.left+"\ny:"+point.top);
                        var tooltip_id = 'tooltip' + i.toString() + j.toString();
                        var tooltip_content = y;
                        var tooltip_x = chart.left + point.left;
                        var tooltip_y = chart.top + point.top;
                        ShowTooltip(tooltip_id, tooltip_content, tooltip_x, tooltip_y);
                        
                        //Presence via bar color
                        plot[i].highlight(j, 0);
                        
                        /*
                        // Obsolete presence via transparency
                        var presence = JsonData.nodes[i].presence;
                        if(presence > 0)
                            plot[i].highlight(j, 0);
                        else
                            plot[i].unhighlight(j, 0);
                        */  
                    }
                }
            }
            else if(JsonData.nodes[i].warning)
                $("#chart" + (i).toString()).html('<p><small>' + JsonData.nodes[i].warning + '</small></p>');
            else
                $("#chart" + (i).toString()).empty();
            
            // Fill in Table footer
            for (data_field in JsonData.nodes[i].data)
            {
                data_value = JsonData.nodes[i].data[data_field]
                field_name = data_field + (i).toString();
                if (data_value)
                    $("#" + field_name).html(data_value);
                else
                    $("#" + field_name).empty();
            }
            
        }
    }
}

var SinglePoint = false
function GetLogData(preserve_old_cookies, single_point)
{
    SinglePoint = single_point === undefined ? false : single_point;
    preserve_old_cookies = preserve_old_cookies === undefined ? false : preserve_old_cookies;

    var JsonData = new Object();
    JsonData.url = Path + '/table';

    if (preserve_old_cookies == false)
    {
        JsonData.cookies = GenerateHeaderCookies();

        // set default for optional parameter
        JsonData.cookies.single_point = SinglePoint;

        JsonData.cookies.export_net_addr = $("select[name='net_addr']").val();

        //console.log(JsonData.cookies);
    }

    RequestForm(JsonData, ParseLogsTable);
}

function ParseLogsTable(JsonData)
{
    ParseTable(JsonData);

    if (JsonData.form !== undefined)
    {
        // console.log(JsonData.form);
        ParseLogsForm(JsonData.form);
    }
}

function ParseLogsForm(JsonData)
{
    //console.log(JsonData);
    
    ParseDisplayWarnings(JsonData);

    if(JsonData.series !== undefined)
    {
        var newData, newOptions, originalData, appendData, mergedData;
        if (SinglePoint)
        {
            if (plot !== undefined && typeof plot.getData === 'function')
            {
                newData = plot.getData();
                for(i=0; i < newData.length; i++)
                {
                    //console.log(i);
                    originalData = newData[i].data;
                    if (i < JsonData.series.length)
                        appendData = JsonData.series[i].data;
                    
                    //console.log(originalData);
    
                    //console.log(originalData.length);                       
                    if (originalData.length !== undefined && appendData !== undefined)
                    {
                        if (appendData.length !== undefined)
                        {
                            //console.log(appendData);
                            if ((originalData.length + appendData.length) > LogLimit)
                                originalData.splice(0,1);
                            mergedData = originalData.concat(appendData);
                            newData[i].data = mergedData;
                            //console.log(mergedData);
                        }
                        else
                            newData[i].data = originalData;
                    }
                    else
                        newData = JsonData.series;
                }
    
                newOptions = plot.getOptions();
                //console.log(newOptions);
                //console.log(JsonData.options);
                $.extend(true, newOptions, JsonData.options);
                //console.log(newOptions);
            }
            else
            {
                newData = JsonData.series;
                newOptions = JsonData.options;
            }
            
            plot = $.plot("#form", newData, newOptions);
        }
        else
        {
            //console.log(JsonData.options);
            plot = $.plot("#form", JsonData.series, JsonData.options);
            //var newOptions = plot.getOptions();
            //console.log(newOptions);
        }
      
        $("<div class='zoom'>Zoom Out</div>").appendTo($("#form")).click(function (event){
            event.preventDefault();
            plot.zoomOut();
        });
  
        //$("<div class='axisLabel yaxisLabel'>Meters</div>").appendTo($("#form"));
     
        /*
        for (i=0; i < json.series.length; i++)
        {
            if (json.series[i]["yaxis"])
            {
                if (json.series[i]["yaxis"] == 2)
                    $("<div class='axisLabel yaxisLabel2'>%</div>").appendTo($("#form"));
            }
        }
        */
    }
}

function ParseTable(JsonData)
{
    if (JsonData.buttons !== undefined)
        $("#buttons").html(JsonData.buttons);

    if (JsonData.page_controls !== undefined)
        $("#page_controls").html(JsonData.page_controls);
        
    if (JsonData.table !== undefined)
        $("#table").html(JsonData.table);

    if (JsonData.software_overlay !== undefined && !OverlayIsOpen())
        $('#software_overlay').html(JsonData.software_overlay);

    if (JsonData.status_icons !== undefined)
    {
        $.each(JsonData.status_icons, function(status_icon_key, status_json){
            if (status_json.status_message !== undefined)
                StatusMessage(status_icon_key, status_json.status_message);

            if (status_json.current_icon !== undefined)
                StatusIcon(status_icon_key, status_json.current_icon, status_json.sound_enable);

            if (status_json.pop_up_enable !== undefined)
                StatusPopMessage(status_icon_key, status_json.pop_up_enable);

            if (status_json.sound_enable !== undefined)
                StatusSound(status_icon_key, status_json.sound_enable);

            if (status_json.onclick_enable !== undefined)
                StatusIconOnClick(status_icon_key, status_json.onclick_enable);
        });
    }

    if (JsonData.alert !== undefined)
        alert(JsonData.alert);
}

function ParseDisplayWarnings(JsonData)
{
    if (JsonData.display_warnings !== undefined)
    {
        $("#display_warnings").show();
        $("#display_warnings_html").html(JsonData.display_warnings);
    }
    else
    {
        $("#display_warnings").hide();
        $("#display_warnings_html").empty();
    }

    if (JsonData.alert !== undefined)
        alert(JsonData.alert);
}

function GetDiagnostics(preserve_old_cookies)
{  
    preserve_old_cookies = preserve_old_cookies === undefined ? false : preserve_old_cookies;

    var cookies;
    if (preserve_old_cookies == false)
    {
        var cookies = GenerateHeaderCookies();
        //console.log(cookies);
    }

    GetForm('table', cookies);
}

// AJAX USER VALIDATION //
function GetNameValidation()
{
    var JsonData = new Object();
    JsonData.url = Path + '/name_validation';
    JsonData.kwargs = new Object();

    if ($("input[name='username']").length)
        JsonData.kwargs.prospective_name = $("input[name='username']").val();
    else if ($("input[name='group_name']").length)
        JsonData.kwargs.prospective_name = $("input[name='group_name']").val();
    else if ($("input[name='snmp_name']").length)
        JsonData.kwargs.prospective_name = $("input[name='snmp_name']").val();

    if ($("input[name='total_access']").length)
        JsonData.kwargs.access = $("input[name='total_access']").val();

    if ($("input[name='active']").length)
        JsonData.kwargs.active = $("input[name='active']").prop('checked');
    else
        JsonData.kwargs.active = true;

    RequestForm(JsonData, ParseNameValidation);
}

var name_taken = false;
var admin_present = false;
function ParseNameValidation(JsonData)
{
    if (JsonData.buttons !== undefined)
        $("#buttons").html(JsonData.buttons);
    if (JsonData.form !== undefined)
        $("#name_validation").html(JsonData.form);
    if ('name_taken' in JsonData)
        name_taken = Boolean(JsonData.name_taken);
    if ('admin_present' in JsonData)
        admin_present = Boolean(JsonData.admin_present);
}

function UpdateWarningAck(warning_key)
{
    var JsonData = new Object();
    JsonData.url = Path + '/ack_update';
    JsonData.kwargs = new Object();
    JsonData.kwargs.warning_key = warning_key;
    JsonData.kwargs.ack_value = $("input:checkbox[name='" + warning_key + "']").prop('checked');

    RequestForm(JsonData, ParseTable);
}

// MISC AJAX FUNCTIONS, NUMEROUS METHODS //
function TryAjaxFileUpload(form)
{
    var support_ajax_file_upload = SupportAjaxFileUpload();

    if (support_ajax_file_upload)
    {
        // Trigger software overlay right here
        var form_data = new FormData(form);
        form_data.append('ajax', 'true');
        form_data.append('data', form.data.files[0]);

        SoftwareOverlay(form_data, form.getAttribute('action'));
    }

    return ! support_ajax_file_upload;
}

function SupportAjaxFileUpload()
{
    return supportFileAPI() && supportAjaxUploadProgressEvents() && supportFormData();

    // Is the File API supported?
    function supportFileAPI() {
        var fi = document.createElement('INPUT');
        fi.type = 'file';
        return 'files' in fi;
    };

    // Are progress events supported?
    function supportAjaxUploadProgressEvents() {
        var xhr = new XMLHttpRequest();
        return !! (xhr && ('upload' in xhr) && ('onprogress' in xhr.upload));
    };

    // Is FormData supported?
    function supportFormData() {
        return !! window.FormData;
    }
}

function SoftwareOverlay(JsonData, uri)
{
    Overlay(false);
    $('#overlay_cancel').show();
    $('#overlay_okay').hide();
    Overlay('software');

    if (JsonData instanceof FormData)
    {
        sendXHRequest(JsonData, uri);

        // DOES NOT WORK FOR WHATEVER REASON...
//        var request = $.ajax({
//            url: uri,
//            type: "POST",
//            // Custom XMLHttpRequest
//            xhr: function() {
//                var myXhr = $.ajaxSettings.xhr();
//                return myXhr;
//            },
//            success: ParseSoftwareOverlay,
//            cache: false,
//            contentType: false,
//            processData: false
//        });
    }
    else if (JsonData !== undefined)
    {
        var request = $.post('', JsonData);
        request.done(ParseSoftwareOverlay);
    }

}

function ParseSoftwareOverlay(JsonData)
{
    // console.log(JsonData);

    if (JsonData.alert !== undefined)
        alert(JsonData.alert);

    if (JsonData.new_cookie !== undefined)
        UpdatePage(JsonData.new_cookie);

    if (JsonData.software_overlay !== undefined)
        $('#software_overlay').html(JsonData.software_overlay);

}

function sendXHRequest(formData, uri)
{
    // Get an XMLHttpRequest instance
    var xhr = new XMLHttpRequest();
    // Set up events
    xhr.addEventListener('readystatechange', onreadystatechangeHandler, false);
    // Set up request
    xhr.open('POST', uri, true);
    // Fire!
    xhr.send(formData);
}

// Handle the response from the server
function onreadystatechangeHandler(evt)
{
    var status, response, readyState;
    try {
        readyState = evt.target.readyState;
        response = evt.target.responseText;
        status = evt.target.status;
    }
    catch(e) {
        return;
    }

    if (readyState == 4 && status == '200' && response) {
        JsonData = JSON.parse(response);
        ParseSoftwareOverlay(JsonData);
    }
}

function SubmitAction(submit_name, action_name)
{
    $("[name='action_method']").val(action_name);
    //$("#form").submit();
    $("input[name='" + submit_name + "_submit']").click();
}
   
// HELPER FUNCTIONS //
/*
function IsNumber(n)
{
    return !isNaN(parseFloat(n)) && isFinite(n);
}
*/
//-->
