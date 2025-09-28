document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.querySelector(".nav-sidebar");
    if (!sidebar) return;

    // Find the "Support" menu item
    const supportItem = Array.from(sidebar.querySelectorAll(".nav-item")).find(item =>
        item.textContent.includes("Support")
    );

    if (supportItem) {
        // Create the clean separator
        const separator = document.createElement("li");
        separator.className = "nav-item text-muted mt-2";
        separator.style.pointerEvents = "none";
        separator.innerHTML = `
            <a class="nav-link disabled" style="font-style: italic; color: #ccc;">
                <p>—— Site Settings ——</p>
            </a>
        `;

        // Insert it after the Support item
        supportItem.after(separator);
    }
});

document.addEventListener("DOMContentLoaded", function () {
    fetch("/api/unverified-users/")
        .then(res => res.json())
        .then(data => {
            const count = data.unverified_users;
            if (count <= 0) return;

            // ✅ 1. Badge on "Accounts" submenu item
            const accountLink = document.querySelector(
                '.nav-treeview a[href="/admin/profiling/account/"]'
            );
            if (accountLink && !accountLink.querySelector('.badge')) {
                const badge = document.createElement("span");
                badge.className = "right badge badge-danger ml-2";
                badge.textContent = count;
                accountLink.appendChild(badge);
            }

            // ✅ 2. Badge on "Profiling" main group
            const profilingLink = Array.from(document.querySelectorAll('.nav-sidebar > .nav-item > a'))
                .find(link => link.textContent.includes("Profiling"));

            if (profilingLink && !profilingLink.querySelector('.badge')) {
                const badge = document.createElement("span");
                badge.className = "right badge badge-danger ml-2";
                badge.textContent = count;
                profilingLink.appendChild(badge);
            }
        });
});


document.addEventListener("DOMContentLoaded", function () {

    // Create Bell Icon Container
    const bellWrapper = document.createElement("li");
    bellWrapper.classList.add("nav-item", "dropdown");

    bellWrapper.innerHTML = `
        <a class="nav-link" href="#" id="notificationBell" role="button">
            <i class="fas fa-bell fa-md"></i>
            <span id="notificationCount" class="badge badge-danger navbar-badge" style="display:none; font-size: 10px; padding: 2px 5px; top: -2px; right: -4px;">0</span>
        </a>
        <div class="dropdown-menu dropdown-menu-lg dropdown-menu-right" id="notificationDropdown" style="width: 400px;">
            <span class="dropdown-header">Notifications</span>
            <div class="dropdown-divider"></div>
            <div id="notificationList" style="
                max-height: 400px;
                overflow-y: auto;
                white-space: normal;
                word-break: break-word;
            "></div>
            <div class="dropdown-divider"></div>
            <a href="#" class="dropdown-item dropdown-footer" id="markAllRead">Mark all as read</a>
        </div>
    `;


    // Insert before user dropdown
    const navbarRight = document.querySelector(".navbar-nav.ml-auto");
    if (navbarRight) {
        navbarRight.insertBefore(bellWrapper, navbarRight.firstChild);
    } else {
    }

    // Fetch notifications
    function fetchNotifications() {

        fetch("/api/admin-notifications/")
            .then((res) => res.json())
            .then((data) => {

                const list = document.getElementById("notificationList");
                const count = document.getElementById("notificationCount");
                list.innerHTML = "";

                if (!Array.isArray(data)) return;

                if (data.length === 0) {
                    list.innerHTML = '<span class="dropdown-item text-muted">No notifications</span>';
                    count.style.display = "none";
                } else {
                    let unreadCount = 0;

                    data.forEach((notif) => {
                        const item = document.createElement("div");
                        item.classList.add("dropdown-item");
                        item.style.cursor = "pointer";
                        item.style.whiteSpace = "normal";
                        item.style.wordBreak = "break-word";
                        if (notif.is_read) {
                            item.classList.add("text-muted");
                        } else {
                            unreadCount += 1;
                        }

                        item.innerHTML = `
                            <i class="fas fa-info-circle mr-2"></i> ${notif.message}
                            <br><small class="text-muted">${notif.created_at}</small>
                        `;

                        item.addEventListener("click", function () {
                            fetch(`/api/admin-notifications/read/${notif.id}/`, {
                                method: "POST",
                                headers: { "X-CSRFToken": getCSRFToken() }
                            }).then(() => {
                                fetchNotifications();
                            });
                        });

                        list.appendChild(item);
                    });

                    count.innerText = unreadCount;
                    count.style.display = unreadCount === 0 ? "none" : "inline-block";
                }
            })
            .catch((error) => {
                console.error("[Notif] Error fetching notifications:", error);
            });
    }

    // Event: Toggle dropdown and fetch
    document.getElementById("notificationBell").addEventListener("click", function (e) {
        e.preventDefault();
        document.getElementById("notificationDropdown").classList.toggle("show");
        fetchNotifications();
    });

    // Event: Mark all as read
    document.getElementById("markAllRead").addEventListener("click", function (e) {
        e.preventDefault();
    
        fetch("/api/admin-notifications/read/", {
            method: "POST",
            headers: {
                "X-CSRFToken": getCSRFToken(),
                "Content-Type": "application/json"
            }
        })
        .then((res) => {
            if (!res.ok) {
                throw new Error("Failed to mark all as read");
            }
            return res.json();
        })
        .then(() => {
            fetchNotifications();  // Refresh the list and count
        })
        .catch((err) => {
            console.error("[Notif] Error:", err);
        });
    });
    
    // Get CSRF token helper
    function getCSRFToken() {
        const name = "csrftoken";
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const c = cookies[i].trim();
            if (c.startsWith(name + "=")) {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        return "";
    }
});
