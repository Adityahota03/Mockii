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
  "#16a34a",
  "#f59e0b",
  "#ef4444",
];

const AttemptStatusChart = ({ report }) => {
  const completed = report?.summary?.completed_attempts || 0;
  const inProgress = report?.summary?.in_progress_attempts || 0;
  const expired = report?.summary?.expired_attempts || 0;
  const total = completed + inProgress + expired;

  if (!report?.summary || total === 0) {
    return (
      <div className="chart-card">
        <div className="chart-header">
          <h3>Attempt Status</h3>
          <p>No attempt data is available for this period.</p>
        </div>
        <div className="chart-empty">No attempts recorded in this time range.</div>
      </div>
    );
  }

  const data = [
    {
      name: "Completed",
      value: completed,
    },
    {
      name: "In Progress",
      value: inProgress,
    },
    {
      name: "Expired",
      value: expired,
    },
  ];

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>Attempt Status</h3>
        <p>Distribution of student test attempts.</p>
      </div>

      <div className="chart-container">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
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

export default AttemptStatusChart;
