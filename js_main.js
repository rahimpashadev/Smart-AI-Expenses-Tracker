// ===============================
// BACKEND CONFIG
// ===============================
const BACKEND_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
    ? "http://127.0.0.1:8000" 
    : `http://${window.location.hostname}:8000`;

// ===============================
// THEME
// ===============================
function applyTheme() {
    const theme = localStorage.getItem("theme") || "light";
    if (theme === "dark") {
        document.documentElement.classList.add("dark");
    } else {
        document.documentElement.classList.remove("dark");
    }
}

function toggleTheme() {
    const isDark = document.documentElement.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
}

applyTheme();
window.toggleTheme = toggleTheme;

// ===============================
// AUTH + SESSION STORAGE
// ===============================
const CURRENT_USER_KEY = "currentUser";
const IS_LOGGED_IN_KEY = "isLoggedIn";

function normalizeEmail(email) {
    return String(email || "").trim().toLowerCase();
}

function getCurrentUser() {
    try {
        return JSON.parse(localStorage.getItem(CURRENT_USER_KEY)) || null;
    } catch (e) {
        return null;
    }
}

function setCurrentUser(user) {
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
    localStorage.setItem(IS_LOGGED_IN_KEY, "true");
}

function requireAuth() {
    const isLoggedIn = localStorage.getItem(IS_LOGGED_IN_KEY) === "true";
    const currentUser = getCurrentUser();
    if (!isLoggedIn || !currentUser) {
        window.location.href = "login.html";
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem(IS_LOGGED_IN_KEY);
    localStorage.removeItem(CURRENT_USER_KEY);
    window.location.href = "login.html";
}
window.logout = logout;

// ===============================
// API CALLS (SIGNUP, LOGIN, PROFILE)
// ===============================

async function signupUser(event) {
    if (event) event.preventDefault();

    const nameEl = document.getElementById("name");
    const emailEl = document.getElementById("email");
    const passwordEl = document.getElementById("password");

    const name = (nameEl?.value || "").trim();
    const email = normalizeEmail(emailEl?.value || "");
    const password = (passwordEl?.value || "").trim();

    if (!name || !email || !password) {
        alert("Please fill all fields.");
        return false;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Signup successful. Please login.");
            window.location.href = "login.html";
        } else {
            alert(data.detail || "Signup failed.");
        }
    } catch (error) {
        console.error(error);
        alert("Error connecting to backend.");
    }
    return false;
}
window.signupUser = signupUser;

async function loginUser(event) {
    if (event) event.preventDefault();

    const email = normalizeEmail(document.getElementById("email")?.value || "");
    const password = (document.getElementById("password")?.value || "").trim();

    if (!email || !password) {
        alert("Please enter email and password.");
        return false;
    }

    try {
        const response = await fetch(`${BACKEND_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            // Map backend fields to frontend profile object
            const user = data.user;
            const profile = {
                age: user.age || "",
                salary: user.salary || "",
                city: user.city || "",
                living: user.living_type || "Family Home",
                family: user.family_size || "Single",
                transport: user.transport_mode || "Car",
                additionalInfo: user.additional_info || ""
            };
            user.profile = profile;
            
            setCurrentUser(user);

            if (user.onboarding_completed) {
                window.location.href = "dashboard.html";
            } else {
                window.location.href = "onboarding.html";
            }
        } else {
            alert(data.detail || "Invalid email or password.");
        }
    } catch (error) {
        console.error(error);
        alert("Error connecting to backend.");
    }
    return false;
}
window.loginUser = loginUser;

async function saveOnboarding(event) {
    if (event) event.preventDefault();
    const currentUser = getCurrentUser();
    if (!currentUser) {
        window.location.href = "login.html";
        return false;
    }

    const payload = {
        email: currentUser.email,
        salary: (document.getElementById("salary")?.value || "").trim(),
        city: (document.getElementById("city")?.value || "").trim(),
        living_type: (document.getElementById("livingType")?.value || "").trim(),
        family_size: (document.getElementById("familySize")?.value || "").trim(),
        transport_mode: (document.getElementById("transportMode")?.value || "").trim(),
        additional_info: (document.getElementById("additionalInfo")?.value || "").trim(),
        onboarding_completed: true
    };

    try {
        const response = await fetch(`${BACKEND_URL}/update-profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            // Update local state
            currentUser.profile = {
                ...currentUser.profile,
                salary: payload.salary,
                city: payload.city,
                living: payload.living_type,
                family: payload.family_size,
                transport: payload.transport_mode,
                additionalInfo: payload.additional_info
            };
            currentUser.onboarding_completed = true;
            setCurrentUser(currentUser);

            alert("Information saved successfully.");
            window.location.href = "dashboard.html";
        } else {
            const data = await response.json();
            alert(data.detail || "Failed to save information.");
        }
    } catch (error) {
        console.error(error);
        alert("Error connecting to backend.");
    }
    return false;
}
window.saveOnboarding = saveOnboarding;

