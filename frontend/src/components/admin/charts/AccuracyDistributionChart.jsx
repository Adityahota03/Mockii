import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";
import "./charts.css";

const AccuracyDistributionChart = ({ report }) => {
  const totalCount =
    report?.accuracy_distribution?.reduce(
      (sum, item) => sum + (item.count || 0),
      0
    ) || 0;

  if (!report?.accuracy_distribution?.length || totalCount === 0) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Accuracy Distribution</h3>
          <p>Attempts grouped by accuracy range.</p>
        </div>
        <div className="chart-empty">No accuracy distribution data available.</div>
      </div>
    );
  }

  const data = report.accuracy_distribution.map((item) => ({
    range: item.range,
    count: item.count,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Accuracy Distribution</h3>
        <p>Attempts grouped by accuracy range.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="range" />

            <YAxis />

            <Tooltip />

            <Bar
              dataKey="count"
              name="Attempts"
              fill="#16a34a"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default AccuracyDistributionChart;
