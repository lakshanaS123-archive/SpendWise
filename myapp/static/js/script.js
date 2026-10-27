
document.addEventListener("DOMContentLoaded", function () {

    // Demo button: retain the original frontend test.
    const demoButton = document.getElementById("demoButton");
    const demoMessage = document.getElementById("demoMessage");

    if (demoButton && demoMessage) {
        demoButton.addEventListener("click", function () {
            demoMessage.textContent =
                "Success! Your SpendWise frontend is responding to JavaScript.";
        });
    }

    // Budget progress bars.
    document.querySelectorAll("[data-progress]").forEach(function (bar) {
        const progress = Number(bar.dataset.progress);

        if (Number.isFinite(progress)) {
            const safeProgress = Math.min(
                100,
                Math.max(0, progress)
            );

            bar.style.width = safeProgress + "%";
        }
    });

});

/* =========================================
   SPENDWISE BATCH 3: AUDIO + INTERFACE SOUNDS
   ========================================= */

document.addEventListener("DOMContentLoaded", function () {
    // ---------- AUDIO LESSONS ----------
    const audioStatus = document.getElementById("audioStatus");
    const stopAudioButton = document.getElementById("stopAudio");
    const audioButtons = document.querySelectorAll(".sw-audio-play");

    function setAudioStatus(message) {
        if (audioStatus) {
            audioStatus.textContent = message;
        }
    }

    function stopLessonAudio() {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }
        setAudioStatus("Audio stopped. Choose a lesson to listen.");
    }

    audioButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const text = button.dataset.audioText || "";

            if (!("speechSynthesis" in window) ||
                !("SpeechSynthesisUtterance" in window)) {
                setAudioStatus(
                    "Audio playback is not supported by this browser. " +
                    "Try opening SpendWise in an updated browser."
                );
                return;
            }

            if (!text.trim()) {
                setAudioStatus("This lesson has no audio text available.");
                return;
            }

            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "en-IN";
            utterance.rate = 0.95;
            utterance.pitch = 1;

            utterance.onstart = function () {
                setAudioStatus("Playing: " + text.split(".")[0]);
            };

            utterance.onend = function () {
                setAudioStatus("Lesson finished. Choose another lesson.");
            };

            utterance.onerror = function (event) {
                if (event.error !== "canceled" &&
                    event.error !== "interrupted") {
                    setAudioStatus(
                        "Could not play audio. Check your browser's " +
                        "speech settings and try again."
                    );
                }
            };

            window.speechSynthesis.speak(utterance);
        });
    });

    if (stopAudioButton) {
        stopAudioButton.addEventListener("click", stopLessonAudio);
    }

    // ---------- OPTIONAL INTERFACE SOUNDS ----------
    // Sounds start OFF. The user must explicitly enable them.
    let soundsEnabled = false;

    const soundToggle = document.createElement("button");
    soundToggle.type = "button";
    soundToggle.className = "sw-sound-toggle";
    soundToggle.textContent = "♪ Sounds: Off";
    soundToggle.setAttribute("aria-pressed", "false");
    soundToggle.setAttribute(
        "aria-label",
        "Enable or disable interface sounds"
    );

    document.body.appendChild(soundToggle);

    let audioContext = null;

    function playInterfaceSound() {
        if (!soundsEnabled) return;

        const AudioContextClass =
            window.AudioContext || window.webkitAudioContext;

        if (!AudioContextClass) return;

        try {
            if (!audioContext) {
                audioContext = new AudioContextClass();
            }

            if (audioContext.state === "suspended") {
                audioContext.resume();
            }

            const oscillator = audioContext.createOscillator();
            const gain = audioContext.createGain();

            oscillator.type = "sine";
            oscillator.frequency.setValueAtTime(
                660,
                audioContext.currentTime
            );

            gain.gain.setValueAtTime(
                0.0001,
                audioContext.currentTime
            );

            gain.gain.exponentialRampToValueAtTime(
                0.045,
                audioContext.currentTime + 0.015
            );

            gain.gain.exponentialRampToValueAtTime(
                0.0001,
                audioContext.currentTime + 0.10
            );

            oscillator.connect(gain);
            gain.connect(audioContext.destination);

            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.11);
        } catch (error) {
            // Audio is optional; never interrupt the application.
        }
    }

    soundToggle.addEventListener("click", function () {
        soundsEnabled = !soundsEnabled;

        soundToggle.textContent = soundsEnabled
            ? "♪ Sounds: On"
            : "♪ Sounds: Off";

        soundToggle.setAttribute(
            "aria-pressed",
            String(soundsEnabled)
        );

        if (soundsEnabled) {
            playInterfaceSound();
        }
    });

    // Short sounds on ordinary buttons, only when enabled.
    document.addEventListener("click", function (event) {
        const target = event.target.closest(
            "button, .primary-button, .sw-button"
        );

        if (target && target !== soundToggle) {
            playInterfaceSound();
        }
    });
});

