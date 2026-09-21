import { useState } from "react";
import {
    Link,
    useNavigate
} from "react-router-dom";

import { registerUser } from "../services/authService";


function Register() {

    const navigate = useNavigate();

    const [form, setForm] = useState({
        first_name: "",
        last_name: "",
        email: "",
        password: "",
        password_confirm: ""
    });

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);


    const handleChange = (e) => {

        setForm({
            ...form,
            [e.target.name]: e.target.value
        });

    };


    const handleSubmit = async (e) => {

        e.preventDefault();

        setError("");
        setLoading(true);

        try {

            await registerUser(form);

            navigate("/login");

        } catch (error) {

            const data =
                error.response?.data;

            setError(
                data
                    ? JSON.stringify(data)
                    : "Registration failed."
            );

        } finally {

            setLoading(false);

        }
    };


    return (

        <div className="auth-page">

            <div className="auth-card">

                <h1>Mockii</h1>

                <h2>Create Your Account</h2>


                {error && (
                    <div className="error-message">
                        {error}
                    </div>
                )}


                <form
                    onSubmit={handleSubmit}
                >

                    <input
                        name="first_name"
                        placeholder="First Name"
                        value={form.first_name}
                        onChange={handleChange}
                        required
                    />


                    <input
                        name="last_name"
                        placeholder="Last Name"
                        value={form.last_name}
                        onChange={handleChange}
                        required
                    />


                    <input
                        type="email"
                        name="email"
                        placeholder="Email Address"
                        value={form.email}
                        onChange={handleChange}
                        required
                    />


                    <input
                        type="password"
                        name="password"
                        placeholder="Password"
                        value={form.password}
                        onChange={handleChange}
                        required
                    />


                    <input
                        type="password"
                        name="password_confirm"
                        placeholder="Confirm Password"
                        value={form.password_confirm}
                        onChange={handleChange}
                        required
                    />


                    <button
                        type="submit"
                        disabled={loading}
                    >

                        {loading
                            ? "Creating Account..."
                            : "Register"
                        }

                    </button>

                </form>


                <p>

                    Already have an account?

                    <Link to="/login">
                        Login
                    </Link>

                </p>

            </div>

        </div>
    );
}


export default Register;