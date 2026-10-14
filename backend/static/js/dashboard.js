"use strict";

const $ = (id) => document.getElementById(id);

let updateInProgress = false;
let resetInProgress = false;
let previousReading = null;

function setText(id, value) {
    const element = $(id);
    if (element) {
        element.textContent = value;
    }
}

function formatNumber(value, decimals = 2) {
    const number = Number(value);
    return value !== null &&
           value !== undefined &&
           value !== "" &&
           Number.isFinite(number)
        ? number.toFixed(decimals)
        : "N/A";
}

function setStatusStyle(element, status) {
    if (!element) return;

    element.classList.remove(
        "status-normal",
        "status-alert",
        "status-off",
        "status-warning"
    );

    const value = String(status || "").toUpperCase();

    if (
        value.includes("ANOMALY") ||
        value.includes("TRIPPED") ||
        value.includes("ERROR") ||
        value.includes("ALERT")
    ) {
        element.classList.add("status-alert");
    } else if (
        value.includes("NORMAL") ||
        value.includes("CHARGING") ||
        value === "ON" ||
        value === "DETECTED" ||
        value === "ACTIVE"
    ) {
        element.classList.add("status-normal");
    } else {
        element.classList.add("status-off");
    }
}

function getCurrentTime() {
    return new Date().toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit"
    });
}

function updateClock() {
    setText("clock", getCurrentTime());
}

function updateReadingsTable(data) {
    const tbody = $("readings-body");
    if (!tbody) return;

    const row = document.createElement("tr");

    const status = data.state || data.anomaly?.status || "UNKNOWN";

    const values = [
        getCurrentTime(),
        `${formatNumber(data.voltage)} V`,
        `${formatNumber(data.current)} A`,
        `${formatNumber(data.power)} W`,
        status
    ];

    values.forEach((value, index) => {
        const cell = document.createElement("td");
        cell.textContent = value;

        if (index === values.length - 1) {
            setStatusStyle(cell, status);
        }

        row.appendChild(cell);
    });

    tbody.querySelector(".empty-state")?.parentElement.remove();
    tbody.prepend(row);

    // Keep the most recent 10 readings in the table.
    while (tbody.rows.length > 10) {
        tbody.deleteRow(tbody.rows.length - 1);
    }
}

function displayData(data) {
    setText("vehicle", data.vehicle_present === true
        ? "DETECTED"
        : data.vehicle_present === false
            ? "NOT DETECTED"
            : "UNKNOWN");

    setText("charging", data.relay_on === true
        ? "ACTIVE"
        : data.relay_on === false
            ? "OFF"
            : "UNKNOWN");

    setText("relay", data.relay_on === true
        ? "ON"
        : data.relay_on === false
            ? "OFF"
            : "UNKNOWN");

    setText("voltage", `${formatNumber(data.voltage)} V`);
    setText("current", `${formatNumber(data.current)} A`);
    setText("power", `${formatNumber(data.power)} W`);

    const anomalyStatus = data.anomaly?.status ||
        (data.anomaly?.is_anomaly === true
            ? "ANOMALY"
            : data.anomaly?.is_anomaly === false
                ? "NORMAL"
                : "NOT EVALUATED");

    setText("anomaly", anomalyStatus);
    setText("protection", data.state || "UNKNOWN");
    setText("reason", data.reason || "No reason reported");

    setStatusStyle($("anomaly"), anomalyStatus);
    setStatusStyle($("protection"), data.state);
    setStatusStyle($("relay"), data.relay_on ? "ON" : "OFF");

    const panelIndicator = document.querySelector(".panel-indicator");
    if (panelIndicator) {
        panelIndicator.classList.toggle(
            "status-alert",
            String(data.state || "").includes("TRIPPED")
        );
    }

    // Avoid inserting duplicate table rows when the API timestamp
    // has not changed.
    const timestamp = data.timestamp ?? null;

    if (timestamp !== null && timestamp !== previousReading) {
        updateReadingsTable(data);
        previousReading = timestamp;
    } else if (timestamp === null) {
        updateReadingsTable(data);
    }
}

async function update() {
    if (updateInProgress) return;

    updateInProgress = true;

    try {
        const response = await fetch("/api/monitor", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Monitoring API returned HTTP ${response.status}`);
        }

        const data = await response.json();
        displayData(data);
    } catch (error) {
        console.error("Dashboard update failed:", error);
        setText("reason", "Unable to retrieve monitoring data");
    } finally {
        updateInProgress = false;
    }
}

const resetButton = $("reset");

if (resetButton) {
    resetButton.addEventListener("click", async () => {
        if (resetInProgress) return;

        resetInProgress = true;
        resetButton.disabled = true;
        resetButton.textContent = "Resetting...";

        try {
            const response = await fetch("/api/reset-protection", {
                method: "POST",
                cache: "no-store"
            });

            if (!response.ok) {
                throw new Error(
                    `Protection reset returned HTTP ${response.status}`
                );
            }

            await update();
        } catch (error) {
            console.error("Protection reset failed:", error);
            setText("reason", "Protection reset failed. Check backend logs.");
        } finally {
            resetInProgress = false;
            resetButton.disabled = false;
            resetButton.textContent = "Reset Protection";
        }
    });
}

updateClock();
update();

setInterval(updateClock, 1000);
setInterval(update, 1000);
