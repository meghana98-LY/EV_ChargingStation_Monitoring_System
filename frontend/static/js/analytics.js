/**
 * EV Charging Analytics Dashboard
 *
 * Live data source:
 *     /api/monitor
 *
 * Graphs:
 *     1. Electrical Parameters
 *        - Voltage
 *        - Current
 *        - Power
 *
 *     2. Isolation Forest
 *        - Anomaly Score
 */

"use strict";

// ============================================================
// CONFIGURATION
// ============================================================

const MAX_POINTS = 30;
const UPDATE_INTERVAL = 1000;

// ============================================================
// HISTORY ARRAYS
// ============================================================

const voltageHistory = [];
const currentHistory = [];
const powerHistory = [];
const anomalyHistory = [];
const timeHistory = [];

// ============================================================
// CANVAS SETUP
// ============================================================

const electricalCanvas = document.getElementById("electrical-chart");

const anomalyCanvas = document.getElementById("anomaly-chart");

// ============================================================
// UTILITY
// ============================================================

function getCanvasSize(canvas) {
  if (!canvas) {
    return null;
  }

  const rect = canvas.getBoundingClientRect();

  const width = Math.max(rect.width, 400);
  const height = 320;

  const devicePixelRatio = window.devicePixelRatio || 1;

  canvas.width = width * devicePixelRatio;
  canvas.height = height * devicePixelRatio;

  const context = canvas.getContext("2d");

  context.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);

  context.clearRect(0, 0, width, height);

  return {
    context,
    width,
    height,
  };
}

// ============================================================
// COMMON CHART AREA
// ============================================================

function getChartArea(width, height) {
  const left = 60;
  const right = 60;
  const top = 30;
  const bottom = 45;

  return {
    left,
    right,
    top,
    bottom,
    width: width - left - right,
    height: height - top - bottom,
  };
}

// ============================================================
// DRAW GRID
// ============================================================

function drawGrid(context, area, minValue, maxValue, unit) {
  context.strokeStyle = "#e5e9ed";
  context.lineWidth = 1;

  context.fillStyle = "#6f7b85";
  context.font = "11px Arial";
  context.textAlign = "right";

  for (let i = 0; i <= 5; i++) {
    const y = area.top + (area.height * i) / 5;

    context.beginPath();

    context.moveTo(area.left, y);

    context.lineTo(area.left + area.width, y);

    context.stroke();

    const value = maxValue - ((maxValue - minValue) * i) / 5;

    context.fillText(value.toFixed(0), area.left - 8, y + 4);
  }

  context.textAlign = "left";

  context.fillText(unit, 8, area.top - 8);
}

// ============================================================
// DRAW X-AXIS
// ============================================================

function drawXAxis(context, area, labels) {
  if (!labels.length) {
    return;
  }

  context.fillStyle = "#6f7b85";
  context.font = "11px Arial";

  context.textAlign = "left";

  context.fillText(labels[0], area.left, area.top + area.height + 30);

  if (labels.length > 1) {
    context.textAlign = "right";

    context.fillText(
      labels[labels.length - 1],
      area.left + area.width,
      area.top + area.height + 30,
    );
  }

  context.textAlign = "left";
}

// ============================================================
// DRAW LINE
// ============================================================

function drawLine(context, values, minValue, maxValue, area, lineWidth = 2.5) {
  if (!values.length) {
    return;
  }

  if (values.length === 1) {
    const x = area.left + area.width / 2;

    const y =
      area.top +
      area.height * (1 - (values[0] - minValue) / (maxValue - minValue));

    context.beginPath();

    context.arc(x, y, 4, 0, Math.PI * 2);

    context.fill();

    return;
  }

  context.beginPath();

  values.forEach((value, index) => {
    const x = area.left + (area.width * index) / (values.length - 1);

    const y =
      area.top + area.height * (1 - (value - minValue) / (maxValue - minValue));

    if (index === 0) {
      context.moveTo(x, y);
    } else {
      context.lineTo(x, y);
    }
  });

  context.lineWidth = lineWidth;

  context.stroke();
}

// ============================================================
// ELECTRICAL PARAMETERS GRAPH
// ============================================================
//
// Voltage, Current and Power are displayed in ONE graph.
//
// Because they use different physical units and scales,
// each series is normalized against its own recent range.
// The actual values are displayed in the legend.
//
// This lets us observe how the three parameters change
// together without allowing Power (W) to hide Voltage (V)
// and Current (A).
// ============================================================

