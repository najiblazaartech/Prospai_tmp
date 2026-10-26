// ProspAI extension - service worker
// Recupere les actions dues via l'API, ouvre le profil, demande au content
// script d'executer l'action DOM, confirme l'envoi a l'API. Jitter humain partout.

const API_URL = "http://localhost:8000"; // a adapter en prod
const TOKEN_KEY = "prospai_token";
const MIN_DELAY_MS = 15000;   // 15 s minimum entre deux actions
const MAX_DELAY_MS = 60000;    // 60 s maximum

async function api(path, opts = {}) {
  const token = (await chrome.storage.local.get(TOKEN_KEY))[TOKEN_KEY];
  if (!token) throw new Error("non connecte");
  const res = await fetch(API_URL + path, {
    ...opts,
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
  });
  if (!res.ok) throw new Error("API " + res.status);
  return res.json();
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function executeAction(tab, action) {
  const url = action.linkedin_url || "https://www.linkedin.com/feed/";
  const target = tab && tab.url && tab.url.includes("linkedin.com") ? tab : null;

  let tabId;
  if (target) {
    await chrome.tabs.update(target.id, { url, active: true });
    tabId = target.id;
  } else {
    const t = await chrome.tabs.create({ url, active: true });
    tabId = t.id;
  }
  await new Promise((resolve) => {
    const listener = (tid, info) => {
      if (tid === tabId && info.status === "complete") {
        chrome.tabs.onUpdated.removeListener(listener);
        resolve();
      }
    };
    chrome.tabs.onUpdated.addListener(listener);
    setTimeout(resolve, 8000);
  });
  await sleep(3000 + Math.random() * 4000); // pause "lecture du profil"

  const results = await chrome.tabs.sendMessage(tabId, { type: "EXECUTE_ACTION", action });
  return results;
}

async function runTick() {
  let actions = [];
  try {
    actions = await api("/campaigns/actions/due");
  } catch (e) {
    return; // non connecte ou erreur API
  }
  let lastTab = null;
  for (const a of actions) {
    try {
      const result = await executeAction(lastTab, a);
      if (result && result.ok) {
        await api("/campaigns/actions/" + a.id + "/sent", { method: "POST" });
      } else {
        console.log("[ProspAI] action echouee:", result && result.error);
      }
      lastTab = null;
    } catch (e) {
      console.log("[ProspAI] erreur action:", e.message);
    }
    // Jitter humain entre chaque action
    await sleep(MIN_DELAY_MS + Math.random() * (MAX_DELAY_MS - MIN_DELAY_MS));
  }
}

chrome.alarms.create("prospai-tick", { periodInMinutes: 10 });

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name !== "prospai-tick") return;
  try { await runTick(); } catch (e) { console.log("[ProspAI]", e.message); }
});

chrome.runtime.onMessage.addListener(async (msg) => {
  if (msg.type === "RUN_NOW") {
    try { await runTick(); } catch (e) { console.log("[ProspAI]", e.message); }
  }
  if (msg.type === "REPLY_DETECTED" && msg.actionId) {
    try {
      await api("/campaigns/actions/" + msg.actionId + "/replied", { method: "POST" });
    } catch (e) { /* ignore */ }
  }
});
