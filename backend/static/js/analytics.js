"use strict";

let mainChart = null;
let anomalyChart = null;
let analyticsLoading = false;

function formatTime(value) {
  const date =
    typeof value === "number"
      ? new Date(value < 1e12 ? value * 1000 : value)
      : new Date(value);

  return Number.isNaN(date.getTime())
    ? String(value)
    : date.toLocaleTimeString([], {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit",
      });
}

function chartOptions(yTitle, showZero = false) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: false,
    interaction: {
      mode: "index",
      intersect: false,
    },
    plugins: {
      legend: {
        position: "top",
        labels: {
          color: "#f8fafc",
          usePointStyle: false,
          boxWidth: 28,
          padding: 18,
          font: {
            size: 13,
            weight: "600",
          },
        },
      },
      tooltip: {
        backgroundColor: "#0f172a",
        titleColor: "#38bdf8",
        bodyColor: "#f8fafc",
        borderColor: "#334155",
        borderWidth: 1,
        padding: 12,
        displayColors: true,
      },
    },
    scales: {
      x: {
        grid: {
          color: "rgba(148, 163, 184, 0.09)",
        },
        ticks: {
          color: "#cbd5e1",
          maxTicksLimit: 10,
          maxRotation: 0,
          autoSkip: true,
        },
        border: {
          color: "#334155",
        },
      },
      y: {
        beginAtZero: showZero,
        title: {
          display: Boolean(yTitle),
          text: yTitle,
          color: "#cbd5e1",
        },
        grid: {
          color: "rgba(148, 163, 184, 0.12)",
        },
        ticks: {
          color: "#cbd5e1",
        },
        border: {
          color: "#334155",
        },
      },
    },
  };
}

function lineDataset(label, data, color) {
  return {
    label,
    data,
    borderColor: color,
    backgroundColor: color,
    borderWidth: 3,
    pointRadius: 2.5,
    pointHoverRadius: 6,
    pointBackgroundColor: color,
    pointBorderWidth: 0,
    tension: 0.25,
    fill: false,
    spanGaps: false,
  };
}

async function loadAnalytics() {
  if (analyticsLoading) return;
  analyticsLoading = true;

  try {
    const response = await fetch("/api/history?limit=200", {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`History API returned HTTP ${response.status}`);
    }

    const rows = await response.json();

    if (!Array.isArray(rows)) {
      throw new Error("History API did not return a list");
    }

    // The API may return newest-first results.
    const orderedRows = [...rows].reverse();

    const labels = orderedRows.map((row) => formatTime(row.timestamp));

    const mainData = {
      labels,
      datasets: [
        lineDataset(
          "Voltage (V)",
          orderedRows.map((row) => row.voltage ?? null),
          "#22d3ee",
        ),
        lineDataset(
          "Current (A)",
          orderedRows.map((row) => row.current ?? null),
          "#00f59b",
        ),
        lineDataset(
          "Power (W)",
          orderedRows.map((row) => row.power ?? null),
          "#ff9800",
        ),
      ],
    };

    const anomalyData = {
      labels,
      datasets: [
        lineDataset(
          "Isolation Forest Anomaly Score",
          orderedRows.map((row) => row.anomaly_score ?? null),
          "#a78bfa",
        ),
      ],
    };

    const mainCanvas = document.getElementById("mainChart");
    const anomalyCanvas = document.getElementById("anomalyChart");

    if (mainCanvas) {
      if (!mainChart) {
        mainChart = new Chart(mainCanvas, {
          type: "line",
          data: mainData,
          options: chartOptions("Sensor value", true),
        });
      } else {
        mainChart.data = mainData;
        mainChart.update("none");
      }
    }

    if (anomalyCanvas) {
      if (!anomalyChart) {
        anomalyChart = new Chart(anomalyCanvas, {
          type: "line",
          data: anomalyData,
          options: chartOptions("Anomaly score", false),
        });
      } else {
        anomalyChart.data = anomalyData;
        anomalyChart.update("none");
      }
    }
  } catch (error) {
    console.error("Analytics loading failed:", error);
  } finally {
    analyticsLoading = false;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadAnalytics();
  setInterval(loadAnalytics, 5000);
});
