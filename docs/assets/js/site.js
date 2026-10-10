/* Shared behaviour for every page except the home page. */
(function () {
    // "Back" buttons return to the previous page (keeping its scroll position)
    // when the visitor came from this site; otherwise they follow their link.
    document.querySelectorAll(".card-back-btn").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            var ref = document.referrer;
            var fromThisSite = ref && new URL(ref).origin === location.origin;
            if (fromThisSite && history.length > 1) {
                e.preventDefault();
                history.back();
            }
        });
    });
})();
