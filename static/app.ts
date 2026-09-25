const fileInput = document.getElementById("file") as HTMLInputElement;
const frame = document.getElementById("frame") as HTMLElement;
const preview = document.getElementById("preview") as HTMLImageElement;
const statusEl = document.getElementById("status") as HTMLParagraphElement;
const out = document.getElementById("out") as HTMLElement;
const vinEl = document.getElementById("vin") as HTMLElement;
const tagEl = document.getElementById("tag") as HTMLElement;
const copyBtn = document.getElementById("copy") as HTMLButtonElement;

interface VinResponse {
  vin: string | null;
  found_on: string;
  valid: boolean;
}

const LABEL: Record<string, string> = {
  car: "Found on vehicle",
  mulkiya: "Found on mulkiya",
  unknown: "VIN found",
};

function fail(msg: string): void {
  statusEl.textContent = msg;
  statusEl.hidden = false;
}

fileInput.addEventListener("change", async () => {
  const file = fileInput.files?.[0];
  if (!file) return;

  statusEl.hidden = true;
  out.hidden = true;
  preview.src = URL.createObjectURL(file);
  frame.hidden = false;
  frame.classList.add("loading");

  const body = new FormData();
  body.append("file", file);

  try {
    const res = await fetch("/api/vin", { method: "POST", body });
    if (!res.ok) throw new Error((await res.json()).detail ?? `HTTP ${res.status}`);
    const data = (await res.json()) as VinResponse;

    if (data.vin) {
      vinEl.textContent = data.vin;
      tagEl.textContent = LABEL[data.found_on] ?? LABEL.unknown;
      out.hidden = false;
    } else {
      fail("No VIN found in this photo. Try the plate or the mulkiya again.");
    }
  } catch (err) {
    fail(err instanceof Error ? err.message : "Something went wrong.");
  } finally {
    frame.classList.remove("loading");
    fileInput.value = "";
  }
});

copyBtn.addEventListener("click", async () => {
  await navigator.clipboard.writeText(vinEl.textContent ?? "");
  copyBtn.textContent = "Copied";
  setTimeout(() => (copyBtn.textContent = "Copy VIN"), 1500);
});
