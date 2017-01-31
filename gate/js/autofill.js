<!--
function AutoTimeoutValues()
{
	var wake = parseFloat(document.getElementsByName('wake')[0].value);
	var sleep = parseFloat(document.getElementsByName('sleep')[0].value);

	var timeout_wake = document.getElementsByName('timeout_wake')[0];
	var timeout_sleep = document.getElementsByName('timeout_sleep')[0];
	var autofill_enable = document.getElementsByName('autofill_enable')[0];

	if(autofill_enable.checked)
	{
		timeout_wake.value = sleep;
		timeout_sleep.value = sleep*sleep/wake;
	}
}

function AutoTimeout()
{
    var timeout_wake = document.getElementsByName('timeout_wake')[0];
    var timeout_sleep = document.getElementsByName('timeout_sleep')[0];
    var autofill_enable = document.getElementsByName('autofill_enable')[0];

    if(autofill_enable.checked)
    {
        // Autofill On
        timeout_wake.disabled = true;
        timeout_sleep.disabled = true;
    }
    else
    {
        // Autofill Off
        timeout_wake.disabled = false;
        timeout_sleep.disabled = false;
    }

    //alert(autofill_enable.value);

}

function AutoTime(automatic_update)
{
    var i, CurrentDate;
    var DateTimeArray = ['year', 'month', 'day', 'hours', 'minutes', 'seconds'];
    var UpdateTimeEnable = Boolean($("[name='system_time']:checked").val() > 0);
    var BrowserTimeEnable = Boolean($("[name='browser_time']:checked").val() > 0);
    
    if (UpdateTimeEnable)
    {
        DisplayForm('SystemTime');
        if (BrowserTimeEnable)
        {
            CurrentDate = new Date();
            // Epoch Time in seconds
            $("[name='time']").val(CurrentDate.getTime()/1000);
        }
        else
        {
            CurrentDate = new Date($("[name='time']").val()*1000);
        }    
 
        for(i=0; i < DateTimeArray.length; i++)
        {
            $("input[name='" + DateTimeArray[i] + "']").attr("disabled", BrowserTimeEnable);
        }
    
        // Time Zone Offset in seconds
        $("[name='timezone']").val(CurrentDate.getTimezoneOffset()*60);
        if (BrowserTimeEnable || automatic_update === undefined)
        {
            $("input[name='year']").val(CurrentDate.getFullYear());
            $("input[name='month']").val(CurrentDate.getMonth() + 1);
            $("input[name='day']").val(CurrentDate.getDate());
            $("input[name='hours']").val(CurrentDate.getHours());
            $("input[name='minutes']").val(CurrentDate.getMinutes());
            $("input[name='seconds']").val(CurrentDate.getSeconds());
        }
    }
    else
    {
        HideForm('SystemTime');
        $("input[name='browser_time'][value='1']").prop('checked', true);
        $("[name='time']").val(null);
        $("[name='timezone']").val(null);
    }
}

function UpdateTime()
{
    var NewDate = new Date();
    NewDate.setFullYear($("input[name='year']").val());
    NewDate.setMonth($("input[name='month']").val() - 1);
    NewDate.setDate($("input[name='day']").val());
    NewDate.setHours($("input[name='hours']").val());
    NewDate.setMinutes($("input[name='minutes']").val());
    NewDate.setSeconds($("input[name='seconds']").val());
    $("[name='time']").val(NewDate.getTime()/1000);
    $("[name='timezone']").val(NewDate.getTimezoneOffset()*60);
}

function UpdateAddress(prefix)
{
    var i;
    var address = "";
    
    for(i=0; i < 4; i++)
    {
        if (i != 0)
        {
            address += ".";
        }
        address += $("input[name='" + prefix + i + "']").val();
    }
    $("input[name='" + prefix + "']").val(address);
}
//-->
