const returnFocus = new WeakMap();

export async function syncDialog(owner, id, open) {
  let targets = returnFocus.get(owner);
  if (!targets) { targets = new Map(); returnFocus.set(owner, targets); }
  if (open) targets.set(id, document.activeElement);
  await owner.$nextTick();
  if (open) {
    const dialog = document.getElementById(id);
    if (dialog && !dialog.open) dialog.showModal();
  } else {
    const origin = targets.get(id);
    targets.delete(id);
    (origin?.isConnected ? origin : document.getElementById('main-workspace'))?.focus();
  }
}

export function containDialogTab(event) {
  const dialog = event.currentTarget;
  const controls = [...dialog.querySelectorAll('button, input, select, textarea, a[href], [tabindex]')]
    .filter(node => !node.disabled && node.tabIndex >= 0 && node.getClientRects().length);
  if (!controls.length) { event.preventDefault(); dialog.focus(); return; }
  const first = controls[0], last = controls.at(-1);
  if (event.shiftKey && (document.activeElement === first || !controls.includes(document.activeElement))) {
    event.preventDefault(); last.focus();
  } else if (!event.shiftKey && (document.activeElement === last || !controls.includes(document.activeElement))) {
    event.preventDefault(); first.focus();
  }
}
