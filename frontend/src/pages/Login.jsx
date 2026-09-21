import { useState } from "react";
import {
    Link,
    useNavigate
} from "react-router-dom";

import { useAuth } from "../context/AuthContext";


function Login() {

    const navigate = useNavigate();

    const { login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);


    const handleSubmit = async (e) => {

    e.preventDefault();

    setError("");
    setLoading(true);

    try {

        const user =
            await login(
                email,
                password
            );


        if (user.role === "STUDENT") {

            navigate(
                "/student/dashboard"
            );

        } else if (
            user.role === "ADMIN"
        ) {

            navigate(
                "/admin/dashboard"
            );

        } else if (
            user.role === "SUPER_ADMIN"
        ) {

            navigate(
                "/super-admin/dashboard"
            );

        } else {

            setError(
                "Unknown user role."
            );

        }

    } catch (error) {

        if (
            error.response?.status === 401
        ) {

            setError(
                "Invalid email or password."
            );

        } else {

            setError(
                "Unable to connect to server."
            );

        }

    } finally {

        setLoading(false);

    }
};


    return (

        <div className="auth-page">

            <div className="auth-card">

                <h1>Mockii</h1>

                <h2>Welcome Back</h2>

                <p>
                    Login to continue your
                    preparation.
                </p>


                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}


                <form
                    onSubmit={handleSubmit}
                >

                    <div className="form-group">

                        <label>
                            Email Address
                        </label>

                        <input
                            type="email"
                            value={email}
                            onChange={(e) =>
                                setEmail(
                                    e.target.value
                                )
                            }
                            placeholder="Enter your email"
                            required
                        />

                    </div>


                    <div className="form-group">

                        <label>
                            Password
                        </label>

                        <input
                            type="password"
                            value={password}
                            onChange={(e) =>
                                setPassword(
                                    e.target.value
                                )
                            }
                            placeholder="Enter your password"
                            required
                        />

                    </div>


                    <button
                        type="submit"
                        disabled={loading}
                    >

                        {loading
                            ? "Logging in..."
                            : "Login"
                        }

                    </button>

                </form>


                <p className="register-link">

                    Don't have an account?

                    <Link to="/register">
                        Register
                    </Link>

                </p>

            </div>

        </div>
    );
}


export default Login;