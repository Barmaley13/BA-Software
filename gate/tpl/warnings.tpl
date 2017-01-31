
%### INCLUDES ###
%from gate.tpl import checked

%### HTML ###
%if defined('warnings') and len(warnings) and defined('status_icon'):
    <h3>{{status_icon.title}}</h3>
    <table class='hor-minimalist-b' style='width:100%' >
        <thead>
            <tr>
                <th scope='col'>Time</th>
                <th scope='col'>Message</th>
                <th scope='col'>Acknowledgement</th>
            </tr>
        </thead>
        <tbody>
            %for warning in warnings:
                <tr>
                    <td>{{warning['time']}}</td>
                    %if 'generic' in warning['key']:
                        <td><b>{{warning['message']}}</b></td>
                    %else:
                        <td>{{warning['message']}}</td>
                    %end

                    <td>
                        <input type='checkbox' name="{{warning['key']}}"
                        onclick="UpdateWarningAck('{{warning['key']}}')" {{checked(not warning['ack'])}} >
                    </td>

                </tr>
            %end
        </tbody>
    </table>
%end
