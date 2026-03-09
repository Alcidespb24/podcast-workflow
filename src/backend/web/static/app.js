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

document.addEventListener("closeModal", function () {
    var dialogs = document.querySelectorAll("dialog[open]");
    dialogs.forEach(function (dialog) {
        dialog.close();
        dialog.remove();
    });
});