/* =========================================
   SPENDWISE BATCH 4: RECEIPT IMAGE PREVIEW
   ========================================= */

document.addEventListener("DOMContentLoaded", function () {
    const fileInputs = document.querySelectorAll(
        'input[type="file"]'
    );

    fileInputs.forEach(function (input) {
        const preview = document.createElement("img");

        preview.alt = "Selected receipt image preview";
        preview.hidden = true;
        preview.style.cssText = [
            "display:none",
            "max-width:100%",
            "max-height:300px",
            "object-fit:contain",
            "margin-top:12px",
            "border:1px solid #d9e0ed",
            "border-radius:10px",
            "padding:5px",
            "background:#fff"
        ].join(";");

        const status = document.createElement("p");
        status.className = "receipt-preview-status";
        status.setAttribute("role", "status");
        status.style.cssText =
            "margin-top:8px;font-size:13px;color:#69758a";

        input.insertAdjacentElement("afterend", preview);
        preview.insertAdjacentElement("afterend", status);

        let currentObjectURL = null;

        input.addEventListener("change", function () {
            if (currentObjectURL) {
                URL.revokeObjectURL(currentObjectURL);
                currentObjectURL = null;
            }

            preview.removeAttribute("src");
            preview.hidden = true;
            preview.style.display = "none";
            status.textContent = "";

            const file = input.files && input.files[0];

            if (!file) return;

            if (!file.type.startsWith("image/")) {
                status.textContent =
                    "File selected. Image preview is available for image files.";
                return;
            }

            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp",
                "image/gif"
            ];

            if (!allowedTypes.includes(file.type)) {
                status.textContent =
                    "Preview supports JPEG, PNG, WebP, and GIF images.";
                return;
            }

            // Avoid decoding unusually large images in the browser.
            if (file.size > 10 * 1024 * 1024) {
                status.textContent =
                    "Image selected, but preview is disabled for files over 10 MB.";
                return;
            }

            currentObjectURL = URL.createObjectURL(file);
            preview.src = currentObjectURL;
            preview.hidden = false;
            preview.style.display = "block";
            status.textContent =
                file.name + " · " +
                (file.size / 1024).toFixed(1) + " KB";

            preview.onerror = function () {
                preview.hidden = true;
                preview.style.display = "none";
                status.textContent =
                    "This image could not be previewed.";
            };
        });

        // Release the temporary preview URL when the page is left.
        window.addEventListener("pagehide", function () {
            if (currentObjectURL) {
                URL.revokeObjectURL(currentObjectURL);
                currentObjectURL = null;
            }
        });
    });
});

/* SpendWise responsive navigation */
document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("navToggle");
    const nav = document.getElementById("navLinks");

    if (!toggle || !nav) return;

    function closeMenu() {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open navigation menu");
    }

    toggle.addEventListener("click", function () {
        const isOpen = nav.classList.toggle("is-open");

        toggle.setAttribute("aria-expanded", String(isOpen));
        toggle.setAttribute(
            "aria-label",
            isOpen ? "Close navigation menu" : "Open navigation menu"
        );
    });

    nav.querySelectorAll("a").forEach(function (link) {
        link.addEventListener("click", closeMenu);
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeMenu();
        }
    });

    window.addEventListener("resize", function () {
        if (window.innerWidth > 760) {
            closeMenu();
        }
    });
});
