/* CSRF token injection -- reads meta tag and sets hx-headers on body */
(function() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
        document.body.setAttribute(
            "hx-headers",
            JSON.stringify({"X-CSRF-Token": meta.getAttribute("content")})
        );
        if (window.htmx) {
            htmx.process(document.body);
        }
    }
})();

/* Toast auto-dismiss and modal close handling */

document.addEventListener("htmx:oobAfterSwap", function () {
    var toasts = document.querySelectorAll("#toast-container .toast");
    toasts.forEach(function (toast) {
        if (toast.getAttribute("data-dismiss-scheduled")) {
            return;
        }
        toast.setAttribute("data-dismiss-scheduled", "true");
        setTimeout(function () {
            toast.classList.add("toast--dismiss");
            setTimeout(function () {
                toast.remove();
            }, 300);
        }, 3000);
    });
});

/* Filter bar: toggle active button on click */
document.addEventListener("click", function (e) {
    var btn = e.target.closest(".filter-bar button");
    if (!btn) return;
    btn.closest(".filter-bar").querySelectorAll("button").forEach(function (b) {
        b.className = "secondary outline";
    });
    btn.className = "primary";
});

document.addEventListener("closeModal", function () {
    var dialogs = document.querySelectorAll("dialog[open]");
    dialogs.forEach(function (dialog) {
        dialog.close();
        dialog.remove();
    });
});
