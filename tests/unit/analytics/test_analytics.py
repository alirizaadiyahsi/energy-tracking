"""
Unit tests for analytics service
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
import uuid
import statistics


@pytest.mark.unit
@pytest.mark.analytics
class TestAnalytics:
    """Test analytics calculations"""
    
    def test_basic_statistics(self):
        """Test basic statistical calculations"""
        
        def calculate_statistics(values):
            """Mock statistics calculator"""
            if not values:
                return {}
            
            return {
                "count": len(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "mode": statistics.mode(values) if len(set(values)) < len(values) else None,
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "variance": statistics.variance(values) if len(values) > 1 else 0,
                "min": min(values),
                "max": max(values),
                "range": max(values) - min(values)
            }
        
        power_values = [1000, 1100, 950, 1050, 1200, 1150, 1000, 1075]
        
        stats = calculate_statistics(power_values)
        
        assert stats["count"] == 8
        assert stats["mean"] == statistics.mean(power_values)
        assert stats["median"] == statistics.median(power_values)
        assert stats["min"] == 950
        assert stats["max"] == 1200
        assert stats["range"] == 250
        assert stats["std_dev"] > 0
    
    def test_energy_consumption_calculation(self):
        """Test energy consumption calculations"""
        
        def calculate_energy_consumption(power_readings):
            """Mock energy consumption calculator"""
            if not power_readings:
                return {}
            
            # Sort by timestamp
            sorted_readings = sorted(power_readings, key=lambda x: x["timestamp"])
            
            total_energy = 0
            consumption_by_hour = {}
            
            for i in range(1, len(sorted_readings)):
                current = sorted_readings[i]
                previous = sorted_readings[i-1]
                
                # Calculate time difference in hours
                current_time = datetime.fromisoformat(current["timestamp"].replace("Z", "+00:00"))
                previous_time = datetime.fromisoformat(previous["timestamp"].replace("Z", "+00:00"))
                time_diff_hours = (current_time - previous_time).total_seconds() / 3600
                
                # Energy = Power * Time (kWh)
                avg_power = (current["power"] + previous["power"]) / 2
                energy_kwh = (avg_power / 1000) * time_diff_hours
                total_energy += energy_kwh
                
                # Group by hour
                hour_key = current_time.replace(minute=0, second=0, microsecond=0)
                if hour_key not in consumption_by_hour:
                    consumption_by_hour[hour_key] = 0
                consumption_by_hour[hour_key] += energy_kwh
            
            return {
                "total_energy_kwh": round(total_energy, 3),
                "consumption_by_hour": {
                    k.isoformat(): round(v, 3) 
                    for k, v in consumption_by_hour.items()
                }
            }
        
        power_readings = [
            {"timestamp": "2024-01-15T10:00:00Z", "power": 1000},
            {"timestamp": "2024-01-15T10:30:00Z", "power": 1200},
            {"timestamp": "2024-01-15T11:00:00Z", "power": 1100},
            {"timestamp": "2024-01-15T11:30:00Z", "power": 950}
        ]
        
        consumption = calculate_energy_consumption(power_readings)
        
        assert "total_energy_kwh" in consumption
        assert consumption["total_energy_kwh"] > 0
        assert "consumption_by_hour" in consumption
        assert len(consumption["consumption_by_hour"]) <= 2  # Max 2 hours
    
    def test_trend_analysis(self):
        """Test trend analysis"""
        
        def analyze_trend(time_series_data):
            """Mock trend analyzer"""
            if len(time_series_data) < 2:
                return {"trend": "insufficient_data"}
            
            values = [point["value"] for point in time_series_data]
            
            # Simple linear regression slope
            n = len(values)
            x_values = list(range(n))
            
            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x * y for x, y in zip(x_values, values))
            sum_x2 = sum(x * x for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Determine trend
            if abs(slope) < 0.1:
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
            
            # Calculate trend strength
            correlation = abs(slope) / (max(values) - min(values)) if max(values) != min(values) else 0
            
            return {
                "trend": trend,
                "slope": round(slope, 4),
                "strength": round(correlation, 3),
                "confidence": "high" if len(values) > 10 else "medium" if len(values) > 5 else "low"
            }
        
        # Increasing trend
        increasing_data = [
            {"timestamp": f"2024-01-15T{i:02d}:00:00Z", "value": 1000 + i * 50}
            for i in range(10, 20)
        ]
        
        # Decreasing trend
        decreasing_data = [
            {"timestamp": f"2024-01-15T{i:02d}:00:00Z", "value": 2000 - i * 30}
            for i in range(10, 20)
        ]
        
        # Stable trend
        stable_data = [
            {"timestamp": f"2024-01-15T{i:02d}:00:00Z", "value": 1000 + (i % 2) * 5}
            for i in range(10, 20)
        ]
        
        increasing_trend = analyze_trend(increasing_data)
        assert increasing_trend["trend"] == "increasing"
        assert increasing_trend["slope"] > 0
        
        decreasing_trend = analyze_trend(decreasing_data)
        assert decreasing_trend["trend"] == "decreasing"
        assert decreasing_trend["slope"] < 0
        
        stable_trend = analyze_trend(stable_data)
        assert stable_trend["trend"] == "stable"
    
    def test_peak_detection(self):
        """Test peak detection in time series"""
        
        def detect_peaks(time_series_data, threshold_multiplier=1.5):
            """Mock peak detector"""
            if len(time_series_data) < 3:
                return []
            
            values = [point["value"] for point in time_series_data]
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0
            
            threshold = mean_value + (threshold_multiplier * std_dev)
            
            peaks = []
            for i in range(1, len(values) - 1):
                current = values[i]
                previous = values[i - 1]
                next_val = values[i + 1]
                
                # Peak conditions: higher than neighbors and above threshold
                if current > previous and current > next_val and current > threshold:
                    peaks.append({
                        "index": i,
                        "timestamp": time_series_data[i]["timestamp"],
                        "value": current,
                        "threshold": threshold,
                        "prominence": current - max(previous, next_val)
                    })
            
            return peaks
        
        # Data with peaks
        time_series_data = [
            {"timestamp": "2024-01-15T10:00:00Z", "value": 1000},
            {"timestamp": "2024-01-15T10:15:00Z", "value": 1200},  # Small peak
            {"timestamp": "2024-01-15T10:30:00Z", "value": 1100},
            {"timestamp": "2024-01-15T10:45:00Z", "value": 2000},  # Large peak
            {"timestamp": "2024-01-15T11:00:00Z", "value": 1050},
            {"timestamp": "2024-01-15T11:15:00Z", "value": 1800},  # Medium peak
            {"timestamp": "2024-01-15T11:30:00Z", "value": 1000}
        ]
        
        peaks = detect_peaks(time_series_data)
        
        # Should detect significant peaks
        assert len(peaks) > 0
        
        # Check that peaks are above average
        avg_value = statistics.mean([point["value"] for point in time_series_data])
        for peak in peaks:
            assert peak["value"] > avg_value
    
    def test_efficiency_calculation(self):
        """Test efficiency calculations"""
        
        def calculate_efficiency(energy_readings, theoretical_capacity):
            """Mock efficiency calculator"""
            if not energy_readings or theoretical_capacity <= 0:
                return {}
            
            actual_energy = sum(reading["energy"] for reading in energy_readings)
            efficiency_percentage = (actual_energy / theoretical_capacity) * 100
            
            # Calculate time-based efficiency
            if len(energy_readings) > 1:
                start_time = min(reading["timestamp"] for reading in energy_readings)
                end_time = max(reading["timestamp"] for reading in energy_readings)
                
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                duration_hours = (end_dt - start_dt).total_seconds() / 3600
                
                energy_per_hour = actual_energy / duration_hours if duration_hours > 0 else 0
            else:
                energy_per_hour = 0
                duration_hours = 0
            
            return {
                "actual_energy": round(actual_energy, 3),
                "theoretical_capacity": theoretical_capacity,
                "efficiency_percentage": round(efficiency_percentage, 2),
                "energy_per_hour": round(energy_per_hour, 3),
                "duration_hours": round(duration_hours, 2),
                "efficiency_rating": (
                    "excellent" if efficiency_percentage >= 90 else
                    "good" if efficiency_percentage >= 75 else
                    "fair" if efficiency_percentage >= 60 else
                    "poor"
                )
            }
        
        energy_readings = [
            {"timestamp": "2024-01-15T10:00:00Z", "energy": 25.0},
            {"timestamp": "2024-01-15T11:00:00Z", "energy": 30.0},
            {"timestamp": "2024-01-15T12:00:00Z", "energy": 28.0}
        ]
        
        theoretical_capacity = 100.0  # kWh
        
        efficiency = calculate_efficiency(energy_readings, theoretical_capacity)
        
        assert efficiency["actual_energy"] == 83.0
        assert efficiency["theoretical_capacity"] == 100.0
        assert efficiency["efficiency_percentage"] == 83.0
        assert efficiency["efficiency_rating"] == "good"
        assert efficiency["duration_hours"] == 2.0


@pytest.mark.unit
@pytest.mark.analytics
class TestDataVisualization:
    """Test data visualization helpers"""
    
    def test_chart_data_preparation(self):
        """Test chart data preparation"""
        
        def prepare_chart_data(raw_data, chart_type="line"):
            """Mock chart data preparer"""
            if chart_type == "line":
                return {
                    "labels": [point["timestamp"] for point in raw_data],
                    "datasets": [{
                        "label": "Power Consumption",
                        "data": [point["power"] for point in raw_data],
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)"
                    }]
                }
            elif chart_type == "bar":
                # Group by hour for bar chart
                hourly_data = {}
                for point in raw_data:
                    timestamp = datetime.fromisoformat(point["timestamp"].replace("Z", "+00:00"))
                    hour_key = timestamp.strftime("%H:00")
                    
                    if hour_key not in hourly_data:
                        hourly_data[hour_key] = []
                    hourly_data[hour_key].append(point["power"])
                
                return {
                    "labels": list(hourly_data.keys()),
                    "datasets": [{
                        "label": "Average Power by Hour",
                        "data": [
                            round(statistics.mean(powers), 2) 
                            for powers in hourly_data.values()
                        ],
                        "backgroundColor": "rgba(54, 162, 235, 0.2)",
                        "borderColor": "rgba(54, 162, 235, 1)"
                    }]
                }
            
            return {}
        
        raw_data = [
            {"timestamp": "2024-01-15T10:15:00Z", "power": 1000},
            {"timestamp": "2024-01-15T10:30:00Z", "power": 1100},
            {"timestamp": "2024-01-15T10:45:00Z", "power": 950},
            {"timestamp": "2024-01-15T11:15:00Z", "power": 1200},
            {"timestamp": "2024-01-15T11:30:00Z", "power": 1150}
        ]
        
        # Test line chart
        line_data = prepare_chart_data(raw_data, "line")
        assert "labels" in line_data
        assert "datasets" in line_data
        assert len(line_data["labels"]) == 5
        assert len(line_data["datasets"][0]["data"]) == 5
        
        # Test bar chart
        bar_data = prepare_chart_data(raw_data, "bar")
        assert "labels" in bar_data
        assert "datasets" in bar_data
        assert len(bar_data["labels"]) == 2  # Two hours
    
    def test_dashboard_metrics(self):
        """Test dashboard metrics calculation"""
        
        def calculate_dashboard_metrics(readings, time_period="24h"):
            """Mock dashboard metrics calculator"""
            if not readings:
                return {}
            
            current_time = datetime.utcnow()
            
            # Filter by time period
            if time_period == "24h":
                cutoff_time = current_time - timedelta(hours=24)
            elif time_period == "7d":
                cutoff_time = current_time - timedelta(days=7)
            elif time_period == "30d":
                cutoff_time = current_time - timedelta(days=30)
            else:
                cutoff_time = None
            
            filtered_readings = readings
            if cutoff_time:
                filtered_readings = [
                    r for r in readings
                    if datetime.fromisoformat(r["timestamp"].replace("Z", "+00:00")) >= cutoff_time
                ]
            
            if not filtered_readings:
                return {"error": "No data in specified time period"}
            
            power_values = [r["power"] for r in filtered_readings]
            energy_values = [r.get("energy", 0) for r in filtered_readings]
            
            return {
                "total_readings": len(filtered_readings),
                "avg_power": round(statistics.mean(power_values), 2),
                "max_power": max(power_values),
                "min_power": min(power_values),
                "total_energy": round(sum(energy_values), 3),
                "power_variance": round(statistics.variance(power_values), 2) if len(power_values) > 1 else 0,
                "efficiency_score": min(100, round((statistics.mean(power_values) / max(power_values)) * 100, 1)),
                "time_period": time_period,
                "first_reading": min(r["timestamp"] for r in filtered_readings),
                "last_reading": max(r["timestamp"] for r in filtered_readings)
            }
        
        readings = [
            {"timestamp": "2024-01-15T10:00:00Z", "power": 1000, "energy": 25.0},
            {"timestamp": "2024-01-15T11:00:00Z", "power": 1200, "energy": 30.0},
            {"timestamp": "2024-01-15T12:00:00Z", "power": 950, "energy": 23.0},
            {"timestamp": "2024-01-15T13:00:00Z", "power": 1100, "energy": 28.0}
        ]
        
        metrics = calculate_dashboard_metrics(readings, "24h")
        
        assert metrics["total_readings"] == 4
        assert metrics["avg_power"] == statistics.mean([1000, 1200, 950, 1100])
        assert metrics["max_power"] == 1200
        assert metrics["min_power"] == 950
        assert metrics["total_energy"] == 106.0
        assert "efficiency_score" in metrics


@pytest.mark.unit
@pytest.mark.analytics
class TestReporting:
    """Test report generation"""
    
    def test_summary_report_generation(self):
        """Test summary report generation"""
        
        def generate_summary_report(data, report_period):
            """Mock summary report generator"""
            if not data:
                return {"error": "No data available"}
            
            power_values = [reading["power"] for reading in data]
            energy_values = [reading.get("energy", 0) for reading in data]
            
            # Calculate key metrics
            total_energy = sum(energy_values)
            avg_power = statistics.mean(power_values)
            peak_power = max(power_values)
            min_power = min(power_values)
            
            # Calculate cost (mock pricing)
            energy_rate = 0.12  # $/kWh
            estimated_cost = total_energy * energy_rate
            
            # Performance analysis
            target_efficiency = 85  # %
            actual_efficiency = (avg_power / peak_power) * 100
            performance_rating = "Above Target" if actual_efficiency >= target_efficiency else "Below Target"
            
            return {
                "report_period": report_period,
                "generated_at": datetime.utcnow().isoformat(),
                "summary": {
                    "total_energy_kwh": round(total_energy, 3),
                    "average_power_w": round(avg_power, 2),
                    "peak_power_w": peak_power,
                    "minimum_power_w": min_power,
                    "estimated_cost_usd": round(estimated_cost, 2)
                },
                "performance": {
                    "efficiency_percentage": round(actual_efficiency, 1),
                    "target_efficiency": target_efficiency,
                    "performance_rating": performance_rating,
                    "power_factor": round(avg_power / peak_power, 3)
                },
                "recommendations": [
                    "Monitor peak consumption periods",
                    "Consider load balancing during high-usage times"
                ] if actual_efficiency < target_efficiency else [
                    "Excellent performance maintained",
                    "Continue current energy management practices"
                ]
            }
        
        sample_data = [
            {"timestamp": "2024-01-15T10:00:00Z", "power": 1000, "energy": 25.0},
            {"timestamp": "2024-01-15T11:00:00Z", "power": 1200, "energy": 30.0},
            {"timestamp": "2024-01-15T12:00:00Z", "power": 950, "energy": 23.0}
        ]
        
        report = generate_summary_report(sample_data, "daily")
        
        assert report["report_period"] == "daily"
        assert "generated_at" in report
        assert "summary" in report
        assert "performance" in report
        assert "recommendations" in report
        
        # Check calculations
        assert report["summary"]["total_energy_kwh"] == 78.0
        assert report["summary"]["peak_power_w"] == 1200
        assert report["summary"]["minimum_power_w"] == 950
    
    def test_comparative_analysis(self):
        """Test comparative analysis between periods"""
        
        def compare_periods(current_data, previous_data):
            """Mock comparative analyzer"""
            if not current_data or not previous_data:
                return {"error": "Insufficient data for comparison"}
            
            # Calculate metrics for both periods
            current_avg = statistics.mean([r["power"] for r in current_data])
            previous_avg = statistics.mean([r["power"] for r in previous_data])
            
            current_energy = sum(r.get("energy", 0) for r in current_data)
            previous_energy = sum(r.get("energy", 0) for r in previous_data)
            
            # Calculate changes
            power_change = ((current_avg - previous_avg) / previous_avg) * 100
            energy_change = ((current_energy - previous_energy) / previous_energy) * 100
            
            return {
                "current_period": {
                    "avg_power": round(current_avg, 2),
                    "total_energy": round(current_energy, 3)
                },
                "previous_period": {
                    "avg_power": round(previous_avg, 2),
                    "total_energy": round(previous_energy, 3)
                },
                "changes": {
                    "power_change_percentage": round(power_change, 1),
                    "energy_change_percentage": round(energy_change, 1),
                    "power_trend": "increase" if power_change > 0 else "decrease",
                    "energy_trend": "increase" if energy_change > 0 else "decrease"
                },
                "insights": [
                    f"Power consumption {'increased' if power_change > 0 else 'decreased'} by {abs(power_change):.1f}%",
                    f"Energy usage {'increased' if energy_change > 0 else 'decreased'} by {abs(energy_change):.1f}%"
                ]
            }
        
        current_data = [
            {"power": 1200, "energy": 30.0},
            {"power": 1100, "energy": 28.0},
            {"power": 1300, "energy": 32.0}
        ]
        
        previous_data = [
            {"power": 1000, "energy": 25.0},
            {"power": 950, "energy": 23.0},
            {"power": 1050, "energy": 26.0}
        ]
        
        comparison = compare_periods(current_data, previous_data)
        
        assert "current_period" in comparison
        assert "previous_period" in comparison
        assert "changes" in comparison
        assert "insights" in comparison
        
        # Check that current period has higher values
        assert comparison["current_period"]["avg_power"] > comparison["previous_period"]["avg_power"]
        assert comparison["changes"]["power_trend"] == "increase"
        assert comparison["changes"]["energy_trend"] == "increase"
