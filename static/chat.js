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
            addChatUI(login_id, chat)
        });
        scrollToTop();
    });

    ws = new WebSocket("ws://localhost:8000/ws/connect");
    ws.onmessage = function (event) {
        console.log(event.data);
        let json = JSON.parse(event.data);
        console.log(json);
        addChat(login_id, json);
    };

    $('#input-text').on('keydown', function (event) {
        if (event.keyCode === 13) {
            if (!event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
    });

    $('#input-button').click(function () {
        sendMessage();
    });

    function sendMessage() {
        let text = $('#input-text').val();
        if (text === "") {
            return;
        }
        let data = JSON.stringify({
            writer_id: login_id,
            chatroom_id: chatroom_id,
            text: text
        });
        console.log(data);
        ws.send(data);
    }
});

function addChat(login_id, chat) {
    addChatUI(login_id, chat);
    clearText($('#input-text'))
    scrollToTop();
}

function addChatUI(login_id, chat) {
    let ui = $('#chat-list');
    ui.append(`
        <div class="chat ${getUserTag(login_id, chat)}">
            <div class="chat-writer text-light">${chat.writer.name}</div>
            <div class="chat-row">
                <div class="chat-text">${convertToHtml(chat.text)}</div>
                <div class="chat-time text-light">${chat.time}</div>
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
    ui.scrollTop(ui[0].scrollHeight);
}