function add_friend(friend_id) {
    console.log("add friend " + friend_id);
    $.ajax({
        url: "/friends/" + friend_id,
        type: "POST",
    }).done(function () {
        let button = $("#user_" + friend_id);
        button.replaceWith(friend_button_builder(friend_id, true));
    });
}

function friend_button_builder(friend_id, is_friend) {
    let str = '<button id="user_' + friend_id + '" style="width: fit-content; height: fit-content" class="btn ';
    str += is_friend ? 'btn-light disabled' : 'btn-warning';
    str += '" type="submit" onclick="add_friend(' + friend_id + ')">';
    str += is_friend ? '추가 완료' : '친구 추가';
    str += '</button>';
    return str
}

$(document).ready(function () {
    $("#friend-input").on("keyup", function () {
        let query = $(this).val();
        console.log("query: " + query);
        if (query !== "") {
            $.ajax({
                url: "/users?query=" + query,
                type: "GET",
                dataType: "json"
            }).done(function (json) {
                let results = json["result"];
                let ui = $("#result");
                ui.empty();

                if (results.length > 0) {
                    ui.append('<hr class="text-light">');
                }

                let html = '';
                results.forEach((result) => {
                    html += '<div class="m-3 row justify-content-between align-items-center">';
                    html += '   <p class="p-0 col text-light fs-3 mb-0">' + result.user.name + '</p>';
                    html += friend_button_builder(result.user.id, result.is_friend)
                    html += '</div>';
                    html += '<hr class="text-light">'
                });
                ui.append(html);
            });
        }
    });
});