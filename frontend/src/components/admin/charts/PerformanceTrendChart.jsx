import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import "./charts.css";

const PerformanceTrendChart = ({ report }) => {
  if (!report?.performance_trend?.length) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Performance Trend</h3>
          <p>No performance data is available for this period.</p>
        </div>
        <div className="chart-empty">No performance records found.</div>
      </div>
    );
  }

  const data = report.performance_trend.map((item) => ({
    date: item.date,
    score: Number(item.average_score || 0),
    percentage: Number(item.average_percentage || 0),
    accuracy: Number(item.average_accuracy || 0),
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Performance Trend</h3>
        <p>Average score, percentage and accuracy over time.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={340}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="date" />

            <YAxis domain={[0, 100]} />

            <Tooltip />

            <Legend />

            <Line
              type="monotone"
              dataKey="percentage"
              name="Percentage (%)"
              stroke="#2563eb"
              strokeWidth={2}
            />

            <Line
              type="monotone"
              dataKey="accuracy"
              name="Accuracy (%)"
              stroke="#16a34a"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default PerformanceTrendChart;
