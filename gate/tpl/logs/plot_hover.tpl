
<script><!--
    var previousPoint = null;
    $("#form").bind("plothover", function (event, pos, item)
    {
        if (item)
        {
            if (previousPoint != item.dataIndex)
            {
                previousPoint = item.dataIndex; 
                $("#tooltip").remove();
                var tooltip_content = item.datapoint[1];
                ShowTooltip('tooltip', tooltip_content, item.pageX, item.pageY);
            }
        }
        else
        {
            $("#tooltip").remove();
            previousPoint = null;            
        }
    });
//--></script>
