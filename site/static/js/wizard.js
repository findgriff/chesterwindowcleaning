// site/static/js/wizard.js
let state = freshState();

function freshState() {
  return {
    step: "property",
    property_type: null,
    rear_access: null,
    postcode: null,
    addons: [],
    velux_count: 0,
    frequency: "regular_6w",
    quote: null,
    poa: false,
  };
}

export function resetWizardState() { state = freshState(); }

const PROPERTY_OPTIONS = [
  ["3bed_semi", "3-bed semi"], ["4bed_semi", "4-bed semi"],
  ["3bed_det", "3-bed detached"], ["4bed_det", "4-bed detached"],
  ["5bed_det", "5-bed detached"], ["townhouse", "Town house / something different"],
];

export function renderWizard(root) {
  root.innerHTML = "";
  const view = VIEWS[state.step] || VIEWS.property;
  view(root);
}

const VIEWS = {
  property(root) {
    root.innerHTML = `<p>What's your home like?</p>` +
      PROPERTY_OPTIONS.map(([k, label]) =>
        `<button type=button data-pt="${k}" style="display:block;width:100%;margin:.25rem 0;text-align:left;">${label}</button>`
      ).join("");
    root.querySelectorAll("button").forEach(b =>
      b.addEventListener("click", () => {
        const pt = b.dataset.pt;
        if (pt === "townhouse") { state.poa = true; state.step = "contact"; }
        else { state.property_type = pt; state.step = "rear_access"; }
        renderWizard(root);
      }));
  },

  rear_access(root) {
    root.innerHTML = `<p>Is there access to the back of the property?</p>
      <button type=button data-r="yes">Yes</button>
      <button type=button data-r="no">No / not sure</button>`;
    root.querySelectorAll("button").forEach(b =>
      b.addEventListener("click", () => {
        if (b.dataset.r === "yes") { state.rear_access = true; state.step = "postcode"; }
        else { state.rear_access = false; state.step = "access_blocked"; }
        renderWizard(root);
      }));
  },

  postcode(root) {
    root.innerHTML = `<label>Your postcode<br>
      <input id="cwc-pc" placeholder="CH3 5AB" autocomplete="postal-code"></label>
      <div class="row"><button type=button id="cwc-pc-next">Next</button></div>
      <p id="cwc-pc-err" style="color:#c00;margin-top:.5rem;display:none;"></p>`;
    root.querySelector("#cwc-pc-next").addEventListener("click", () => {
      const v = root.querySelector("#cwc-pc").value.trim();
      if (!v) { showErr("Need a postcode."); return; }
      state.postcode = v;
      state.step = "addons";
      renderWizard(root);
    });
    function showErr(msg) {
      const e = root.querySelector("#cwc-pc-err");
      e.textContent = msg; e.style.display = "block";
    }
  },

  addons(root) {
    root.innerHTML = `<p>Any add-ons?</p>
      <label><input type=checkbox data-a="conservatory"> Conservatory</label>
      <label><input type=checkbox data-a="extension"> Extension / 2+ side windows + doors</label>
      <label><input type=checkbox data-a="garage_single"> Garage door (single)</label>
      <label><input type=checkbox data-a="garage_double"> Garage door (double)</label>
      <label>Velux windows count:
        <input type=number min=0 step=1 value=0 id="cwc-velux"></label>
      <div class="row"><button type=button id="cwc-next">Next</button></div>`;
    root.querySelector("#cwc-next").addEventListener("click", () => {
      state.addons = [];
      root.querySelectorAll("input[type=checkbox]").forEach(cb => {
        if (cb.checked) state.addons.push(cb.dataset.a);
      });
      const v = parseInt(root.querySelector("#cwc-velux").value, 10) || 0;
      if (v > 0) state.addons.push({ type: "velux", count: v });
      state.step = "frequency";
      renderWizard(root);
    });
  },

  frequency(root) {
    root.innerHTML = `<p>How often?</p>
      <button type=button data-f="regular_6w">Regular (every 4–6 weeks)</button>
      <button type=button data-f="one_off">One-off / first clean</button>`;
    root.querySelectorAll("button").forEach(b =>
      b.addEventListener("click", async () => {
        state.frequency = b.dataset.f;
        await fetchQuote();
        state.step = "quote";
        renderWizard(root);
      }));
  },

  quote(root) {
    const q = state.quote;
    if (!q) { root.innerHTML = "Couldn't price that. Get in touch?"; return; }
    root.innerHTML = `<p><strong>${q.total_display}</strong> ${state.frequency === "one_off" ? "for a one-off clean." : "every clean."}</p>
      <ul>${q.breakdown.map(b => `<li>${b.label} – ${b.display}</li>`).join("")}</ul>
      <p>Want me to book you in?</p>
      <div class="row"><button type=button id="cwc-book">Yes, take my details</button></div>`;
    root.querySelector("#cwc-book").addEventListener("click", () => {
      state.step = "contact"; renderWizard(root);
    });
  },

  contact(root) {
    root.innerHTML = `
      <p>${state.poa ? "Tell me a bit about your property and I'll get back to you with a quote." : "Almost done."}</p>
      <label>Name<br><input id="cwc-name" required></label>
      <label>Email<br><input id="cwc-email" type=email required></label>
      <label>Phone (optional)<br><input id="cwc-phone" type=tel></label>
      <label>Address<br><input id="cwc-address"></label>
      ${state.poa ? `<label>About your property<br><textarea id="cwc-notes" rows=3></textarea></label>` : ""}
      ${!state.poa ? `<label>Anything else?<br><textarea id="cwc-notes" rows=2></textarea></label>` : ""}
      <div class="row"><button type=button id="cwc-submit">Send</button></div>
      <p id="cwc-err" style="color:#c00;display:none;"></p>`;
    root.querySelector("#cwc-submit").addEventListener("click", async () => {
      const body = {
        source: "wizard",
        name: root.querySelector("#cwc-name").value.trim(),
        email: root.querySelector("#cwc-email").value.trim(),
        phone: root.querySelector("#cwc-phone").value.trim(),
        address: root.querySelector("#cwc-address").value.trim(),
        postcode: state.postcode,
        property_type: state.property_type,
        addons: state.addons,
        frequency: state.frequency,
        quote_pence: state.quote?.total_pence ?? null,
        notes_visitor: root.querySelector("#cwc-notes")?.value || "",
        poa: state.poa,
        access_blocked: false,
      };
      if (!body.name || !body.email) {
        return showErr("Need at least a name and an email.");
      }
      const ok = await postLead(body);
      if (ok) { state.step = "done"; renderWizard(root); }
      else showErr("Sorry — something went wrong. Try emailing hello@chesterwindowcleaner.co.uk.");
    });
    function showErr(m) {
      const e = root.querySelector("#cwc-err");
      e.textContent = m; e.style.display = "block";
    }
  },

  access_blocked(root) {
    root.innerHTML = `<p>I can only take on properties with rear access.</p>
      <p>Want me to note your details in case that changes?</p>
      <label>Name<br><input id="cwc-name"></label>
      <label>Email<br><input id="cwc-email" type=email></label>
      <label>Postcode<br><input id="cwc-pc"></label>
      <div class="row"><button type=button id="cwc-submit">Yes, note me</button>
      <button type=button id="cwc-close">No thanks</button></div>`;
    root.querySelector("#cwc-submit").addEventListener("click", async () => {
      await postLead({
        source: "wizard",
        name: root.querySelector("#cwc-name").value,
        email: root.querySelector("#cwc-email").value,
        postcode: root.querySelector("#cwc-pc").value,
        access_blocked: true,
      });
      state.step = "done"; renderWizard(root);
    });
    root.querySelector("#cwc-close").addEventListener("click", () => window.cwcWidget.close());
  },

  done(root) {
    root.innerHTML = `<p>Thanks. I'll be in touch within 4 working hours.</p>
      <p>You can close this window.</p>
      <div class="row"><button type=button id="cwc-close">Close</button></div>`;
    root.querySelector("#cwc-close").addEventListener("click", () => window.cwcWidget.close());
  },
};

async function fetchQuote() {
  const r = await fetch("/api/quote", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      property_type: state.property_type,
      addons: state.addons,
      frequency: state.frequency,
    }),
  });
  state.quote = r.ok ? await r.json() : null;
}

async function postLead(body) {
  try {
    const r = await fetch("/api/lead", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return r.ok;
  } catch { return false; }
}
