import {
    BrowserRouter,
    Routes,
    Route
} from "react-router-dom";


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


import StudyMaterials
    from "./pages/StudyMaterials";

import StudyMaterialDetails
    from "./pages/StudyMaterialDetails";

import PreviousYearPapers
    from "./pages/PreviousYearPapers";

import SuperAdminDashboard
    from "./pages/SuperAdminDashboard";

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
                    path="/test/instructions/:mockTestId"
                    element={<TestInstructions />}
                />

                <Route
                    path="/test/:attemptId"
                    element={<MockTest />}
                />

                <Route
                    path="/test/:attemptId/result"
                    element={<TestResult />}
                />


                {/* Admin */}

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


                {/* Default */}

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
