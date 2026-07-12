/* global window, document, CONFIG */

// =========================================
// CAROUSEL
// =========================================
(function initCarousel() {
  const track = document.getElementById("carouselTrack");
  const dotsContainer = document.getElementById("carouselDots");
  if (!track) return;

  const slides = track.querySelectorAll(".carousel__slide");
  const total = slides.length;
  let current = 0;
  let autoTimer;

  // Build dots
  slides.forEach((_, i) => {
    const dot = document.createElement("button");
    dot.className = "carousel__dot" + (i === 0 ? " carousel__dot--active" : "");
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-label", `Photo ${i + 1}`);
    dot.addEventListener("click", () => goTo(i));
    dotsContainer.appendChild(dot);
  });

  function goTo(index) {
    current = (index + total) % total;
    track.style.transform = `translateX(-${current * 100}%)`;
    dotsContainer.querySelectorAll(".carousel__dot").forEach((d, i) => {
      d.classList.toggle("carousel__dot--active", i === current);
    });
  }

  function startAuto() {
    autoTimer = setInterval(() => goTo(current + 1), 4500);
  }

  function stopAuto() {
    clearInterval(autoTimer);
  }

  document.querySelector(".carousel__btn--prev")?.addEventListener("click", () => {
    stopAuto(); goTo(current - 1); startAuto();
  });

  document.querySelector(".carousel__btn--next")?.addEventListener("click", () => {
    stopAuto(); goTo(current + 1); startAuto();
  });

  // Touch / swipe support
  let touchStartX = 0;
  track.addEventListener("touchstart", (e) => { touchStartX = e.touches[0].clientX; }, { passive: true });
  track.addEventListener("touchend", (e) => {
    const delta = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(delta) > 40) {
      stopAuto();
      goTo(delta > 0 ? current + 1 : current - 1);
      startAuto();
    }
  }, { passive: true });

  // Pause on hover
  track.closest(".carousel").addEventListener("mouseenter", stopAuto);
  track.closest(".carousel").addEventListener("mouseleave", startAuto);

  startAuto();
})();


// =========================================
// ACCORDION (FAQ)
// =========================================
(function initAccordion() {
  document.querySelectorAll(".accordion__trigger").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const expanded = trigger.getAttribute("aria-expanded") === "true";
      const bodyId = trigger.getAttribute("aria-controls");
      const body = document.getElementById(bodyId);

      trigger.setAttribute("aria-expanded", String(!expanded));
      if (body) body.hidden = expanded;
    });
  });
})();


