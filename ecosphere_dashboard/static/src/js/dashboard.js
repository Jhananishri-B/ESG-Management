/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, useState, onMounted, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

class EsgDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.actionService = useService("action");
        
        this.state = useState({
            data: null,
            isLoading: true,
        });

        this.chartCanvasRef = useRef("chartCanvas");

        onWillStart(async () => {
            await this.fetchDashboardData();
            // Load Chart.js from CDN since we want a modern version easily available without relying on internal bundles
            await loadJS("https://cdn.jsdelivr.net/npm/chart.js");
        });

        onMounted(() => {
            this.renderChart();
        });
    }

    async fetchDashboardData() {
        try {
            const result = await this.rpc("/ecosphere/dashboard_data", {});
            this.state.data = result;
            this.state.isLoading = false;
        } catch (error) {
            console.error("Failed to load ESG Dashboard data:", error);
            this.state.isLoading = false;
        }
    }

    renderChart() {
        if (!this.state.data || !this.chartCanvasRef.el || typeof Chart === "undefined") {
            return;
        }

        const ctx = this.chartCanvasRef.el.getContext('2d');
        const trends = this.state.data.trends;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: trends.labels,
                datasets: [
                    {
                        label: 'Environmental',
                        data: trends.data.env,
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Social',
                        data: trends.data.soc,
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Governance',
                        data: trends.data.gov,
                        borderColor: '#8b5cf6',
                        backgroundColor: 'rgba(139, 92, 246, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(17, 24, 39, 0.9)',
                        titleFont: { size: 13 },
                        bodyFont: { size: 13 },
                        padding: 10,
                        cornerRadius: 8,
                        displayColors: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        grid: {
                            color: '#f3f4f6',
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        }
                    }
                }
            }
        });
    }

    openDepartment(deptId) {
        this.actionService.doAction({
            type: "ir.actions.act_window",
            res_model: "esg.department",
            res_id: deptId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

EsgDashboard.template = "ecosphere_dashboard.Dashboard";

registry.category("actions").add("ecosphere.dashboard", EsgDashboard);
