/** @odoo-module **/
/**
 * EcoSphere — Shared JavaScript Utilities
 * Helpers for formatting, colors, chart defaults, and OWL component mixins.
 */

import { registry } from "@web/core/registry";

// ─── Score Formatting ───────────────────────────────────────────────────────

/**
 * Returns a CSS class name based on ESG score range.
 * @param {number} score - ESG score 0–100
 * @returns {string} CSS class
 */
export function getScoreClass(score) {
    if (score >= 80) return "eco-score-excellent";
    if (score >= 60) return "eco-score-good";
    if (score >= 40) return "eco-score-average";
    return "eco-score-poor";
}

/**
 * Returns a label string based on ESG score range.
 * @param {number} score
 * @returns {string}
 */
export function getScoreLabel(score) {
    if (score >= 80) return "Excellent";
    if (score >= 60) return "Good";
    if (score >= 40) return "Needs Improvement";
    return "At Risk";
}

/**
 * Returns hex color for a score value (for Chart.js usage).
 * @param {number} score
 * @returns {string} hex color
 */
export function getScoreColor(score) {
    if (score >= 80) return "#10b981";  // emerald
    if (score >= 60) return "#3b82f6";  // blue
    if (score >= 40) return "#f59e0b";  // amber
    return "#f43f5e";                   // rose
}

// ─── ESG Pillar Colors ──────────────────────────────────────────────────────

export const ECO_COLORS = {
    env:        "#10b981",
    envLight:   "#d1fae5",
    soc:        "#3b82f6",
    socLight:   "#dbeafe",
    gov:        "#8b5cf6",
    govLight:   "#ede9fe",
    xp:         "#f59e0b",
    xpLight:    "#fef3c7",
    carbon:     "#64748b",
    carbonLight:"#f1f5f9",
    // Chart palette
    chart: [
        "#3b82f6", "#10b981", "#8b5cf6",
        "#f59e0b", "#f43f5e", "#06b6d4",
        "#84cc16", "#ec4899", "#f97316",
    ],
};

// ─── Chart.js Default Config ────────────────────────────────────────────────

/**
 * Returns default Chart.js options for EcoSphere charts.
 * @param {object} overrides - Optional option overrides
 * @returns {object}
 */
export function getChartDefaults(overrides = {}) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: false,
                labels: {
                    font: { family: "Inter, sans-serif", size: 12, weight: "600" },
                    color: "#6b7280",
                    usePointStyle: true,
                    pointStyleWidth: 10,
                },
            },
            tooltip: {
                backgroundColor: "#1f2937",
                titleColor: "#f9fafb",
                bodyColor: "#d1d5db",
                borderColor: "#374151",
                borderWidth: 1,
                cornerRadius: 8,
                padding: 12,
                titleFont: { family: "Inter, sans-serif", size: 13, weight: "700" },
                bodyFont: { family: "Inter, sans-serif", size: 12 },
            },
        },
        scales: {
            x: {
                grid: { color: "#f3f4f6", drawBorder: false },
                ticks: {
                    color: "#9ca3af",
                    font: { family: "Inter, sans-serif", size: 11, weight: "500" },
                },
            },
            y: {
                grid: { color: "#f3f4f6", drawBorder: false },
                ticks: {
                    color: "#9ca3af",
                    font: { family: "Inter, sans-serif", size: 11, weight: "500" },
                },
                beginAtZero: true,
            },
        },
        ...overrides,
    };
}

/**
 * Returns a gradient fill for Chart.js area charts.
 * @param {CanvasRenderingContext2D} ctx
 * @param {string} color - Hex color
 * @returns {CanvasGradient}
 */
export function createGradient(ctx, color) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, color + "40");   // 25% opacity at top
    gradient.addColorStop(1, color + "05");   // ~2% opacity at bottom
    return gradient;
}

// ─── Number Formatting ──────────────────────────────────────────────────────

/**
 * Format a large number with K/M suffix.
 * @param {number} value
 * @param {number} decimals
 * @returns {string}
 */
export function formatCompact(value, decimals = 1) {
    if (value >= 1_000_000) return (value / 1_000_000).toFixed(decimals) + "M";
    if (value >= 1_000) return (value / 1_000).toFixed(decimals) + "K";
    return value.toFixed(decimals);
}

/**
 * Format carbon value with unit.
 * @param {number} kg
 * @param {string} unit - 'kg' or 'tonne'
 * @returns {string}
 */
export function formatCarbon(kg, unit = "kg") {
    if (unit === "tonne") return (kg / 1000).toFixed(2) + " tCO₂e";
    return kg.toFixed(1) + " kg CO₂e";
}

/**
 * Format XP number with comma separators.
 * @param {number} xp
 * @returns {string}
 */
export function formatXP(xp) {
    return xp.toLocaleString() + " XP";
}

// ─── Date Helpers ───────────────────────────────────────────────────────────

/**
 * Returns days between today and a target date.
 * @param {string} dateStr - ISO date string
 * @returns {number}
 */
export function daysUntil(dateStr) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const target = new Date(dateStr);
    return Math.ceil((target - today) / (1000 * 60 * 60 * 24));
}

/**
 * Returns a relative time label ("2 days ago", "in 5 days", "Today").
 * @param {string} dateStr
 * @returns {string}
 */
export function relativeDate(dateStr) {
    const days = daysUntil(dateStr);
    if (days === 0) return "Today";
    if (days === 1) return "Tomorrow";
    if (days === -1) return "Yesterday";
    if (days > 0) return `in ${days} days`;
    return `${Math.abs(days)} days ago`;
}

// ─── Animated Counter ───────────────────────────────────────────────────────

/**
 * Animates a number counter from 0 to target value.
 * @param {HTMLElement} el - Target DOM element
 * @param {number} target - Final value
 * @param {number} duration - Animation duration in ms
 * @param {Function} formatter - Optional value formatter
 */
export function animateCounter(el, target, duration = 1000, formatter = (v) => Math.round(v)) {
    const start = performance.now();
    const initial = parseFloat(el.textContent) || 0;

    function step(timestamp) {
        const elapsed = timestamp - start;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = initial + (target - initial) * eased;
        el.textContent = formatter(current);
        if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
}

// ─── Register as OWL Service ────────────────────────────────────────────────

export const ecosphereUtils = {
    getScoreClass,
    getScoreLabel,
    getScoreColor,
    getChartDefaults,
    createGradient,
    formatCompact,
    formatCarbon,
    formatXP,
    daysUntil,
    relativeDate,
    animateCounter,
    ECO_COLORS,
};

registry.category("services").add("ecosphere_utils", {
    start() {
        return ecosphereUtils;
    },
});