function drawElectricalChart() {
  const chart = getCanvasSize(electricalCanvas);

  if (!chart) {
    return;
  }

  const { context, width, height } = chart;

  const area = getChartArea(width, height);

  if (timeHistory.length === 0) {
    context.fillStyle = "#7b858d";
    context.font = "14px Arial";

    context.fillText("Waiting for electrical data...", 20, 40);

    return;
  }

  // --------------------------------------------------------
  // Determine common display scale
  // --------------------------------------------------------

  const allValues = [...voltageHistory, ...currentHistory, ...powerHistory];

  let minValue = Math.min(...allValues);

  let maxValue = Math.max(...allValues);

  if (minValue === maxValue) {
    const padding = Math.max(Math.abs(minValue) * 0.1, 1);

    minValue -= padding;
    maxValue += padding;
  } else {
    const padding = (maxValue - minValue) * 0.1;

    minValue -= padding;
    maxValue += padding;
  }

  // --------------------------------------------------------
  // Grid
  // --------------------------------------------------------

  drawGrid(context, area, minValue, maxValue, "Electrical trend");

  drawXAxis(context, area, timeHistory);

  // --------------------------------------------------------
  // Normalize each parameter
  // --------------------------------------------------------

  function normalize(values) {
    if (!values.length) {
      return [];
    }

    const seriesMin = Math.min(...values);

    const seriesMax = Math.max(...values);

    if (seriesMin === seriesMax) {
      return values.map(() => 0.5);
    }

    return values.map((value) => (value - seriesMin) / (seriesMax - seriesMin));
  }

  const normalizedVoltage = normalize(voltageHistory);

  const normalizedCurrent = normalize(currentHistory);

  const normalizedPower = normalize(powerHistory);

  // --------------------------------------------------------
  // Draw normalized series
  // --------------------------------------------------------

  function drawNormalizedLine(values, lineColor) {
    if (!values.length) {
      return;
    }

    context.beginPath();

    values.forEach((value, index) => {
      const x =
        area.left + (area.width * index) / Math.max(values.length - 1, 1);

      const y = area.top + area.height * (1 - value);

      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });

    context.strokeStyle = lineColor;

    context.lineWidth = 2.5;

    context.stroke();

    // Data points

    values.forEach((value, index) => {
      const x =
        area.left + (area.width * index) / Math.max(values.length - 1, 1);

      const y = area.top + area.height * (1 - value);

      context.beginPath();

      context.arc(x, y, 2.5, 0, Math.PI * 2);

      context.fillStyle = lineColor;

      context.fill();
    });
  }

  drawNormalizedLine(normalizedVoltage, "#1976d2");

  drawNormalizedLine(normalizedCurrent, "#e67e22");

  drawNormalizedLine(normalizedPower, "#7b3fc6");

  // --------------------------------------------------------
  // Legend
  // --------------------------------------------------------

  const latestVoltage = voltageHistory[voltageHistory.length - 1];

  const latestCurrent = currentHistory[currentHistory.length - 1];

  const latestPower = powerHistory[powerHistory.length - 1];

  const legendY = 18;

  context.font = "12px Arial";

  // Voltage

  context.fillStyle = "#1976d2";

  context.fillRect(area.left, legendY - 9, 12, 3);

  context.fillStyle = "#263238";

  context.fillText(`Voltage: ${latestVoltage} V`, area.left + 18, legendY);

  // Current

  context.fillStyle = "#e67e22";

  context.fillRect(area.left + 150, legendY - 9, 12, 3);

  context.fillStyle = "#263238";

  context.fillText(`Current: ${latestCurrent} A`, area.left + 168, legendY);

  // Power

  context.fillStyle = "#7b3fc6";

  context.fillRect(area.left + 300, legendY - 9, 12, 3);

  context.fillStyle = "#263238";

  context.fillText(`Power: ${latestPower} W`, area.left + 318, legendY);
}

// ============================================================
// ISOLATION FOREST GRAPH
// ============================================================

