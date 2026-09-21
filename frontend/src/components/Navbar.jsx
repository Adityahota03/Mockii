import { useState } from "react";
import { Link } from "react-router-dom";

function Navbar() {
    const [menuOpen, setMenuOpen] = useState(false);

    const closeMenu = () => {
        setMenuOpen(false);
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
                            Your Preparation Partner
                        </div>
                    </div>
                </Link>

                {/* Desktop Navigation */}
                <div className="navbar-links">
                    <a href="#exams">Exams</a>
                    <a href="#features">Features</a>
                    <a href="#mock-tests">Mock Tests</a>
                    <Link to="/study-materials">Study Material</Link>
                    <a href="#faq">FAQ</a>
                </div>

                {/* Desktop Buttons */}
                <div className="navbar-actions">
                    <Link to="/login" className="login-button">
                        Login
                    </Link>

                    <Link to="/register" className="register-button">
                        Get Started
                    </Link>
                </div>

                {/* Mobile Menu Button */}
                <button
                    className="mobile-menu-button"
                    onClick={() => setMenuOpen(!menuOpen)}
                    aria-label="Toggle navigation"
                >
                    <span></span>
                    <span></span>
                    <span></span>
                </button>
            </div>

            {/* Mobile Navigation */}
            <div className={`mobile-menu ${menuOpen ? "open" : ""}`}>

                <a href="#exams" onClick={closeMenu}>
                    Exams
                </a>

                <a href="#features" onClick={closeMenu}>
                    Features
                </a>

                <a href="#mock-tests" onClick={closeMenu}>
                    Mock Tests
                </a>

                <Link to="/study-materials" onClick={closeMenu}>
                    Study Material
                </Link>

                <a href="#faq" onClick={closeMenu}>
                    FAQ
                </a>

                <div className="mobile-menu-actions">
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
                </div>
            </div>
        </nav>
    );
}

export default Navbar;