
%### INCLUDES ###
%from gate.tpl import checked, hidden, get_options, DATA_RATE

<p>Channel:
    <select name='channel' >
        {{!get_options(range(16), network['channel'])}}
    </select>
</p>
<p>Data Rate:
    <select name='data_rate' >
        {{!get_options(DATA_RATE, network['data_rate'])}}
    </select>
</p>
<p>AES Enable:
    <input type='radio' name='aes_enable' value='1' onclick="DisplayForm('AESKey')"
    {{checked(network['aes_enable'] == 1)}} >On
    <input type='radio' name='aes_enable' value='0' onclick="HideForm('AESKey')"
    {{checked(network['aes_enable'] == 0)}} >Off
</p>
%# AES Key
<span id='AESKey' {{!hidden(network['aes_enable'] == 0)}} >
    <p>AES Key:
        <input type='text' name='aes_key' value="{{network['aes_key']}}" size='18' >
        <small>*You may enter up to 16 characters</small>
    </p>
</span>
    
