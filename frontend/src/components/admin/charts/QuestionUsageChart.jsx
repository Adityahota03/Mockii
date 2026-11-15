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

const QuestionUsageChart = ({ report }) => {
  const filteredUsage =
    report?.usage?.filter((item) => item.usage_count > 0) || [];

  if (!filteredUsage.length) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Most Used Questions</h3>
          <p>Top questions by mock-test usage.</p>
        </div>
        <div className="chart-empty">No question usage data available.</div>
      </div>
    );
  }

  const data = filteredUsage.slice(0, 10).map((item) => ({
    question: `Q${item.id}`,
    usage: item.usage_count,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Most Used Questions</h3>
        <p>Top questions by mock-test usage.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={data}
            layout="vertical"
          >
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis type="number" />

            <YAxis
              type="category"
              dataKey="question"
            />

            <Tooltip />

            <Bar
              dataKey="usage"
              name="Usage"
              fill="#ea580c"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default QuestionUsageChart;
