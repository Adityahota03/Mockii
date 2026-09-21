function Unauthorized() {

    return (

        <div className="unauthorized-page">

            <h1>
                403
            </h1>

            <h2>
                Access Denied
            </h2>

            <p>
                You don't have permission to
                access this page.
            </p>

            <a href="/login">
                Return to Login
            </a>

        </div>
    );
}


export default Unauthorized;