// ProspAI content script - automatisation DOM LinkedIn
// Execute : invitation avec message personnalise, message direct.
// Delis aleatoires entre chaque interaction pour un profil humain-like.

const HUMAN_DELAY = () => 800 + Math.random() * 2500;

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function humanType(el, text) {
  el.focus();
  for (const ch of text) {
    el.value += ch;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    await sleep(15 + Math.random() * 60);
  }
}

async function sendInvitationWithNote(content) {
  // Bouton "Se connecter"
  const connectBtn = await waitFor(() => {
    return [...document.querySelectorAll("button span")].find(
      (s) => /Se connecter|Connect/i.test(s.textContent)
    )?.closest("button");
  }, 8000);
  if (!connectBtn) return { ok: false, error: "Bouton Se connecter introuvable (deja connecte ?)" };

  connectBtn.click();
  await sleep(HUMAN_DELAY());

  // Fenetre d'invitation -> "Ajouter une note"
  const addNote = await waitFor(() => {
    return [...document.querySelectorAll("button")].find((b) => /Ajouter une note|Add a note/i.test(b.textContent));
  }, 6000);
  if (addNote) {
    addNote.click();
    await sleep(HUMAN_DELAY());
    const textarea = document.querySelector("textarea");
    if (textarea) await humanType(textarea, content.slice(0, 280)); // limite LinkedIn ~300
  }

  const sendBtn = await waitFor(() => {
    return [...document.querySelectorAll("button")].find((b) => /^(Envoyer|Send)$/i.test(b.textContent.trim()));
  }, 6000);
  if (!sendBtn) return { ok: false, error: "Bouton Envoyer introuvable" };
  sendBtn.click();
  await sleep(HUMAN_DELAY());
  return { ok: true };
}

async function sendMessage(content) {
  // Bouton "Message"
  const msgBtn = await waitFor(() => {
    return [...document.querySelectorAll("button span")].find(
      (s) => /^Message$/i.test(s.textContent.trim())
    )?.closest("button");
  }, 8000);
  if (!msgBtn) return { ok: false, error: "Bouton Message introuvable" };

  msgBtn.click();
  await sleep(HUMAN_DELAY());

  const editor = await waitFor(() => {
    return document.querySelector("div[contenteditable='true']");
  }, 8000);
  if (!editor) return { ok: false, error: "Zone de message introuvable" };

  editor.focus();
  await humanType(editor, content);
  await sleep(HUMAN_DELAY());

  const sendBtn = await waitFor(() => {
    return [...document.querySelectorAll("button")].find((b) => /^(Envoyer|Send)$/i.test(b.textContent.trim()) && !b.disabled);
  }, 6000);
  if (!sendBtn) return { ok: false, error: "Bouton Envoyer introuvable" };
  sendBtn.click();
  await sleep(HUMAN_DELAY());
  return { ok: true };
}

function waitFor(fn, timeout) {
  const start = Date.now();
  return new Promise((resolve) => {
    const iv = setInterval(() => {
      const result = fn();
      if (result) {
        clearInterval(iv);
        resolve(result);
      } else if (Date.now() - start > timeout) {
        clearInterval(iv);
        resolve(null);
      }
    }, 400);
  });
}

// Detection de reponses : badge de notifications qui augmente
let lastNotifCount = null;
setInterval(() => {
  const badge = document.querySelector(
    ".notification-badge, [data-num-uncollapsed-children]"
  );
  if (badge && lastNotifCount !== null && parseInt(badge.textContent) > lastNotifCount) {
    chrome.runtime.sendMessage({ type: "REPLY_DETECTED" });
  }
  if (badge) lastNotifCount = parseInt(badge.textContent) || 0;
}, 10000);

chrome.runtime.onMessage.addListener(async (msg, _sender, respond) => {
  if (msg.type !== "EXECUTE_ACTION") return;
  try {
    const action = msg.action;
    let result;
    if (action.kind === "invitation") {
      result = await sendInvitationWithNote(action.content);
    } else {
      result = await sendMessage(action.content);
    }
    respond(result);
  } catch (e) {
    respond({ ok: false, error: String(e) });
  }
  return true;
});
