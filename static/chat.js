let height = 0;

$(document).ready(function () {
    let login_id;
    let chatroom_id;
    let ws;

    $.ajax({
        url: window.location + "/chats",
        type: "get",
        contentType: "application/json; charset=utf-8",
    }).done(function (json) {
        console.log(json);
        login_id = json["login_user"];
        chatroom_id = json["chatroom_id"];
        json["chats"].forEach(chat => {
            let chat_type = chat["chat_type"];
            if (chat_type === "text") {
                addTextChat(login_id, chat);
            } else if (chat_type === "image") {
                addImageChat(login_id, chat);
            } else if (chat_type === "video") {
                addVideoChat(login_id, chat);
            }
        });
        height = scrollToTop(height);
        console.log("height: " + height);
    });

    ws = new WebSocket("ws://localhost:8000/ws/connect");
    ws.onmessage = function (event) {
        let json = JSON.parse(event.data);
        console.log(json);

        let chat_type = json["chat_type"];
        if (chat_type === "text") {
            addTextChat(login_id, json);
        } else if (chat_type === "image") {
            addImageChat(login_id, json);
        } else if (chat_type === "video") {
            addVideoChat(login_id, json);
        }
        height = scrollToTop(height);
        console.log("height: " + height);
    };

    $('#input-text').on('keydown', function (event) {
        if (event.keyCode === 13) {
            if (!event.shiftKey) {
                event.preventDefault();
                sendText();
            }
        }
    });

    $('#input-button').click(function () {
        sendText();
    });

    $('#image-input').change(function () {
        let image = $(this)[0].files[0];
        console.log(image);

        let data = new FormData();
        data.append("file", image);

        $.ajax({
            url: "/images",
            type: "post",
            contentType: false,
            processData: false,
            data: data
        }).done(function (json) {
            console.log(json)
            sendImage(json["id"])
        });
    })

    function sendText() {
        let text = $('#input-text').val();
        if (text === "") {
            return;
        }
        let data = JSON.stringify({
            writer_id: login_id,
            chatroom_id: chatroom_id,
            text: text,
            chat_type: "text"
        });
        console.log(data);
        ws.send(data);
    }

    function sendImage(imageId) {
        let data = JSON.stringify({
            writer_id: login_id,
            chatroom_id: chatroom_id,
            image_id: imageId,
            chat_type: "image"
        });
        console.log(data);
        ws.send(data);
    }
});

function addTextChat(login_id, chat) {
    addTextChatUI(login_id, chat);
    clearText($('#input-text'));
}

function addTextChatUI(login_id, chat) {
    let ui = $('#chat-list');
    ui.append(`
        <div class="chat ${getUserTag(login_id, chat)}">
            <div class="chat-writer text-light">${chat.writer.name}</div>
            <div class="chat-row">
                <div class="chat-text">${convertToHtml(chat.text)}</div>
                <div class="chat-time text-light">${parseTime(chat.time)}</div>
            </div>
        </div>
    `);
}


function addImageChat(login_id, chat) {
    addImageChatUI(login_id, chat);
}

function addImageChatUI(login_id, chat) {
    let ui = $('#chat-list');
    let width = window.innerWidth;
    ui.append(`
        <div class="chat ${getUserTag(login_id, chat)}">
            <div class="chat-writer text-light">${chat.writer.name}</div>
            <div class="chat-row">
                <div class="chat-image"><img src="http://localhost:8000/images/${chat["image"]["image_name"]}" width="${width / 100 * 60}" height="auto" 
                onclick="window.open('http://localhost:8000/images/${chat["image"]["image_name"]}')" onload="scrollToTop()"></div>
                <div class="chat-time text-light">${parseTime(chat.time)}</div>
            </div>
        </div>
    `)
}

function addVideoChat(login_id, chat) {
    addVideoChatUI(login_id, chat);
}

function addVideoChatUI(login_id, chat) {
    let ui = $('#chat-list');
    let width = window.innerWidth;
    ui.append(`
        <div class="chat ${getUserTag(login_id, chat)}">
            <div class="chat-writer text-light">${chat.writer.name}</div>
            <div class="chat-row">
                <div class="chat-video">
                    <video class="video" src="http://localhost:8000/images/${chat["image"]["image_name"]}" width="${width / 100 * 60}" height="auto" muted autoplay
                        onclick="window.open('http://localhost:8000/images/${chat["image"]["image_name"]}')" onload="scrollToTop()"></video>
                </div>
                <div class="chat-time text-light">${parseTime(chat.time)}</div>
            </div>
        </div>
    `);
}

function convertToHtml(text) {
    return text.replaceAll("\n", "<br>");
}

function getUserTag(login_id, chat) {
    return chat.writer_id === login_id ? "me" : "other";
}

function clearText(ui) {
    ui.val("");
}

function scrollToTop() {
    let ui = $('#chat-list');
    let curHeight = ui[0].scrollHeight;
    if (height !== curHeight) {
        console.log("change from " + height + " to " + curHeight);
        ui.scrollTop(curHeight);
        height = curHeight;
    }
    return curHeight;
}

function parseTime(time) {
    let date = new Date(time);
    // console.log(date);
    let hour = date.getHours();
    let minute = date.getMinutes();
    let a = hour >= 12 ? "오후" : "오전";
    hour = (hour - 1) % 12 + 1;
    return a + " " + hour + ":" + minute.toString().padStart(2, '0');
}