function drawAnomalyChart() {
  const chart = getCanvasSize(anomalyCanvas);

  if (!chart) {
    return;
  }

  const { context, width, height } = chart;

  const area = getChartArea(width, height);

  if (anomalyHistory.length === 0) {
    context.fillStyle = "#7b858d";
    context.font = "14px Arial";

    context.fillText("Waiting for anomaly data...", 20, 40);

    return;
  }

  let minValue = Math.min(...anomalyHistory, 0);

  let maxValue = Math.max(...anomalyHistory, 0);

  if (minValue === maxValue) {
    minValue -= 0.1;
    maxValue += 0.1;
  } else {
    const padding = (maxValue - minValue) * 0.15;

    minValue -= padding;
    maxValue += padding;
  }

  // --------------------------------------------------------
  // Grid
  // --------------------------------------------------------

  context.strokeStyle = "#e5e9ed";

  context.lineWidth = 1;

  context.fillStyle = "#6f7b85";

  context.font = "11px Arial";

  context.textAlign = "right";

  for (let i = 0; i <= 5; i++) {
    const y = area.top + (area.height * i) / 5;

    context.beginPath();

    context.moveTo(area.left, y);

    context.lineTo(area.left + area.width, y);

    context.stroke();

    const value = maxValue - ((maxValue - minValue) * i) / 5;

    context.fillText(value.toFixed(3), area.left - 8, y + 4);
  }

  context.textAlign = "left";

  context.fillStyle = "#6f7b85";

  context.fillText("Anomaly Score", 8, area.top - 8);

  // --------------------------------------------------------
  // Zero decision reference
  // --------------------------------------------------------

  if (minValue <= 0 && maxValue >= 0) {
    const zeroY =
      area.top + area.height * (1 - (0 - minValue) / (maxValue - minValue));

    context.beginPath();

    context.setLineDash([6, 5]);

    context.moveTo(area.left, zeroY);

    context.lineTo(area.left + area.width, zeroY);

    context.strokeStyle = "#555";

    context.lineWidth = 1.5;

    context.stroke();

    context.setLineDash([]);

    context.fillStyle = "#555";

    context.font = "11px Arial";

    context.fillText("Decision boundary", area.left + 8, zeroY - 6);
  }

  // --------------------------------------------------------
  // X-axis
  // --------------------------------------------------------

  drawXAxis(context, area, timeHistory);

  // --------------------------------------------------------
  // Anomaly line
  // --------------------------------------------------------

  if (anomalyHistory.length === 1) {
    const x = area.left + area.width / 2;

    const y =
      area.top +
      area.height *
        (1 - (anomalyHistory[0] - minValue) / (maxValue - minValue));

    context.beginPath();

    context.arc(x, y, 4, 0, Math.PI * 2);

    context.fillStyle = anomalyHistory[0] < 0 ? "#dc3545" : "#198754";

    context.fill();
  } else {
    context.beginPath();

    anomalyHistory.forEach((value, index) => {
      const x = area.left + (area.width * index) / (anomalyHistory.length - 1);

      const y =
        area.top +
        area.height * (1 - (value - minValue) / (maxValue - minValue));

      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });

    context.strokeStyle = "#dc3545";

    context.lineWidth = 2.5;

    context.stroke();

    // Data points

    anomalyHistory.forEach((value, index) => {
      const x = area.left + (area.width * index) / (anomalyHistory.length - 1);

      const y =
        area.top +
        area.height * (1 - (value - minValue) / (maxValue - minValue));

      context.beginPath();

      context.arc(x, y, 3, 0, Math.PI * 2);

      context.fillStyle = value < 0 ? "#dc3545" : "#198754";

      context.fill();
    });
  }

  // --------------------------------------------------------
  // Current value
  // --------------------------------------------------------

  const latestScore = anomalyHistory[anomalyHistory.length - 1];

  context.fillStyle = latestScore < 0 ? "#dc3545" : "#198754";

  context.font = "bold 13px Arial";

  context.fillText(
    `Current Score: ${latestScore.toFixed(6)}`,
    area.left,
    height - 8,
  );
}

// ============================================================
// UPDATE GRAPHS
// ============================================================

function updateGraphs() {
  drawElectricalChart();

  drawAnomalyChart();
}

// ============================================================
// ADD READING
// ============================================================

function addReading(data) {
  const now = new Date();

  timeHistory.push(
    now.toLocaleTimeString([], {
      minute: "2-digit",
      second: "2-digit",
    }),
  );

  voltageHistory.push(Number(data.voltage));

  currentHistory.push(Number(data.current));

  powerHistory.push(Number(data.power));

  if (data.anomaly_score !== null && data.anomaly_score !== undefined) {
    anomalyHistory.push(Number(data.anomaly_score));
  } else {
    anomalyHistory.push(0);
  }

  // --------------------------------------------------------
  // Keep latest readings only
  // --------------------------------------------------------

  while (timeHistory.length > MAX_POINTS) {
    timeHistory.shift();

    voltageHistory.shift();

    currentHistory.shift();

    powerHistory.shift();

    anomalyHistory.shift();
  }
}

