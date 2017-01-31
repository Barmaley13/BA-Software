
<script><!--
    function ShowTooltip(tooltip_id, content, x, y)
    {
        var tooltip = $("<div id='" + tooltip_id + "'>" + content + "</div>").css({
            position: "absolute",
            display: "none",
            top: y - 35,
            left: x - 23,
            border: "1px solid #fdd",
            padding: "2px",
            "background-color": "#fee",
            opacity: 0.80
        }).appendTo("body").fadeIn(200);
    }
//--></script>
