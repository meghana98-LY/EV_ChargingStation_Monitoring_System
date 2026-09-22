"""
Flask application for EV Charging Station Monitoring Dashboard.
Provides REST API and web interface for monitoring.
"""
from flask import Flask, render_template, jsonify, request
from datetime import datetime
import csv
import os
from config import Config
from logger import get_logger
from monitor import get_monitor
from sensor import get_sensor
from email_alert import get_email_system

logger = get_logger('flask_app')


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config['JSON_SORT_KEYS'] = False
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Initialize monitoring service
    monitor = get_monitor()
    if not monitor.running:
        monitor.start()
        logger.info("Monitoring service started by Flask app")
    
    # Routes
    
    @app.route('/', methods=['GET'])
    def index():
        """Serve main dashboard."""
        return render_template('index.html')
    
    @app.route('/graph', methods=['GET'])
    def graph():
        """Serve graph page."""
        return render_template('graph.html')
    
    @app.route('/api/latest', methods=['GET'])
    def api_latest():
        """
        Get latest sensor and analysis state.
        
        Returns JSON with current readings and status
        """
        try:
            state = monitor.get_latest_state()
            return jsonify({
                'status': 'ok',
                'data': state,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"API error in /latest: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/status', methods=['GET'])
    def api_status():
        """
        Get detailed system status.
        
        Returns JSON with monitoring, cache, and email status
        """
        try:
            status = monitor.get_status()
            return jsonify({
                'status': 'ok',
                'monitoring_service': {
                    'running': status['running'],
                    'sampling_interval': status['sampling_interval']
                },
                'latest_state': status['latest_state'],
                'cache': status['cache_status'],
                'email': status['email_cooldown'],
                'early_warning': status['early_warning'],
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"API error in /status: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/history', methods=['GET'])
    def api_history():
        """
        Get charging history from log file.
        
        Query parameters:
            limit: Maximum number of records to return (default: 100)
            offset: Number of records to skip (default: 0)
        
        Returns JSON with historical readings
        """
        try:
            limit = int(request.args.get('limit', 100))
            offset = int(request.args.get('offset', 0))
            
            limit = min(limit, 1000)  # Cap at 1000
            
            if not os.path.exists(Config.LOG_FILE):
                return jsonify({
                    'status': 'ok',
                    'data': [],
                    'total': 0,
                    'limit': limit,
                    'offset': offset
                })
            
            readings = []
            with open(Config.LOG_FILE, 'r') as f:
                rows = list(csv.DictReader(f))
                rows.reverse()  # Newest entries first!
                readings = rows[offset : offset + limit]
            
            return jsonify({
                'status': 'ok',
                'data': readings,
                'total': len(rows),
                'limit': limit,
                'offset': offset,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"API error in /history: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500

    @app.route('/api/test-email', methods=['GET', 'POST'])
    def api_test_email():
        """Send a diagnostic test email."""
        try:
            email_system = get_email_system()
            success, msg = email_system.send_test_email()
            status_code = 200 if success else 400
            return jsonify({
                'status': 'ok' if success else 'error',
                'message': msg,
                'timestamp': datetime.now().isoformat()
            }), status_code
        except Exception as e:
            logger.error(f"API error in /test-email: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @app.route('/api/simulation-mode', methods=['GET', 'POST'])
    def api_simulation_mode():
        """Get or set simulated sensor mode ('stable', 'gradual', 'abrupt', 'fail')."""
        try:
            sensor = get_sensor()
            if request.method == 'POST':
                data = request.get_json(silent=True) or request.form
                mode = data.get('mode', 'stable')
                if hasattr(sensor, 'set_mode'):
                    sensor.set_mode(mode)
                    monitor.early_warning.reset()
                    return jsonify({
                        'status': 'ok',
                        'message': f'Simulation mode changed to "{mode}"',
                        'mode': mode
                    })
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Real MCP3008 sensor active. Cannot set simulation mode.'
                    }), 400
            
            current_mode = getattr(sensor, 'mode', 'N/A')
            return jsonify({
                'status': 'ok',
                'mode': current_mode,
                'sensor_type': Config.SENSOR_TYPE
            })
        except Exception as e:
            logger.error(f"API error in /simulation-mode: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 500

    @app.route('/api/clear-history', methods=['POST'])
    def api_clear_history():
        """Clear the CSV history log file."""
        try:
            if os.path.exists(Config.LOG_FILE):
                with open(Config.LOG_FILE, 'w') as f:
                    f.write('timestamp,voltage,current,power,prediction,anomaly_score,severity,email_alert_sent,data_source\n')
            return jsonify({
                'status': 'ok',
                'message': 'History log cleared successfully'
            })
        except Exception as e:
            logger.error(f"API error in /clear-history: {str(e)}")
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/statistics', methods=['GET'])
    def api_statistics():
        """
        Calculate statistics from historical data.
        
        Returns JSON with aggregated statistics
        """
        try:
            if not os.path.exists(Config.LOG_FILE):
                return jsonify({
                    'status': 'ok',
                    'data': {},
                    'message': 'No data available'
                })
            
            voltages = []
            currents = []
            powers = []
            warnings = 0
            criticals = 0
            last_anomaly = None
            
            with open(Config.LOG_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        v = float(row.get('voltage', 0))
                        c = float(row.get('current', 0))
                        p = float(row.get('power', 0))
                        severity = row.get('severity', 'NORMAL')
                        
                        voltages.append(v)
                        currents.append(c)
                        powers.append(p)
                        
                        if severity == 'WARNING':
                            warnings += 1
                        elif severity == 'CRITICAL':
                            criticals += 1
                        
                        if severity in ['WARNING', 'CRITICAL']:
                            last_anomaly = row.get('timestamp')
                    except (ValueError, KeyError):
                        continue
            
            # Calculate statistics
            stats = {
                'total_readings': len(voltages),
                'voltage': {
                    'avg': sum(voltages) / len(voltages) if voltages else 0,
                    'min': min(voltages) if voltages else 0,
                    'max': max(voltages) if voltages else 0,
                    'unit': 'V'
                },
                'current': {
                    'avg': sum(currents) / len(currents) if currents else 0,
                    'min': min(currents) if currents else 0,
                    'max': max(currents) if currents else 0,
                    'unit': 'A'
                },
                'power': {
                    'avg': sum(powers) / len(powers) if powers else 0,
                    'min': min(powers) if powers else 0,
                    'max': max(powers) if powers else 0,
                    'unit': 'W'
                },
                'alerts': {
                    'warnings': warnings,
                    'criticals': criticals,
                    'last_anomaly': last_anomaly
                }
            }
            
            return jsonify({
                'status': 'ok',
                'data': stats,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"API error in /statistics: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/cache', methods=['GET'])
    def api_cache():
        """Get cache status."""
        try:
            cache = monitor.cache_manager.get_cache_status()
            return jsonify({
                'status': 'ok',
                'cache': cache,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"API error in /cache: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.route('/api/config', methods=['GET'])
    def api_config():
        """Get public configuration (no secrets)."""
        try:
            config_data = {
                'sensor_type': Config.SENSOR_TYPE,
                'sampling_interval': Config.get_sampling_interval(),
                'simulated_sampling_interval': Config.SIMULATED_SAMPLING_INTERVAL,
                'real_sampling_interval': Config.REAL_SAMPLING_INTERVAL,
                'anomaly_threshold': Config.ANOMALY_THRESHOLD,
                'warning_threshold': Config.WARNING_THRESHOLD,
                'critical_threshold': Config.CRITICAL_THRESHOLD,
                'consecutive_anomalies_warning': Config.CONSECUTIVE_ANOMALIES_FOR_WARNING,
                'consecutive_anomalies_critical': Config.CONSECUTIVE_ANOMALIES_FOR_CRITICAL,
                'email_enabled': Config.EMAIL_ALERT_ENABLED,
                'email_cooldown': Config.EMAIL_ALERT_COOLDOWN,
            }
            return jsonify({
                'status': 'ok',
                'data': config_data
            })
        except Exception as e:
            logger.error(f"API error in /config: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e)
            }), 500
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors."""
        return jsonify({
            'status': 'error',
            'error': 'Not found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors."""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'status': 'error',
            'error': 'Internal server error'
        }), 500
    
    return app


if __name__ == '__main__':
    import sys
    
    logger.info("Starting Flask application...")
    app = create_app()
    
    try:
        app.run(
            host=Config.FLASK_HOST,
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG
        )
    except KeyboardInterrupt:
        logger.info("Flask application stopped")
        sys.exit(0)
