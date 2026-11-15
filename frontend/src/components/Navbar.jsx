import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Navbar() {
    const [menuOpen, setMenuOpen] = useState(false);
    const { user } = useAuth();

    const closeMenu = () => {
        setMenuOpen(false);
    };

    const getDashboardPath = () => {
        if (!user) return "/login";
        if (user.role === "SUPER_ADMIN") return "/superadmin/dashboard";
        if (user.role === "ADMIN") return "/admin/dashboard";
        return "/student/dashboard";
    };

    return (
        <nav className="public-navbar">
            <div className="navbar-container">

                {/* Logo */}
                <Link to="/" className="brand-logo" onClick={closeMenu}>
                    <div className="brand-icon">M</div>

                    <div className="brand-text">
                        <div className="brand-name">Mockii</div>
                        <div className="brand-tagline">
                            Spatial Exam Preparation
                        </div>
                    </div>
                </Link>

                {/* Desktop Navigation */}
                <div className="navbar-links">
                    <Link to="/exams">Exams</Link>
                    <Link to="/mock-tests">Mock Tests</Link>
                    <Link to="/study-materials">Study Materials</Link>
                    <Link to="/previous-papers">Previous Papers</Link>
                    <a href="/#faq">FAQ</a>
                </div>

                {/* Desktop Buttons */}
                <div className="navbar-actions">
                    {user ? (
                        <Link to={getDashboardPath()} className="register-button">
                            Dashboard →
                        </Link>
                    ) : (
                        <>
                            <Link to="/login" className="login-button">
                                Login
                            </Link>

                            <Link to="/register" className="register-button">
                                Get Started
                            </Link>
                        </>
                    )}
                </div>

                {/* Mobile Menu Button */}
                <button
                    className={`mobile-menu-button${menuOpen ? " is-open" : ""}`}
                    onClick={() => setMenuOpen(!menuOpen)}
                    aria-label="Toggle navigation"
                    aria-expanded={menuOpen}
                    aria-controls="public-navigation"
                >
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>

            {/* Mobile Navigation */}
            <div
                id="public-navigation"
                className={`mobile-menu ${menuOpen ? "open" : ""}`}
            >
                <Link to="/exams" onClick={closeMenu}>
                    Exams
                </Link>

                <Link to="/mock-tests" onClick={closeMenu}>
                    Mock Tests
                </Link>

                <Link to="/study-materials" onClick={closeMenu}>
                    Study Materials
                </Link>

                <Link to="/previous-papers" onClick={closeMenu}>
                    Previous Papers
                </Link>

                <a href="/#faq" onClick={closeMenu}>
                    FAQ
                </a>

                <div className="mobile-menu-actions">
                    {user ? (
                        <Link
                            to={getDashboardPath()}
                            className="register-button"
                            onClick={closeMenu}
                            style={{ width: "100%", textAlign: "center" }}
                        >
                            Go to Dashboard →
                        </Link>
                    ) : (
                        <>
                            <Link
                                to="/login"
                                className="login-button"
                                onClick={closeMenu}
                            >
                                Login
                            </Link>

                            <Link
                                to="/register"
                                className="register-button"
                                onClick={closeMenu}
                            >
                                Get Started
                            </Link>
                        </>
                    )}
                </div>
            </div>
        </nav>
    );
}

export default Navbar;
