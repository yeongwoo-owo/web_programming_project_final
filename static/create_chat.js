function find_members() {
    let members = [];
    $('#friend_list_form').find('input:checked').each(function () {
        members.push(parseInt($(this)[0].id));
    });
    return members;
}

function create_groupchat() {
    let members = find_members();
    let name = $('#chatroom_name').val();
    console.log(name);
    let data = {
        name: name,
        member_ids: members
    };
    console.log(JSON.stringify(data));
    $.ajax({
        url: "/groupchat",
        type: "POST",
        contentType: "application/json; charset=utf-8",
        data: JSON.stringify(data)
    }).done(function (json) {
        window.location.replace(json["redirect_url"]);
    });
}

$(document).ready(function () {
    $("#submit_button").click(function () {
        create_groupchat();
    });
})