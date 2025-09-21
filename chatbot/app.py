# app.py
import os, secrets
import gradio as gr

from config import CSS, SUGGESTED_QUESTIONS, QA_PATH
from utils import append_lead, load_json, save_json
from admin import ADMIN_SESSIONS
from retriever import retriever  # ensures corpus is built
from app_logic import answer_query, health, ask_quick

# ---------- Client JS (runs in browser via demo.load) ----------
SPEECH_INIT_JS = r"""
() => {
  const DEBUG = true;
  const log  = (...a) => { if (DEBUG) console.log("[TTS]", ...a); };
  const warn = (...a) => { if (DEBUG) console.warn("[TTS]", ...a); };
  const err  = (...a) => { if (DEBUG) console.error("[TTS]", ...a); };
  const gr = () => (window.gradioApp ? window.gradioApp() : document);
  const $  = (sel, root = gr()) => root.querySelector(sel);
  const $$ = (sel, root = gr()) => Array.from(root.querySelectorAll(sel));
  function getChatbotRoots() {
    const appRoot = gr();
    const host = $("#chatbox", appRoot);
    const root = host && host.shadowRoot ? host.shadowRoot : appRoot;
    log("getChatbotRoots()", { hasGradioApp: !!window.gradioApp, host, hasShadow: !!(host && host.shadowRoot) });
    return { host: host || appRoot, root };
  }
  function resolveToggleInput(blockEl) {
    if (!blockEl) return null;
    let inp = blockEl.matches?.('input[type="checkbox"], [role="switch"]') ? blockEl : null;
    inp = inp || blockEl.querySelector?.('input[type="checkbox"]');
    inp = inp || blockEl.querySelector?.('[role="switch"]');
    if (!inp) {
      const scoped = $('#speak_toggle input[type="checkbox"]', gr()) ||
                     $('#speak_toggle [role="switch"]', gr());
      if (scoped) inp = scoped;
    }
    return inp;
  }
  function isSpeakOn(inp, blockEl) {
    if (inp) return !!inp.checked;
    const aria = blockEl && blockEl.getAttribute?.("aria-checked");
    if (aria === "true") return true;
    if (aria === "false") return false;
    return true; // default ON
  }
  function waitFor(selList, cb, tries = 0) {
    const { root } = getChatbotRoots();
    const els = selList.map(sel => root.querySelector(sel));
    if (els.every(Boolean)) { log("waitFor found", selList); return cb(...els); }
    if (tries % 10 === 0) log("waitFor retry", tries, selList);
    if (tries > 240) { warn("waitFor timed out", selList); return; }
    setTimeout(() => waitFor(selList, cb, tries + 1), 50);
  }
  try {
    const style = document.createElement("style");
    style.textContent = `
      #speak_toggle { position: relative; z-index: 10; }
      #speech_diag { font-size: 12px; opacity: .8; margin-left: 8px; }
      #speech_test_btn { margin-left: 8px; }
    `;
    document.head.appendChild(style);
  } catch (e) { warn("style append failed", e); }
  function pickMaleVoice(voices) {
    if (!voices || !voices.length) return null;
    let v = voices.find(v => /Google UK English Male|Google US English Male|Microsoft David/i.test(v.name));
    if (v) return v;
    v = voices.find(v => v.lang?.startsWith("en") && /male/i.test(v.name));
    if (v) return v;
    return voices.find(v => v.lang?.startsWith("en")) || voices[0] || null;
  }
  waitFor(["#speak_toggle"], (toggleBlock) => {
    log("init: toggle block found", toggleBlock);
    let toggleInput = resolveToggleInput(toggleBlock);
    log("resolved toggle input:", toggleInput);
    const parent = toggleBlock.parentElement || toggleBlock.closest("*") || document.body;
    const diag = document.createElement("span"); diag.id = "speech_diag"; diag.textContent = "loading voices…";
    const testBtn = document.createElement("button"); testBtn.id = "speech_test_btn"; testBtn.type = "button"; testBtn.textContent = "Test voice";
    parent.appendChild(testBtn); parent.appendChild(diag);
    let voices = []; let unlocked = false; let lastSpoken = "";
    function updateDiag(extra = "") {
      const count = (voices || []).length;
      const on = isSpeakOn(toggleInput, toggleBlock) ? "on" : "off";
      const text = `voices: ${count} • speak: ${on}${extra ? " • " + extra : ""}`;
      diag.textContent = text;
      log("diag:", text);
    }
    function loadVoices() {
      if (!("speechSynthesis" in window)) { diag.textContent = "speechSynthesis not available"; warn("no speechSynthesis"); return; }
      voices = window.speechSynthesis.getVoices() || [];
      log("voices loaded:", voices.map(v => `${v.name} (${v.lang})`));
      updateDiag();
    }
    if ("speechSynthesis" in window) {
      loadVoices();
      window.speechSynthesis.onvoiceschanged = () => { log("onvoiceschanged"); loadVoices(); };
    } else {
      updateDiag("no API");
      return;
    }
    function unlockIfNeeded() {
      if (!unlocked) {
        try { const u = new SpeechSynthesisUtterance(" "); u.volume = 0; window.speechSynthesis.speak(u); log("unlock: silent utterance"); }
        catch (e) { err("unlock error", e); }
        unlocked = true; updateDiag("unlocked");
      }
    }
    ["click","keydown","touchstart"].forEach(evt => window.addEventListener(evt, unlockIfNeeded, { once:true, capture:true }));
    function speakNow(text) {
      if (!isSpeakOn(toggleInput, toggleBlock)) { log("speakNow: toggle OFF (input:", !!toggleInput, ")"); return; }
      if (!text) { log("speakNow: empty"); return; }
      try {
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        const chosen = pickMaleVoice(voices);
        if (chosen) { u.voice = chosen; log("using voice:", chosen.name, chosen.lang); }
        u.rate = 1.0; u.pitch = 1.0; u.lang = (chosen && chosen.lang) || "en-US";
        window.speechSynthesis.speak(u);
        log("speaking:", text.slice(0,120));
      } catch (e) { updateDiag("error speaking"); err("speak error", e); }
    }
    testBtn.addEventListener("click", () => { log("test button"); unlockIfNeeded(); speakNow("Voice test. If you can hear this, speech synthesis is working."); });
    if (toggleInput) {
      toggleInput.addEventListener("change", () => { log("input change:", toggleInput.checked); if (!toggleInput.checked) window.speechSynthesis.cancel(); updateDiag(); });
    } else {
      toggleBlock.addEventListener("click", () => {
        toggleInput = toggleInput || resolveToggleInput(toggleBlock);
        log("block click; re-resolved input:", toggleInput);
        updateDiag();
      });
    }
    const BOT_SELECTORS = [
      '[data-testid="bot"]','[data-testid="bot"] *','[data-testid="block-markdown"]',
      '.message.bot','[role="log"]','[aria-live="polite"]','[aria-live="assertive"]'
    ];
    function getLatestBotText() {
      const { root, host } = getChatbotRoots();
      for (const sel of BOT_SELECTORS) {
        const nodes = $$(sel, root);
        if (nodes.length) {
          const t = (nodes[nodes.length-1].innerText || nodes[nodes.length-1].textContent || "").trim();
          if (t) { log("root sel:", sel, "→", t.slice(0,120)); return t; }
        }
      }
      for (const sel of BOT_SELECTORS) {
        const nodes = $$(sel, host);
        if (nodes.length) {
          const t = (nodes[nodes.length-1].innerText || nodes[nodes.length-1].textContent || "").trim();
          if (t) { log("host sel:", sel, "→", t.slice(0,120)); return t; }
        }
      }
      const nodes = $$(BOT_SELECTORS.join(","), gr());
      if (nodes.length) {
        const t = (nodes[nodes.length-1].innerText || nodes[nodes.length-1].textContent || "").trim();
        if (t) { log("app fallback →", t.slice(0,120)); return t; }
      }
      log("no bot text found");
      return "";
    }
    function attachObserver() {
      const { host, root } = getChatbotRoots();
      log("attachObserver", { host, root });
      let debounceTimer = null;
      const handler = () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          try {
            const latest = getLatestBotText();
            if (!latest) return;
            const act = (root.activeElement || document.activeElement);
            const activeVal = (act && ("value" in act)) ? (act.value || "").trim() : "";
            if (activeVal && latest === activeVal) { log("skip (equals active input)"); return; }
            if (latest === lastSpoken) { log("skip (same as last)"); return; }
            lastSpoken = latest;
            unlockIfNeeded();
            speakNow(latest);
          } catch (e) { warn("observer handler error", e); }
        }, 80);
      };
      try { const obs1 = new MutationObserver(handler);
        obs1.observe(root, { childList: true, subtree: true, characterData: true });
        log("observer on root");
      } catch (e) { warn("observe root failed", e); }
      try { if (host !== root) {
        const obs2 = new MutationObserver(handler);
        obs2.observe(host, { childList: true, subtree: true, characterData: true });
        log("observer on host");
      }} catch (e) { warn("observe host failed", e); }
      updateDiag("observer on");
    }
    waitFor(["#chatbox"], () => attachObserver());
    updateDiag();
    log("init complete");
  });
}
"""

