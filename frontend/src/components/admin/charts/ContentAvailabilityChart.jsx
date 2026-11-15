import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
import "./charts.css";

const ContentAvailabilityChart = ({ report }) => {
  if (!report?.availability_by_exam?.length) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Published Content by Exam</h3>
          <p>Published study materials and previous-year papers.</p>
        </div>
        <div className="chart-empty">No content availability data available.</div>
      </div>
    );
  }

  const data = report.availability_by_exam.map((item) => ({
    exam: item.exam_name,
    materials: item.study_materials?.published ?? 0,
    papers: item.previous_year_papers?.published ?? 0,
  }));

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Published Content by Exam</h3>
        <p>Published study materials and previous-year papers.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={340}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="exam" />

            <YAxis />

            <Tooltip />

            <Legend />

            <Bar
              dataKey="materials"
              name="Study Materials"
              fill="#2563eb"
            />

            <Bar
              dataKey="papers"
              name="Previous Year Papers"
              fill="#16a34a"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ContentAvailabilityChart;