// =========================================
// WIZARD
// =========================================
(function initWizard() {
  const TOTAL_SLIDES = 4;
  let currentSlide = 1;

  const btnNext   = document.getElementById("btnNext");
  const btnBack   = document.getElementById("btnBack");
  const btnSubmit = document.getElementById("btnSubmit");

  if (!btnNext) return; // wizard not on page

  function showSlide(n) {
    for (let i = 1; i <= TOTAL_SLIDES; i++) {
      const el = document.getElementById(`slide${i}`);
      if (el) el.hidden = i !== n;
    }
    document.getElementById("slideSuccess").hidden = true;

    // Update step indicators
    document.querySelectorAll(".wizard__step").forEach((step, idx) => {
      const stepNum = idx + 1;
      step.classList.toggle("wizard__step--active", stepNum === n);
      step.classList.toggle("wizard__step--done", stepNum < n);
    });

    // Update progress bar
    const fill = document.getElementById("progressFill");
    if (fill) fill.style.width = `${(n / TOTAL_SLIDES) * 100}%`;

    // Button visibility
    btnBack.hidden   = n === 1;
    btnNext.hidden   = n === TOTAL_SLIDES;
    btnSubmit.hidden = n !== TOTAL_SLIDES;

    currentSlide = n;

    // Populate slide 2 conditional fields when entering it
    if (n === 2) updateSlide2Fields();
  }

  // Slide 2: show/hide fields based on Slide 1 selections
  function updateSlide2Fields() {
    const checked = Array.from(
      document.querySelectorAll('input[name="services"]:checked')
    ).map((cb) => cb.value);

    const hasHousehold  = checked.includes("household") || checked.includes("office");
    const hasPoolTable  = checked.includes("pool-table");
    const hasHeavy      = ["piano", "pool-table", "fitness", "fish-tank", "vending"].some((s) =>
      checked.includes(s)
    );

    const boxGroup    = document.getElementById("detail-boxes");
    const refurbGroup = document.getElementById("detail-refurb");
    const heavyGroup  = document.getElementById("detail-heavy");

    if (boxGroup)    boxGroup.hidden    = !hasHousehold;
    if (refurbGroup) refurbGroup.hidden = !hasPoolTable;
    if (heavyGroup)  heavyGroup.hidden  = !hasHeavy;
  }

  // Stairs toggle inside slide 2
  document.getElementById("stairs-toggle")?.addEventListener("change", function () {
    const stairsDetail = document.getElementById("stairs-detail");
    if (stairsDetail) stairsDetail.hidden = !this.checked;
  });

  // Set min date for move-date picker to today
  const dateInput = document.getElementById("move-date");
  if (dateInput) {
    const today = new Date().toISOString().split("T")[0];
    dateInput.setAttribute("min", today);
  }

  // Validation per slide
  function validateSlide(n) {
    const errorEl = document.getElementById(`slide${n}-error`);

    if (n === 1) {
      const anyChecked = document.querySelectorAll('input[name="services"]:checked').length > 0;
      if (errorEl) errorEl.hidden = anyChecked;
      return anyChecked;
    }

    if (n === 2) {
      // Slide 2 has no strictly required fields — all are conditional
      if (errorEl) errorEl.hidden = true;
      return true;
    }

    if (n === 3) {
      const fields = ["origin-city", "origin-postal", "dest-city", "dest-postal"];
      const allFilled = fields.every((id) => (document.getElementById(id)?.value || "").trim() !== "");
      if (errorEl) errorEl.hidden = allFilled;
      return allFilled;
    }

    if (n === 4) {
      const name  = (document.getElementById("contact-name")?.value  || "").trim();
      const email = (document.getElementById("contact-email")?.value || "").trim();
      const phone = (document.getElementById("contact-phone")?.value || "").trim();
      const ok    = name.length > 0 && email.includes("@") && phone.length >= 7;
      if (errorEl) errorEl.hidden = ok;
      return ok;
    }

    return true;
  }

  btnNext.addEventListener("click", () => {
    if (validateSlide(currentSlide) && currentSlide < TOTAL_SLIDES) {
      showSlide(currentSlide + 1);
    }
  });

  btnBack.addEventListener("click", () => {
    if (currentSlide > 1) showSlide(currentSlide - 1);
  });

  btnSubmit.addEventListener("click", async () => {
    if (!validateSlide(4)) return;

    btnSubmit.disabled   = true;
    btnSubmit.textContent = "Sending…";

    const payload = collectPayload();

    try {
      const endpoint = (typeof CONFIG !== "undefined" && CONFIG.API_ENDPOINT) || "/quote";
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      // Show success
      for (let i = 1; i <= TOTAL_SLIDES; i++) {
        const el = document.getElementById(`slide${i}`);
        if (el) el.hidden = true;
      }
      document.getElementById("slideSuccess").hidden = false;
      document.getElementById("wizardNav").hidden    = true;
      document.querySelector(".wizard__progress").style.display = "none";

    } catch (err) {
      console.error("Quote submission error:", err);
      const errEl = document.getElementById("slide4-error");
      if (errEl) {
        errEl.textContent = "Something went wrong. Please call us at 1-647-885-0450.";
        errEl.hidden = false;
      }
      btnSubmit.disabled   = false;
      btnSubmit.textContent = "Submit Quote Request";
    }
  });

  function collectPayload() {
    const services = Array.from(
      document.querySelectorAll('input[name="services"]:checked')
    ).map((cb) => cb.value);

    return {
      services,
      box_count:        document.getElementById("box-count")?.value          || null,
      pool_refurb:      document.querySelector('input[name="pool_refurb"]')?.checked || false,
      heavy_count:      document.getElementById("heavy-count")?.value        || null,
      has_stairs:       document.getElementById("stairs-toggle")?.checked    || false,
      stair_count:      document.getElementById("stair-count")?.value        || null,
      origin_city:      document.getElementById("origin-city")?.value        || "",
      origin_postal:    document.getElementById("origin-postal")?.value      || "",
      dest_city:        document.getElementById("dest-city")?.value          || "",
      dest_postal:      document.getElementById("dest-postal")?.value        || "",
      name:             document.getElementById("contact-name")?.value       || "",
      email:            document.getElementById("contact-email")?.value      || "",
      phone:            document.getElementById("contact-phone")?.value      || "",
      move_date:        document.getElementById("move-date")?.value          || "",
      instructions:     document.getElementById("instructions")?.value       || "",
      "cf-turnstile-response": document.querySelector("[name=cf-turnstile-response]")?.value || "",
      middle_name:      document.getElementById("middle_name")?.value        || "",
    };
  }

  // Initialize to slide 1
  showSlide(1);
})();
