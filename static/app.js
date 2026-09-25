"use strict";
const fileInput = document.getElementById("file");
const frame = document.getElementById("frame");
const preview = document.getElementById("preview");
const statusEl = document.getElementById("status");
const out = document.getElementById("out");
const vinEl = document.getElementById("vin");
const tagEl = document.getElementById("tag");
const copyBtn = document.getElementById("copy");
const LABEL = {
    car: "Found on vehicle",
    mulkiya: "Found on mulkiya",
    unknown: "VIN found",
};
function fail(msg) {
    statusEl.textContent = msg;
    statusEl.hidden = false;
}
fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    if (!file)
        return;
    statusEl.hidden = true;
    out.hidden = true;
    preview.src = URL.createObjectURL(file);
    frame.hidden = false;
    frame.classList.add("loading");
    const body = new FormData();
    body.append("file", file);
    try {
        const res = await fetch("/api/vin", { method: "POST", body });
        if (!res.ok)
            throw new Error((await res.json()).detail ?? `HTTP ${res.status}`);
        const data = (await res.json());
        if (data.vin) {
            vinEl.textContent = data.vin;
            tagEl.textContent = LABEL[data.found_on] ?? LABEL.unknown;
            out.hidden = false;
        }
        else {
            fail("No VIN found in this photo. Try the plate or the mulkiya again.");
        }
    }
    catch (err) {
        fail(err instanceof Error ? err.message : "Something went wrong.");
    }
    finally {
        frame.classList.remove("loading");
        fileInput.value = "";
    }
});
copyBtn.addEventListener("click", async () => {
    await navigator.clipboard.writeText(vinEl.textContent ?? "");
    copyBtn.textContent = "Copied";
    setTimeout(() => (copyBtn.textContent = "Copy VIN"), 1500);
});
