
%### HTML ###
%if defined('status_icon') and status_icon.modes is not None:
    <h3>{{status_icon.title}} Legend</h3>
    %if status_icon.internal_name == 'warnings':
        <table class='hor-minimalist-b' style='width:100%' >
            <thead><tr><th scope='col' rowspan='{{2 * len(status_icon.modes)}}'></th></tr></thead>
            <tbody>
                <tr>
                    %for mode, mode_description in status_icon.modes.items():
                        <td><input id='{{status_icon.internal_name}}_legend' type='image'
                        src='/img/{{status_icon.internal_name}}_{{mode}}.png'
                        alt='{{status_icon.title}}' title='{{status_icon.title}}' width='25' height='25' ></td>
                        <td>{{mode_description}}</td>
                    %end
                </tr>
            </tbody>
        </table>
    %else:
        <table class='hor-minimalist-b' style='width:100%' >
            <thead>
                <tr>
                    <th scope='col'>Icon</th>
                    <th scope='col'>Description</th>
                </tr>
            </thead>
            <tbody>
                %for mode, mode_description in status_icon.modes.items():
                    <tr>
                        <td>
                            <input id='{{status_icon.internal_name}}_legend' type='image'
                            src='/img/{{status_icon.internal_name}}_{{mode}}.png'
                            alt='{{status_icon.title}}' title='{{status_icon.title}}' width='25' height='25' >
                        </td>
                        <td>{{mode_description}}</td>
                    </tr>
                %end
            </tbody>
        </table>
    %end
%end
