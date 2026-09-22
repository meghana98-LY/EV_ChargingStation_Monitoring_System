async function updateDashboard() {
  try {
    const response = await fetch("/api/monitor", {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Failed to fetch monitoring data");
    }

    const data = await response.json();

    // ====================================================
    // ELECTRICAL PARAMETERS
    // ====================================================

    document.getElementById("voltage").textContent = `${data.voltage} V`;

    document.getElementById("current").textContent = `${data.current} A`;

    document.getElementById("power").textContent = `${data.power} W`;

    document.getElementById("distance").textContent = `${data.distance_cm} cm`;

    // ====================================================
    // STATUS
    // ====================================================

    document.getElementById("vehicle-status").textContent = data.vehicle_status;

    document.getElementById("charging-status").textContent =
      data.charging_status;

    document.getElementById("anomaly-status").textContent = data.anomaly_status;

    document.getElementById("protection-status").textContent =
      data.protection_status;

   

    // ====================================================
    // VEHICLE BADGE
    // ====================================================

    const vehicleBadge = document.getElementById("vehicle-badge");

    vehicleBadge.textContent = data.vehicle_present
      ? "VEHICLE PRESENT"
      : "NO VEHICLE";

    // ====================================================
    // CHARGING BADGE
    // ====================================================

    const chargingBadge = document.getElementById("charging-badge");

    chargingBadge.textContent = data.charging_active ? "ACTIVE" : "INACTIVE";

    // ====================================================
    // ANOMALY BADGE
    // ====================================================

    const anomalyBadge = document.getElementById("anomaly-badge");

    anomalyBadge.textContent = data.is_anomaly ? "ABNORMAL" : "NORMAL";

    // ====================================================
    // PROTECTION BADGE
    // ====================================================

    const protectionBadge = document.getElementById("protection-badge");

    protectionBadge.textContent = data.protection_triggered
      ? "PROTECTION"
      : data.protection_status;

    // ====================================================
    // LAST UPDATE
    // ====================================================

    document.getElementById("last-update").textContent =
      new Date().toLocaleTimeString();
  } catch (error) {
    console.error("Dashboard update failed:", error);
  }
}

updateDashboard();
// ============================================================
// LOAD RECENT MONITORING HISTORY
// ============================================================

async function loadHistory() {

    try {

        const response =
            await fetch(
                "/api/history",
                {
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "Failed to load monitoring history"
            );

        }


        const result =
            await response.json();


        const tableBody =
            document.getElementById(
                "history-table-body"
            );


        if (!tableBody) {
            return;
        }


        if (
            !result.records ||
            result.records.length === 0
        ) {

            tableBody.innerHTML = `
                <tr>
                    <td colspan="9">
                        No monitoring records available.
                    </td>
                </tr>
            `;

            return;
        }


        tableBody.innerHTML =
            result.records
                .map(
                    record => {

                        /*
                         * SQLite record structure:
                         *
                         * 0  id
                         * 1  timestamp
                         * 2  voltage
                         * 3  current
                         * 4  power
                         * 5  distance_cm
                         * 6  vehicle_present
                         * 7  vehicle_status
                         * 8  charging_active
                         * 9  charging_status
                         * 10 anomaly_status
                         * 11 is_anomaly
                         * 12 anomaly_score
                         * 13 model_available
                         * 14 protection_triggered
                         * 15 protection_status
                         * 16 protection_reason
                         */


                        const timestamp =
                            new Date(
                                record[1]
                            );


                        const time =
                            timestamp.toLocaleTimeString();


                        const anomalyClass =
                            record[10] === "ANOMALY"
                                ? "history-anomaly"
                                : "history-normal";


                        const protectionClass =
                            record[14]
                                ? "history-protection"
                                : (
                                    record[15] === "WARNING"
                                        ? "history-warning"
                                        : "history-normal"
                                );


                        return `
                            <tr>

                                <td>
                                    ${time}
                                </td>

                                <td>
                                    ${record[2]} V
                                </td>

                                <td>
                                    ${record[3]} A
                                </td>

                                <td>
                                    ${record[4]} W
                                </td>

                                <td>
                                    ${record[5]} cm
                                </td>

                                <td>
                                    ${record[7]}
                                </td>

                                <td>
                                    ${record[9]}
                                </td>

                                <td class="${anomalyClass}">
                                    ${record[10]}
                                </td>

                                <td class="${protectionClass}">
                                    ${record[15]}
                                </td>

                            </tr>
                        `;

                    }
                )
                .join("");


    } catch (error) {

        console.error(
            "History update failed:",
            error
        );

    }
}

updateDashboard();

loadHistory();

setInterval(updateDashboard, 1000);

setInterval(loadHistory, 3000);

