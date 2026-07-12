# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class CarbonForecast(models.Model):
    """
    Carbon Forecast: Linear trend projection of carbon emissions.
    Uses historical carbon transaction data to project future emissions,
    supporting management decision-making and target setting.
    """
    _name = 'carbon.forecast'
    _description = 'Carbon Emission Forecast'
    _order = 'forecast_date desc'

    name = fields.Char(string='Forecast Name', required=True)
    department_id = fields.Many2one(
        'esg.department', string='Department', required=True, ondelete='cascade')
    forecast_date = fields.Date(
        string='Forecast Generated', default=fields.Date.today, readonly=True)

    # Historical data window
    history_months = fields.Integer(
        string='History Window (months)', default=6,
        help='Number of past months used to calculate the trend')
    forecast_months = fields.Integer(
        string='Forecast Horizon (months)', default=6)

    # Trend data (stored as JSON string for portability)
    trend_slope = fields.Float(
        string='Monthly Trend (kg)', digits=(10, 2),
        help='Average monthly change in carbon emissions (+/- kg CO₂e)')
    baseline_monthly = fields.Float(
        string='Baseline Monthly (kg CO₂e)', digits=(10, 2))

    # Forecast summary
    forecast_total_kg = fields.Float(
        string='Projected Total (kg CO₂e)', digits=(10, 2))
    forecast_vs_target_pct = fields.Float(
        string='Forecast vs Target (%)', digits=(5, 2))
    on_track = fields.Boolean(string='On Track', default=True)

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published'),
    ], default='draft')
    notes = fields.Text(string='Analysis Notes')

    def action_generate(self):
        """
        Generate forecast using linear regression on historical carbon data.
        Groups past transactions by month, computes slope, projects forward.
        """
        self.ensure_one()
        CarbonTx = self.env['carbon.transaction']
        today = fields.Date.today()
        history_start = today - timedelta(days=self.history_months * 30)

        # Aggregate monthly carbon for this department
        txs = CarbonTx.search([
            ('department_id', '=', self.department_id.id),
            ('state', 'in', ('confirmed', 'verified')),
            ('date', '>=', history_start),
        ])

        # Build monthly totals dict
        monthly = {}
        for tx in txs:
            month_key = tx.date.strftime('%Y-%m')
            monthly[month_key] = monthly.get(month_key, 0) + tx.carbon_kg

        if not monthly:
            self.write({
                'trend_slope': 0,
                'baseline_monthly': 0,
                'forecast_total_kg': 0,
                'notes': 'No historical data found for this department.',
                'state': 'published',
            })
            return

        values = list(monthly.values())
        n = len(values)
        mean_val = sum(values) / n
        baseline = mean_val

        # Simple linear regression: slope = cov(x,y)/var(x)
        if n > 1:
            xs = list(range(n))
            mean_x = sum(xs) / n
            cov = sum((xs[i] - mean_x) * (values[i] - mean_val) for i in range(n))
            var_x = sum((x - mean_x) ** 2 for x in xs)
            slope = cov / var_x if var_x else 0
        else:
            slope = 0

        # Project forward
        projected = sum(
            max(baseline + slope * (n + i), 0)
            for i in range(self.forecast_months)
        )

        dept = self.department_id
        target = dept.carbon_target_kg
        vs_target = (projected / target * 100) if target else 0
        on_track = projected <= target if target else True

        # Auto-generate notes
        direction = 'increasing' if slope > 0 else 'decreasing'
        notes = (
            f'Based on {n} months of data ({history_start} to {today}).\n'
            f'Average monthly emissions: {baseline:.0f} kg CO₂e.\n'
            f'Monthly trend: {slope:+.0f} kg ({direction}).\n'
            f'Projected {self.forecast_months}-month total: {projected:,.0f} kg CO₂e.\n'
            f'Department target: {target:,.0f} kg CO₂e → '
            f'{"✅ On track" if on_track else "⚠️ At risk of exceeding target"}.'
        )

        self.write({
            'trend_slope': slope,
            'baseline_monthly': baseline,
            'forecast_total_kg': projected,
            'forecast_vs_target_pct': vs_target,
            'on_track': on_track,
            'notes': notes,
            'state': 'published',
        })
        _logger.info('Carbon forecast generated for dept %s: %s kg projected',
                     dept.name, projected)

    @api.model
    def _cron_refresh_forecasts(self):
        """Scheduled action: refresh all published forecasts."""
        forecasts = self.search([('state', '=', 'published')])
        for forecast in forecasts:
            try:
                forecast.action_generate()
            except Exception as e:
                _logger.error('Forecast refresh failed for %s: %s', forecast.name, e)
