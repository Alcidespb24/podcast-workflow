/* Toast auto-dismiss and modal close handling */

document.addEventListener("htmx:oobAfterSwap", function (event) {
    var toasts = event.target.querySelectorAll(".toast");
    toasts.forEach(function (toast) {
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
