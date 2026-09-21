import { Link } from "react-router-dom";

function Footer() {

    return (

        <footer className="public-footer">

            <div className="footer-container">

                {/* Brand */}

                <div className="footer-brand">

                    <div className="brand-logo footer-logo">

                        <div className="brand-icon">
                            M
                        </div>

                        <div>

                            <div className="brand-name">
                                Mockii
                            </div>

                            <div className="brand-tagline">
                                Your Preparation Partner
                            </div>

                        </div>

                    </div>


                    <p>
                        A complete preparation platform
                        for competitive examinations.
                    </p>

                </div>


                {/* Exams */}

                <div className="footer-column">

                    <h3>
                        Exams
                    </h3>

                    <a href="#exams">
                        SSC
                    </a>

                    <a href="#exams">
                        Banking
                    </a>

                    <a href="#exams">
                        Railway
                    </a>

                    <a href="#exams">
                        State Exams
                    </a>

                </div>


                {/* Platform */}

                <div className="footer-column">

                    <h3>
                        Platform
                    </h3>

                    <a href="#mock-tests">
                        Mock Tests
                    </a>

                    <a href="#study-material">
                        Study Material
                    </a>

                    <a href="#previous-papers">
                        Previous Year Papers
                    </a>

                    <a href="#features">
                        Performance
                    </a>

                </div>


                {/* Company */}

                <div className="footer-column">

                    <h3>
                        Company
                    </h3>

                    <a href="#why-mockii">
                        About Mockii
                    </a>

                    <a href="#contact">
                        Contact
                    </a>

                    <a href="#faq">
                        FAQ
                    </a>

                    <Link to="/login">
                        Login
                    </Link>

                </div>

            </div>


            <div className="footer-bottom">

                <p>
                    © 2026 Mockii. All rights reserved.
                </p>

                <div>

                    <a href="#privacy">
                        Privacy Policy
                    </a>

                    <a href="#terms">
                        Terms & Conditions
                    </a>

                </div>

            </div>

        </footer>
    );
}

export default Footer;