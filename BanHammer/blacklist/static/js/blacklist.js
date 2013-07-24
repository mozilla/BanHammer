function initPage() {
    setDuration(document.getElementById('id_duration').value);
    document.getElementById('id_timezone').innerHTML = getUTCOffset();
    document.getElementById('id_duration').onchange = changeDuration;
}

function zeroPad(value, pad) {
    value = value.toString();
    while( value.length < pad ) {
        value = '0' + value;
    }
    return value;
}

function getDateStr(date) {
    var month = zeroPad(date.getUTCMonth() + 1, 2);
    var day = zeroPad(date.getUTCDate(), 2);
    var year = date.getUTCFullYear();
    var hour = zeroPad(date.getUTCHours(), 2);
    var minute = zeroPad(date.getUTCMinutes(), 2);

    return month + '/' + day + '/' + year + ' ' + hour + ':' + minute;
}

function getUTCOffset() {
    var d = new Date();
    offset = -d.getTimezoneOffset() / 60;
    if( offset < 0 ) {
        return 'UTC ' + offset;
    } else if( offset > 0 ) {
        return 'UTC +' + offset;
    } else {
        return 'UTC';
    }
}

function setDates(offset) {
    var start = new Date();
    var diff = start.getTime() + ( offset * 1000 );
    var end = new Date(diff);

    document.getElementById('id_start_date').value = getDateStr(start);
    document.getElementById('id_end_date').value = getDateStr(end);
}

function changeDuration() {
    var value = document.getElementById('id_duration').value;
    setDuration(value);
}

function setDuration(value) {
    if( typeof(value) == 'undefined' || value == 0 ) {
        document.getElementById('id_start_date').readOnly=false;
        document.getElementById('id_end_date').readOnly=false;
    } else {
        setDates(value);
        document.getElementById('id_start_date').readOnly=true;
        document.getElementById('id_end_date').readOnly=true;
    }
}

