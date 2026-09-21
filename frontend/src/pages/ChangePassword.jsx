import {
    useState
} from "react";

import api from "../services/api";


function ChangePassword() {

    const [form, setForm] =
        useState({
            old_password: "",
            new_password: "",
            confirm_password: ""
        });

    const [message, setMessage] =
        useState("");

    const [error, setError] =
        useState("");


    const handleChange = (e) => {

        setForm({
            ...form,
            [e.target.name]:
                e.target.value
        });

    };


    const handleSubmit = async (e) => {

        e.preventDefault();

        setMessage("");
        setError("");


        try {

            const response =
                await api.post(
                    "auth/change-password/",
                    form
                );

            setMessage(
                response.data.message
            );


            setForm({
                old_password: "",
                new_password: "",
                confirm_password: ""
            });


        } catch (error) {

            const data =
                error.response?.data;


            if (
                data?.old_password
            ) {

                setError(
                    data.old_password[0]
                );

            } else if (
                data?.confirm_password
            ) {

                setError(
                    data.confirm_password[0]
                );

            } else {

                setError(
                    "Unable to change password."
                );

            }

        }
    };


    return (

        <div className="dashboard-page">

            <div className="dashboard-header">

                <h1>
                    Change Password
                </h1>

                <p>
                    Update your account password.
                </p>

            </div>


            <div className="profile-card">

                <form
                    onSubmit={handleSubmit}
                >

                    <div className="profile-field">

                        <label>
                            Current Password
                        </label>

                        <input
                            type="password"
                            name="old_password"
                            value={
                                form.old_password
                            }
                            onChange={
                                handleChange
                            }
                            required
                        />

                    </div>


                    <div className="profile-field">

                        <label>
                            New Password
                        </label>

                        <input
                            type="password"
                            name="new_password"
                            value={
                                form.new_password
                            }
                            onChange={
                                handleChange
                            }
                            required
                        />

                    </div>


                    <div className="profile-field">

                        <label>
                            Confirm New Password
                        </label>

                        <input
                            type="password"
                            name="confirm_password"
                            value={
                                form.confirm_password
                            }
                            onChange={
                                handleChange
                            }
                            required
                        />

                    </div>


                    {message && (
                        <p className="success-message">
                            {message}
                        </p>
                    )}


                    {error && (
                        <p className="error-message">
                            {error}
                        </p>
                    )}


                    <button type="submit">
                        Change Password
                    </button>

                </form>

            </div>

        </div>
    );
}


export default ChangePassword;