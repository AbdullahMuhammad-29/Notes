// Timestamps are stored on the server in UTC (see store.py / users.py).
// We intentionally format them here, in the browser, instead of on the
// server - that way every viewer sees the date/time in *their own*
// timezone and locale, not the server's. Any element with a
// data-timestamp="<ISO 8601 string>" attribute gets its text replaced.

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-timestamp]").forEach((el) => {
        const iso = el.getAttribute("data-timestamp");
        if (!iso) return;

        const date = new Date(iso);
        if (isNaN(date.getTime())) return;

        el.textContent = date.toLocaleString(undefined, {
            day: "numeric",
            month: "short",
            year: "numeric",
            hour: "numeric",
            minute: "2-digit",
        });
        el.setAttribute("title", date.toString());
    });
});
