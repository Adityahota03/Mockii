import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import "./charts.css";

const COLORS = [
  "#2563eb",
  "#ef4444",
];

const StudentStatusChart = ({ report }) => {
  const active = report?.summary?.active_students || 0;
  const inactive = report?.summary?.inactive_students || 0;
  const total = active + inactive;

  if (!report || total === 0) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Student Account Status</h3>
          <p>No student account data is available.</p>
        </div>
        <div className="chart-empty">No student records found.</div>
      </div>
    );
  }

  const data = [
    {
      name: "Active",
      value: active,
    },
    {
      name: "Inactive",
      value: inactive,
    },
  ];

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Student Account Status</h3>
        <p>Active and inactive student accounts.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              outerRadius={100}
              label
            >
              {data.map((entry, index) => (
                <Cell
                  key={entry.name}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>

            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default StudentStatusChart;