# ---------- UI ----------
with gr.Blocks(title="Janaka’s Learning Chatbot", css=CSS) as demo:
    gr.HTML("<style>.gr-button { white-space: normal; line-height: 1.2; }</style>")
    gr.Markdown(
        "## Janaka’s Learning Chatbot\n"
        "Warm, concise screening. If a detail is missing, I’ll tell you and follow up. "
        "You can also share your details in the **Contact** tab."
    )

    # Chat tab
    with gr.Tab("Chat"):
        chatbot = gr.Chatbot(height=420, label="Interview Chat", elem_id="chatbox")
        user_in = gr.Textbox(
            placeholder="Ask about experience, availability, location, etc.",
            label="Your question",
            lines=1,
        )
        send_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear")
        state = gr.State([])

        gr.Markdown("#### Quick questions (tap to ask)")
        with gr.Row():
            quick_buttons = [gr.Button(label) for label in SUGGESTED_QUESTIONS]
        with gr.Row():
            speak_toggle = gr.Checkbox(value=True, label="🔊 Speak answers", elem_id="speak_toggle")

        for btn, label in zip(quick_buttons, SUGGESTED_QUESTIONS):
            btn.click(lambda s, q=label: ask_quick(s, q), [state], [state, user_in]) \
                .then(lambda s: s, inputs=state, outputs=chatbot) \
                .then(lambda: "", None, user_in)

        def _send(state_, msg):
            return answer_query(state_, msg)

        send_btn.click(_send, [state, user_in], [state, user_in]) \
            .then(lambda s: s, inputs=state, outputs=chatbot) \
            .then(lambda: "", None, user_in)

        user_in.submit(_send, [state, user_in], [state, user_in]) \
            .then(lambda s: s, inputs=state, outputs=chatbot) \
            .then(lambda: "", None, user_in)

        clear_btn.click(lambda: ([], ""), None, [state, user_in]) \
            .then(lambda: [], None, chatbot)

    # Contact tab
    with gr.Tab("Contact"):
        gr.Markdown("### Share your details — I’ll follow up")
        name = gr.Textbox(label="Your name", placeholder="e.g., Alex Johnson")
        email = gr.Textbox(label="Email", placeholder="e.g., alex@company.com")
        phone = gr.Textbox(label="Phone", placeholder="+41 79 ... (optional but helpful)")
        company = gr.Textbox(label="Company", placeholder="e.g., ACME Bank")
        message = gr.Textbox(label="Message", placeholder="Short note or question", lines=3)
        submit_btn = gr.Button("Send")
        contact_out = gr.Markdown()

        def _submit(name_, email_, phone_, company_, message_):
            if not (email_.strip() or phone_.strip()):
                return "Please provide at least an email or a phone number."
            return append_lead(
                name_.strip(), email_.strip(), phone_.strip(), company_.strip(), message_.strip()
            )

        submit_btn.click(_submit, [name, email, phone, company, message], [contact_out])
        gr.Markdown("> Or reach me directly: **janaka2@gmail.com** · **+41 76 224 84 45**")

    # Manage Knowledge tab
    with gr.Tab("Manage Knowledge"):
        admin_token = gr.State("")
        login_group = gr.Group(visible=True)
        with login_group:
            gr.Markdown("### Admin login")
            admin_pw_input = gr.Textbox(type="password", label="Password")
            login_btn = gr.Button("Login", variant="primary")
            login_status = gr.Markdown()

        admin_group = gr.Group(visible=False)
        with admin_group:
            gr.Markdown("### Add / Update Q&A")
            q_box = gr.Textbox(label="Question")
            a_box = gr.Textbox(label="Answer", lines=3)
            add_btn = gr.Button("Save Q&A", variant="primary")
            add_out = gr.Markdown()

            gr.Markdown("### Current Q&A")
            list_btn = gr.Button("Refresh Q&A List")
            list_out = gr.Markdown()

            gr.Markdown("### Reindex (reload facts/docs/Q&A)")
            reindex_btn = gr.Button("Reindex Now")
            reindex_out = gr.Markdown()

        def _login(pw):
            if not pw or pw.strip() != os.getenv("ADMIN_PASSWORD", "change-me").strip():
                return "", gr.update(visible=True), gr.update(visible=True), gr.update(visible=False), "Invalid password."
            token = secrets.token_urlsafe(24)
            import time as _t
            if "ADMIN_SESSIONS" in globals():
                ADMIN_SESSIONS[token] = _t.time() + 60 * 60 * 4
            return token, gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), "Logged in. Welcome!"

        login_btn.click(
            _login,
            [admin_pw_input],
            [admin_token, admin_pw_input, login_btn, admin_group, login_status],
        )

        import time as _t

        def add_qa_session(token: str, q: str, a: str) -> str:
            if token not in ADMIN_SESSIONS or ADMIN_SESSIONS[token] < _t.time():
                return "Not authorized."
            ADMIN_SESSIONS[token] = _t.time() + 60 * 60 * 4
            q = (q or "").strip()
            a = (a or "").strip()
            if not q or not a:
                return "Please provide both Question and Answer."
            data = load_json(QA_PATH, [])
            replaced = False
            for item in data:
                if item.get("q", "").strip().lower() == q.lower():
                    item["a"] = a
                    replaced = True
                    break
            if not replaced:
                data.append({"q": q, "a": a})
            ok, msg = save_json(QA_PATH, data)
            if ok:
                retriever.build_corpus()
                return "Saved Q&A and reindexed."
            return msg

        def list_qa_session(token: str) -> str:
            if token not in ADMIN_SESSIONS or ADMIN_SESSIONS[token] < _t.time():
                return "Not authorized."
            ADMIN_SESSIONS[token] = _t.time() + 60 * 60 * 4
            data = load_json(QA_PATH, [])
            if not data:
                return "No Q&A entries yet."
            lines = []
            for i, item in enumerate(data, start=1):
                lines.append(f"{i}. Q: {item.get('q','')}\n   A: {item.get('a','')}")
            return "\n\n".join(lines)

        def reindex_session(token: str) -> str:
            if token not in ADMIN_SESSIONS or ADMIN_SESSIONS[token] < _t.time():
                return "Not authorized."
            ADMIN_SESSIONS[token] = _t.time() + 60 * 60 * 4
            retriever.build_corpus()
            return "Reindexed knowledge successfully."

        add_btn.click(lambda tok, q, a: add_qa_session(tok, q, a), [admin_token, q_box, a_box], [add_out])
        list_btn.click(lambda tok: list_qa_session(tok), [admin_token], [list_out])
        reindex_btn.click(lambda tok: reindex_session(tok), [admin_token], [reindex_out])

    # Health tab
    with gr.Tab("Health"):
        health_btn = gr.Button("Check")
        health_out = gr.Code(label="Status JSON")
        health_btn.click(lambda: health(), None, [health_out])

    # Register client JS once
    demo.load(None, None, None, js=SPEECH_INIT_JS)

# ---------- Launch ----------
if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)