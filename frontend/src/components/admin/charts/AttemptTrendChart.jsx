import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import "./charts.css";

const AttemptTrendChart = ({ report }) => {
  if (!report?.attempt_trend?.length) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Attempt Trend</h3>
          <p>No attempt data is available for this period.</p>
        </div>
        <div className="chart-empty">No trend data available for this period.</div>
      </div>
    );
  }

  const data = report.attempt_trend.map((item) => ({
    date: item.date,
    attempts: item.attempts,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Attempt Trend</h3>
        <p>Number of mock-test attempts over time.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="date" />

            <YAxis />

            <Tooltip />

            <Line
              type="monotone"
              dataKey="attempts"
              name="Attempts"
              stroke="#2563eb"
              strokeWidth={2}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AttemptTrendChart;
