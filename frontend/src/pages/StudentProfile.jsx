import {
    useEffect,
    useState
} from "react";

import api from "../services/api";


function StudentProfile() {

    const [profile, setProfile] =
        useState(null);

    const [form, setForm] =
        useState({
            first_name: "",
            last_name: ""
        });

    const [message, setMessage] =
        useState("");

    const [error, setError] =
        useState("");


    useEffect(() => {

        loadProfile();

    }, []);


    const loadProfile = async () => {

        try {

            const response =
                await api.get(
                    "auth/profile/"
                );

            setProfile(
                response.data
            );

            setForm({
                first_name:
                    response.data.first_name || "",

                last_name:
                    response.data.last_name || ""
            });

        } catch (error) {

            setError(
                "Unable to load profile."
            );

        }
    };


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
                await api.patch(
                    "auth/profile/",
                    form
                );

            setProfile(
                response.data
            );

            setMessage(
                "Profile updated successfully."
            );

        } catch (error) {

            setError(
                "Unable to update profile."
            );

        }
    };


    if (!profile) {

        return (
            <div className="dashboard-page">
                Loading profile...
            </div>
        );

    }


    return (

        <div className="dashboard-page">

            <div className="dashboard-header">

                <h1>
                    My Profile
                </h1>

                <p>
                    Manage your Mockii account.
                </p>

            </div>


            <div className="profile-card">

                <form
                    onSubmit={handleSubmit}
                >

                    <div className="profile-field">

                        <label>
                            Email
                        </label>

                        <input
                            type="email"
                            value={profile.email}
                            disabled
                        />

                    </div>


                    <div className="profile-field">

                        <label>
                            First Name
                        </label>

                        <input
                            type="text"
                            name="first_name"
                            value={
                                form.first_name
                            }
                            onChange={
                                handleChange
                            }
                        />

                    </div>


                    <div className="profile-field">

                        <label>
                            Last Name
                        </label>

                        <input
                            type="text"
                            name="last_name"
                            value={
                                form.last_name
                            }
                            onChange={
                                handleChange
                            }
                        />

                    </div>


                    <div className="profile-field">

                        <label>
                            Role
                        </label>

                        <input
                            value={
                                profile.role
                            }
                            disabled
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


                    <button
                        type="submit"
                    >
                        Save Changes
                    </button>

                </form>

            </div>

        </div>
    );
}


export default StudentProfile;