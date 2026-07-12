// ---------- 요약 (기존) ----------
const btn = document.getElementById("go");
const result = document.getElementById("result");

btn.onclick = async () => {
    btn.disabled = true;
    result.innerHTML = "";
    try {
        const res = await fetch("list.php");
        const data = await res.json();
        for (const item of data.items) {
            const card = document.createElement("div");
            card.className = "card";
            card.innerHTML = '<h3><a target="_blank"></a></h3><p class="muted">요약 중...</p>';
            card.querySelector("a").href = item.url;
            card.querySelector("a").textContent = item.title;
            result.appendChild(card);
            try {
                const r = await fetch("summarize.php", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({url: item.url, title: item.title})
                });
                const d = await r.json();
                card.querySelector("p").textContent = d.summary ?? d.error ?? "요약 실패";
                card.querySelector("p").className = "";
            } catch (e) {
                card.querySelector("p").textContent = "요약 실패";
            }
        }
    } catch (e) {
        result.textContent = "목록을 가져오지 못했습니다.";
    }
    btn.disabled = false;
};

// ---------- 챗봇 ----------
const chatbox = document.getElementById("chatbox");
const chatinput = document.getElementById("chatinput");
const sendBtn = document.getElementById("send");
let sessionId = null;   // 첫 응답 후 자동 유지

function addBubble(role, text, sources) {
    const div = document.createElement("div");
    div.className = "msg " + role;
    const span = document.createElement("span");
    span.textContent = text;
    div.appendChild(span);
    if (sources && sources.length > 0) {
        const s = document.createElement("p");
        s.className = "srcs";
        for (const src of sources) {
            const a = document.createElement("a");
            a.href = src.url;
            a.target = "_blank";
            a.textContent = "#" + src.topic_id;
            a.title = src.title;
            s.appendChild(a);
        }
        div.appendChild(s);
    }
    chatbox.appendChild(div);
    chatbox.scrollTop = chatbox.scrollHeight;
    return span;
}

async function sendMessage() {
    const q = chatinput.value.trim();
    if (q === "") return;
    chatinput.value = "";
    sendBtn.disabled = true;
    addBubble("user", q);
    const pending = addBubble("model", "생각 중...");
    const pendingMsg = pending.parentElement;
    try {
        const r = await fetch("chat.php", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({question: q, session_id: sessionId})
        });
        const d = await r.json();
        pendingMsg.remove();
        if (d.error) {
            addBubble("model", "오류: " + d.error);
        } else {
            sessionId = d.session_id;
            addBubble("model", d.answer, d.sources);
        }
    } catch (e) {
        pendingMsg.remove();
        addBubble("model", "요청 실패");
    }
    sendBtn.disabled = false;
    chatinput.focus();
}

sendBtn.onclick = sendMessage;
chatinput.addEventListener("keydown", e => {
    if (e.key === "Enter") sendMessage();
});
