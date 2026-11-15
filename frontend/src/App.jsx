import {
    BrowserRouter,
    Routes,
    Route,
    Navigate
} from "react-router-dom";

import "./superadmin.css";

import Login from "./pages/Login";
import Register from "./pages/Register";

import StudentDashboard
    from "./pages/StudentDashboard";

import StudentPerformance
    from "./pages/StudentPerformance";

import AdminDashboard
    from "./pages/AdminDashboard";

import ExamManagement
    from "./pages/ExamManagement";

import MockTestManagement
    from "./pages/MockTestManagement";

import QuestionManagement
    from "./pages/QuestionManagement";

import SectionManagement
    from "./pages/SectionManagement";

import StudyMaterialManagement
    from "./pages/admin/StudyMaterialManagement";

import PreviousYearPaperManagement
    from "./pages/admin/PreviousYearPaperManagement";

import StudentManagement
    from "./pages/admin/StudentManagement";

import StudentDetail
    from "./pages/admin/StudentDetail";

import AdminReports
    from "./pages/admin/AdminReports";



import StudyMaterials
    from "./pages/StudyMaterials";

import StudyMaterialDetails
    from "./pages/StudyMaterialDetails";

import PreviousYearPapers
    from "./pages/PreviousYearPapers";

import SuperAdminDashboard
    from "./pages/SuperAdminDashboard";

import AdminManagement
    from "./pages/superadmin/AdminManagement";

import SuperAdminManagement
    from "./pages/superadmin/SuperAdminManagement";

import UserManagement
    from "./pages/superadmin/UserManagement";

import RolesPermissions
    from "./pages/superadmin/RolesPermissions";

import SystemConfig
    from "./pages/superadmin/SystemConfig";

import AuditLogs
    from "./pages/superadmin/AuditLogs";

import SecurityMonitoring
    from "./pages/superadmin/SecurityMonitoring";

import Statistics
    from "./pages/superadmin/Statistics";

import CriticalControls
    from "./pages/superadmin/CriticalControls";


import Unauthorized
    from "./pages/Unauthorized";


import RoleProtectedRoute
    from "./routes/RoleProtectedRoute";


import StudentLayout
    from "./layouts/StudentLayout";

import AdminLayout
    from "./layouts/AdminLayout";

import SuperAdminLayout
    from "./layouts/SuperAdminLayout";

import StudentProfile
    from "./pages/StudentProfile";

import ChangePassword
    from "./pages/ChangePassword";

import StudentSettings
    from "./pages/StudentSettings";

import Home from "./pages/Home";
import MockTest from "./pages/MockTest";
import TestInstructions from "./pages/TestInstructions";
import TestResult from "./pages/TestResult";
import Exams from "./pages/Exams";
import ExamDetails from "./pages/ExamDetails";
import MockTests from "./pages/MockTests";
import TestHistory from "./pages/TestHistory";
import Search from "./pages/Search";
import Notifications from "./pages/Notifications";