function loadSettingsForm() {
    if (!requireAuth()) return;
    const currentUser = getCurrentUser();
    const profile = currentUser.profile || {};

    if (document.getElementById("name")) document.getElementById("name").value = currentUser.name || "";
    if (document.getElementById("age")) document.getElementById("age").value = profile.age || "";
    if (document.getElementById("salary")) document.getElementById("salary").value = profile.salary || "";
    if (document.getElementById("city")) document.getElementById("city").value = profile.city || "";
    if (document.getElementById("living")) document.getElementById("living").value = profile.living || "Family Home";
    if (document.getElementById("family")) document.getElementById("family").value = profile.family || "Single";
    if (document.getElementById("transport")) document.getElementById("transport").value = profile.transport || "Car";
    if (document.getElementById("additionalInfo")) document.getElementById("additionalInfo").value = profile.additionalInfo || "";
}
window.loadSettingsForm = loadSettingsForm;

async function saveSettings() {
    if (!requireAuth()) return;
    const currentUser = getCurrentUser();

    const name = (document.getElementById("name")?.value || "").trim();
    const age = (document.getElementById("age")?.value || "").trim();
    const salary = (document.getElementById("salary")?.value || "").trim();
    const city = (document.getElementById("city")?.value || "").trim();
    const living = (document.getElementById("living")?.value || "Family Home").trim();
    const family = (document.getElementById("family")?.value || "Single").trim();
    const transport = (document.getElementById("transport")?.value || "Car").trim();

    const payload = {
        email: currentUser.email,
        name: name,
        age: age,
        salary: salary,
        city: city,
        living_type: living,
        family_size: family,
        transport_mode: transport,
        additional_info: (document.getElementById("additionalInfo")?.value || "").trim()
    };

    try {
        const response = await fetch(`${BACKEND_URL}/update-profile`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            currentUser.name = name;
            currentUser.profile = {
                age, salary, city, living, family, transport, 
                additionalInfo: payload.additional_info
            };
            setCurrentUser(currentUser);
            alert("Profile updated successfully.");
        } else {
            const data = await response.json();
            alert(data.detail || "Failed to update profile.");
        }
    } catch (error) {
        console.error(error);
        alert("Error connecting to backend.");
    }
}
window.saveSettings = saveSettings;

function getDashboardProfile() {
    const currentUser = getCurrentUser();
    const profile = currentUser?.profile || {};
    return {
        name: currentUser?.name || "User",
        email: currentUser?.email || "",
        city: profile.city || "Your City",
        salary: parseInt(profile.salary, 10) || 100000,
        transport: profile.transport || "Car",
        living: profile.living || "Family Home",
        additionalInfo: profile.additionalInfo || ""
    };
}
window.getDashboardProfile = getDashboardProfile;

// ===============================
// LOCATION TRACKING
// ===============================
let locationWatchId = null;
let lastPosition = null;
let arrivalTime = null;
const DWELL_TIME_LIMIT = 1 * 60 * 1000; // Set to 1 minute as per user request
const DISTANCE_THRESHOLD = 0.05; // 50 meters

function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

