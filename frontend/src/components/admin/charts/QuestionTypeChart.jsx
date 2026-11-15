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

const QuestionTypeChart = ({ report }) => {
  if (!report?.type_distribution?.length) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Question Type Distribution</h3>
          <p>Questions grouped by question type.</p>
        </div>
        <div className="chart-empty">No question type data available.</div>
      </div>
    );
  }

  const data = report.type_distribution.map((item) => ({
    type: item.question_type,
    total: item.total,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Question Type Distribution</h3>
        <p>Questions grouped by question type.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="type" />

            <YAxis />

            <Tooltip />

            <Bar
              dataKey="total"
              name="Questions"
              fill="#7c3aed"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default QuestionTypeChart;
