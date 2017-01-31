
%### INCLUDES ###
%from bottle import template

%from gate.main import manager, pages


%### JS ###
<script><!--

function StatusMessage(status_id, status_message)
{
    $('#' + status_id + '_message').html(status_message);
}

function StatusIcon(status_id, status_icon_src)
{
    $('#' + status_id + '_icon').attr('src', status_icon_src);
}

function StatusPopMessage(status_id, status_pop_up_enable)
{
    %if manager.system_settings['warnings_pop_up_enable']:
        if (status_pop_up_enable)
        {
            %# Show Overlay
            if ($('#' + status_id + '_overlay').is(':hidden'))
            {
                Overlay(status_id);
            }
        }
    %else:
        return;
    %end

}

function StatusSound(status_id, status_sound_enable)
{
    %if manager.system_settings['warnings_sound_enable']:
        %# Automatic Sound
        if (status_sound_enable)
            audioElement.play();
        else
            audioElement.pause();
    %else:
        return;
    %end
}

function StatusIconOnClick(status_id, onclick_enable)
{
    if (onclick_enable)
        $('#' + status_id + '_icon').attr('onclick', "Overlay('" + status_id + "')");
    else
        $('#' + status_id + '_icon').attr('onclick', '');
}

%# Audio
%if manager.system_settings['warnings_sound_enable']:
    var audioElement = document.createElement('audio');
    $(document).ready(function() {
        audioElement.setAttribute('src', '/audio/ride_of_the_valkyries.mp3');
        audioElement.addEventListener('ended', function() {
            this.currentTime = 0;
            this.play();
        }, false);
    });
%end

//--></script>


%### HTML ###
<div class='overlay1 invisible'></div>
<div class='overlay2 invisible'>
    <div class='overlay3 invisible'>
        {{!pages.status_icons_overlay()}}
        
        %# Software Overlay aka Progress Bar #
        <div id='software_overlay' class='hidden'>
            {{!template('software_overlay')}}
        </div>
    </div>
</div>