async function reverseGeocode(lat, lon) {
    try {
        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}&zoom=18&addressdetails=1`);
        const data = await res.json();
        const addr = data.address;
        // High accuracy priority for place names
        return addr.amenity || addr.shop || addr.restaurant || addr.cafe || addr.fast_food || addr.mall || addr.leisure || addr.tourism || addr.building || data.display_name.split(',')[0];
    } catch (e) {
        return "this location";
    }
}

window.toggleLocationTracking = function() {
    const isTracking = localStorage.getItem("isLocationTracking") === "true";
    const newState = !isTracking;
    localStorage.setItem("isLocationTracking", newState);
    
    if (newState) {
        if ("Notification" in window && Notification.permission !== "granted") {
            Notification.requestPermission();
        }
        startLocationTracking();
        alert("Location tracking ACTIVE. Keep this tab open. We will ping you if you stay at a shop/cafe for 1 minute.");
    } else {
        stopLocationTracking();
        alert("Location tracking STOPPED.");
    }
    return newState;
};

let dwellInterval = null;

function startLocationTracking() {
    if (!navigator.geolocation) return;
    
    // 1. Start Watcher for movement
    locationWatchId = navigator.geolocation.watchPosition((position) => {
        const { latitude, longitude } = position.coords;
        const now = Date.now();
        if (!lastPosition || getDistance(lastPosition.latitude, lastPosition.longitude, latitude, longitude) > DISTANCE_THRESHOLD) {
            lastPosition = { latitude, longitude };
            arrivalTime = now;
            console.log("📍 Moved to new location:", latitude, longitude);
        }
    }, (err) => console.warn("GPS Error:", err), { enableHighAccuracy: true });

    // 2. Start Proactive Polling for dwelling (Every 30 seconds)
    if (dwellInterval) clearInterval(dwellInterval);
    dwellInterval = setInterval(async () => {
        if (!lastPosition || !arrivalTime) return;
        
        const now = Date.now();
        const dwellTime = now - arrivalTime;
        
        if (dwellTime >= DWELL_TIME_LIMIT) {
            const locationName = await reverseGeocode(lastPosition.latitude, lastPosition.longitude);
            console.log("⏰ Dwell limit reached at:", locationName);
            
            // Trigger UI Modal
            if (window.showPurchaseModal) window.showPurchaseModal(locationName);
            
            // Trigger System Notification
            if ("Notification" in window && Notification.permission === "granted") {
                new Notification("💰 Smart AI Expenses Tracker: New Purchase?", {
                    body: `You've been at ${locationName} for 1 minute. Add your purchase?`,
                    icon: "https://cdn-icons-png.flaticon.com/512/2845/2845811.png"
                });
            }
            
            // Reset arrival time to prevent spamming (re-triggers in 1 min if still there)
            arrivalTime = now; 
        }
    }, 30000); 
}

function stopLocationTracking() {
    if (locationWatchId) navigator.geolocation.clearWatch(locationWatchId);
    if (dwellInterval) clearInterval(dwellInterval);
    locationWatchId = null;
    dwellInterval = null;
}

// Auto-start if it was enabled
if (localStorage.getItem("isLocationTracking") === "true") {
    startLocationTracking();
}

async function addManualExpense(category, amount, description) {
    const currentUser = getCurrentUser();
    if (!currentUser) return { success: false };

    try {
        const response = await fetch(`${BACKEND_URL}/add-expense`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_email: currentUser.email,
                category,
                amount,
                description
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Failed to save expense');
        }

        if (data.over_budget) {
            const reasonsText = Array.isArray(data.recent_same_category) && data.recent_same_category.length
                ? data.recent_same_category.map(item => `- ${item.description} (PKR ${(item.amount || 0).toLocaleString()})`).join('\n')
                : '- No detailed reason available';

            alert(
`⚠️ Budget Alert!

Category: ${data.category}
Assigned Budget: PKR ${(data.budget || 0).toLocaleString()}
Your Total Spending: PKR ${(data.spent || 0).toLocaleString()}
Remaining: PKR ${(data.remaining || 0).toLocaleString()}
Over Budget By: PKR ${(data.over_amount || 0).toLocaleString()}

Reason:
You are spending more than your assigned budget in this category.

Recent uses:
${reasonsText}`
            );
        }

        return { success: true, data };
    } catch (e) {
        console.error(e);
        alert("Error saving expense.");
        return { success: false };
    }
}
window.addManualExpense = addManualExpense;

// ===============================
// ASK AI FUNCTION
// ===============================
window.askAI = async function () {
    const question = document.getElementById("ai-question")?.value || "";

    if (!question.trim()) {
        alert("Please write a question first");
        return;
    }

    const responseBox = document.getElementById("ai-response");
    if (responseBox) {
        responseBox.innerText = "Thinking...";
        responseBox.classList.remove("hidden");
    }

    try {
        const response = await fetch(`${BACKEND_URL}/ask-ai`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();
        if (responseBox) responseBox.innerText = data.answer || "No response from AI";

    } catch (error) {
        console.error(error);
        if (responseBox) responseBox.innerText = "Error connecting to backend";
    }
};