// ============================================================
// UPDATE ANALYSIS
// ============================================================

function updateAnalysis(data) {
  const analysisScore = document.getElementById("analysis-score");

  if (analysisScore) {
    analysisScore.textContent = data.anomaly_score ?? "N/A";
  }

  const analysisState = document.getElementById("analysis-state");

  if (analysisState) {
    analysisState.textContent = data.anomaly_status;
  }

  const analysisProtection = document.getElementById("analysis-protection");

  if (analysisProtection) {
    analysisProtection.textContent = data.protection_status;
  }

  const analysisVehicle = document.getElementById("analysis-vehicle");

  if (analysisVehicle) {
    analysisVehicle.textContent = data.vehicle_present
      ? "Vehicle Present"
      : "No Vehicle Detected";
  }

  const protectionReason = document.getElementById("protection-reason");

  if (protectionReason) {
    protectionReason.textContent = data.protection_reason;
  }

  const model = document.getElementById("model-status");

  if (model) {
    model.textContent = data.model_available
      ? "MODEL AVAILABLE"
      : "MODEL NOT TRAINED";
  }

  const result = document.getElementById("logic-result");

  if (!result) {
    return;
  }

  if (data.protection_status === "PROTECTION_TRIGGERED") {
    result.textContent = "SYSTEM STATUS: PROTECTION TRIGGERED";

    result.style.background = "#fdebed";

    result.style.color = "#b4232d";
  } else if (data.protection_status === "WARNING") {
    result.textContent = "SYSTEM STATUS: WARNING";

    result.style.background = "#fff7df";

    result.style.color = "#956d00";
  } else {
    result.textContent = "SYSTEM STATUS: SAFE";

    result.style.background = "#e8f7ee";

    result.style.color = "#18864b";
  }
}

// ============================================================
// UPDATE SUMMARY
// ============================================================

function updateSummary(data) {
  const voltage = document.getElementById("voltage");

  if (voltage) {
    voltage.textContent = `${data.voltage} V`;
  }

  const current = document.getElementById("current");

  if (current) {
    current.textContent = `${data.current} A`;
  }

  const power = document.getElementById("power");

  if (power) {
    power.textContent = `${data.power} W`;
  }

  const voltageCurrent = document.getElementById("voltage-current");

  if (voltageCurrent) {
    voltageCurrent.textContent = `${data.voltage} V`;
  }

  const currentCurrent = document.getElementById("current-current");

  if (currentCurrent) {
    currentCurrent.textContent = `${data.current} A`;
  }

  const powerCurrent = document.getElementById("power-current");

  if (powerCurrent) {
    powerCurrent.textContent = `${data.power} W`;
  }

  const anomalyCurrent = document.getElementById("anomaly-current");

  if (anomalyCurrent) {
    anomalyCurrent.textContent = data.anomaly_score ?? "N/A";
  }

  const vehicleStatus = document.getElementById("vehicle-status");

  if (vehicleStatus) {
    vehicleStatus.textContent = data.vehicle_status;
  }

  const chargingStatus = document.getElementById("charging-status");

  if (chargingStatus) {
    chargingStatus.textContent = data.charging_status;
  }
}

// ============================================================
// MAIN UPDATE
// ============================================================

async function updateAnalytics() {
  try {
    const response = await fetch("/api/monitor", {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error("Monitoring API failed.");
    }

    const data = await response.json();

    // Update dashboard values
    updateSummary(data);

    // Update intelligent analysis
    updateAnalysis(data);

    // Add new graph point
    addReading(data);

    // Redraw both graphs
    updateGraphs();

    // Update timestamp
    const lastUpdate = document.getElementById("last-update");

    if (lastUpdate) {
      lastUpdate.textContent = new Date().toLocaleTimeString();
    }
  } catch (error) {
    console.error("Analytics update failed:", error);
  }
}

// ============================================================
// START
// ============================================================

updateAnalytics();

// Existing history loader
if (typeof loadHistory === "function") {
  loadHistory();
}

// ============================================================
// LIVE UPDATE
// ============================================================

setInterval(updateAnalytics, UPDATE_INTERVAL);

if (typeof loadHistory === "function") {
  setInterval(loadHistory, 3000);
}

// ============================================================
// RESIZE
// ============================================================

window.addEventListener("resize", updateGraphs);