function App() {

    return (

        <BrowserRouter>

            <Routes>



            <Route
                path="/"
                element={<Home />}
            />

            <Route
                path="/study-materials"
                element={<StudyMaterials />}
            />

            <Route
                path="/study-materials/:materialId"
                element={<StudyMaterialDetails />}
            />

            <Route
                path="/previous-year-papers"
                element={<PreviousYearPapers />}
            />

            <Route
                path="/previous-papers"
                element={<PreviousYearPapers />}
            />

            <Route
                path="/exams"
                element={<Exams />}
            />

            <Route
                path="/exams/:examId"
                element={<ExamDetails />}
            />

            <Route
                path="/mock-tests"
                element={<MockTests />}
            />

            <Route
                path="/search"
                element={<Search />}
            />

                {/* Authentication */}

                <Route
                    path="/login"
                    element={<Login />}
                />

                <Route
                    path="/register"
                    element={<Register />}
                />


                {/* Unauthorized */}

                <Route
                    path="/unauthorized"
                    element={<Unauthorized />}
                />


                {/* Student */}

                <Route
                    path="/student/profile"
                    element={

                        <RoleProtectedRoute
                            allowedRoles={[
                                "STUDENT"
                            ]}
                        >

                            <StudentLayout>

                                <StudentProfile />

                            </StudentLayout>

                        </RoleProtectedRoute>

                    }
                />

                {/* Change Password */}

                <Route
                    path="/student/change-password"
                    element={

                        <RoleProtectedRoute
                            allowedRoles={[
                                "STUDENT"
                            ]}
                        >

                            <StudentLayout>

                                <ChangePassword />

                            </StudentLayout>

                        </RoleProtectedRoute>

                    }
                />

                {/* Settings */}

                <Route
                    path="/student/settings"
                    element={

                        <RoleProtectedRoute
                            allowedRoles={[
                                "STUDENT"
                            ]}
                        >

                            <StudentLayout>

                                <StudentSettings />

                            </StudentLayout>

                        </RoleProtectedRoute>

                    }
                />

                <Route
                    path="/student/dashboard"
                    element={

                        <RoleProtectedRoute
                            allowedRoles={[
                                "STUDENT"
                            ]}
                        >

                            <StudentLayout>

                                <StudentDashboard />

                            </StudentLayout>

                        </RoleProtectedRoute>

                    }
                />

                <Route
                    path="/student/performance"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={["STUDENT"]}
                        >
                            <StudentLayout>
                                <StudentPerformance />
                            </StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/study-materials"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><StudyMaterials /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/study-materials/:materialId"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><StudyMaterialDetails /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/previous-year-papers"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><PreviousYearPapers /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/previous-papers"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><PreviousYearPapers /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/exams"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><Exams /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/exams/:examId"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><ExamDetails /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/mock-tests"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><MockTests /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/history"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><TestHistory /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/attempts"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><TestHistory /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/search"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><Search /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/student/notifications"
                    element={
                        <RoleProtectedRoute allowedRoles={["STUDENT"]}>
                            <StudentLayout><Notifications /></StudentLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/test/instructions/:mockTestId"
                    element={<TestInstructions />}
                />

                <Route
                    path="/student/instructions/:mockTestId"
                    element={<TestInstructions />}
                />

                <Route
                    path="/test/:attemptId"
                    element={<MockTest />}
                />

                <Route
                    path="/student/mock-test/:attemptId"
                    element={<MockTest />}
                />

                <Route
                    path="/mock-test/:attemptId"
                    element={<MockTest />}
                />

                <Route
                    path="/test/:attemptId/result"
                    element={<TestResult />}
                />

                <Route
                    path="/student/test-result/:attemptId"
                    element={<TestResult />}
                />

                <Route
                    path="/test-result/:attemptId"
                    element={<TestResult />}
                />


                {/* Admin */}

                <Route
                    path="/admin"
                    element={<Navigate to="/admin/dashboard" replace />}
                />

                <Route
                    path="/admin/dashboard"
                    element={

                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >

                            <AdminLayout>

                                <AdminDashboard />

                            </AdminLayout>

                        </RoleProtectedRoute>

                    }
                />

                <Route
                    path="/admin/exams"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <ExamManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/mock-tests"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <MockTestManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/mock-tests/:mockTestId/questions"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <QuestionManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/questions"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <QuestionManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/sections"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <SectionManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/mock-tests/:mockTestId/sections"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <SectionManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/study-materials"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <StudyMaterialManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/previous-year-papers"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <PreviousYearPaperManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/previous-papers"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <PreviousYearPaperManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/students"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <StudentManagement />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/students/:studentId"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <StudentDetail />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/admin/reports"
                    element={
                        <RoleProtectedRoute
                            allowedRoles={[
                                "ADMIN",
                                "SUPER_ADMIN"
                            ]}
                        >
                            <AdminLayout>
                                <AdminReports />
                            </AdminLayout>
                        </RoleProtectedRoute>
                    }
                />




                {/* Super Admin */}

                <Route
                    path="/super-admin/dashboard"
                    element={

                        <RoleProtectedRoute
                            allowedRoles={[
                                "SUPER_ADMIN"
                            ]}
                        >

                            <SuperAdminLayout>

                                <SuperAdminDashboard />

                            </SuperAdminLayout>

                        </RoleProtectedRoute>

                    }
                />

                <Route
                    path="/super-admin/admins"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <AdminManagement />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/superadmins"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <SuperAdminManagement />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/users"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <UserManagement />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/roles"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <RolesPermissions />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/system-config"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <SystemConfig />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/audit-logs"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <AuditLogs />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/security"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <SecurityMonitoring />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/statistics"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <Statistics />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />

                <Route
                    path="/super-admin/critical-controls"
                    element={
                        <RoleProtectedRoute allowedRoles={["SUPER_ADMIN"]}>
                            <SuperAdminLayout>
                                <CriticalControls />
                            </SuperAdminLayout>
                        </RoleProtectedRoute>
                    }
                />



                <Route
                    path="*"
                    element={
                        <Login />
                    }
                />

            </Routes>

        </BrowserRouter>
    );
}


export default App;
