let mainChart = null;
let anomalyChart = null;

function formatTime(value) {
    const date = typeof value === "number"
        ? new Date(value < 1e12 ? value * 1000 : value)
        : new Date(value);

    return Number.isNaN(date.getTime())
        ? String(value)
        : date.toLocaleTimeString();
}

async function loadAnalytics() {
    try {
        const response = await fetch("/api/history?limit=200", {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`History API returned HTTP ${response.status}`);
        }

        const rows = await response.json();

        if (!Array.isArray(rows)) {
            throw new Error("History API did not return a list");
        }

        // Database queries often return newest rows first.
        rows.reverse();

        const labels = rows.map(row => formatTime(row.timestamp));

        const mainData = {
            labels,
            datasets: [
                {
                    label: "Voltage (V)",
                    data: rows.map(row => row.voltage ?? null),
                    borderColor: "#2563eb",
                    tension: 0.2
                },
                {
                    label: "Current (A)",
                    data: rows.map(row => row.current ?? null),
                    borderColor: "#dc2626",
                    tension: 0.2
                },
                {
                    label: "Power (W)",
                    data: rows.map(row => row.power ?? null),
                    borderColor: "#d97706",
                    tension: 0.2
                }
            ]
        };

        const anomalyData = {
            labels,
            datasets: [{
                label: "Isolation Forest Anomaly Score",
                data: rows.map(row => row.anomaly_score ?? null),
                borderColor: "#7c3aed",
                tension: 0.2,
                spanGaps: false
            }]
        };

        if (!mainChart) {
            mainChart = new Chart(
                document.getElementById("mainChart"),
                {
                    type: "line",
                    data: mainData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        scales: {
                            x: { ticks: { maxTicksLimit: 10 } },
                            y: { beginAtZero: false }
                        }
                    }
                }
            );
        } else {
            mainChart.data = mainData;
            mainChart.update("none");
        }

        if (!anomalyChart) {
            anomalyChart = new Chart(
                document.getElementById("anomalyChart"),
                {
                    type: "line",
                    data: anomalyData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        animation: false,
                        scales: {
                            x: { ticks: { maxTicksLimit: 10 } },
                            y: { beginAtZero: false }
                        }
                    }
                }
            );
        } else {
            anomalyChart.data = anomalyData;
            anomalyChart.update("none");
        }
    } catch (error) {
        console.error("Analytics loading failed:", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadAnalytics();
    setInterval(loadAnalytics, 5000);
});
